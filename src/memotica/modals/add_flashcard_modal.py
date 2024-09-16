from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Select, Static, Switch, TextArea
from memotica.models import Flashcard, Deck


class AddFlashcardModal(ModalScreen):
    """
    A modal screen to add cards.
    """

    def __init__(self, decks: list[Deck] | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decks = decks

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--add-card"):
            yield Container(
                Container(
                    Static("Reversible", classes="label"),
                    Switch(value=False, animate=False),
                    classes="modal__reversible",
                ),
                Select(
                    allow_blank=False,
                    options=((deck.name, deck.id) for deck in self.decks),
                    prompt="Deck",
                ),
                classes="modal__options",
            )
            yield Container(
                Container(
                    Static("Front"),
                    TextArea.code_editor(
                        language="markdown",
                        show_line_numbers=False,
                        tab_behavior="focus",
                    ).focus(),
                    classes="modal__front",
                ),
                Container(
                    Static("Back"),
                    TextArea.code_editor(
                        language="markdown",
                        show_line_numbers=False,
                        tab_behavior="focus",
                    ),
                    classes="modal__back",
                ),
                classes="modal__review",
            )

            yield Container(
                Button(
                    label="Submit",
                    variant="success",
                    classes="submit submit--success",
                ),
                classes="modal__buttons",
            )

    def action_quit(self) -> None:
        self.dismiss(None)

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        modal.border_title = "Add a new card"
        modal.border_subtitle = "^q/esc to Close"

        textareas = self.query(TextArea)
        for textarea in textareas:
            textarea.theme = "monokai" if self.app.dark else "github_light"

    def on_button_pressed(self) -> None:
        front_textarea = self.query(TextArea)[0]
        back_textarea = self.query(TextArea)[1]
        selected_deck = self.query_one(Select)

        if not front_textarea.text or not back_textarea.text:
            self.notify(
                "Both front and back content are required",
                severity="error",
                timeout=5,
            )
            if not front_textarea.text:
                front_textarea.focus()
            else:
                back_textarea.focus()

            return

        if selected_deck.value == Select.BLANK:
            self.notify(
                "You need to select a deck!",
                severity="error",
                timeout=5,
            )
            selected_deck.focus()
            return

        flashcard = Flashcard(
            front=front_textarea.text,
            back=back_textarea.text,
            reversible=self.query_one(Switch).value,
            deck_id=selected_deck.value,
        )

        self.dismiss(flashcard)
