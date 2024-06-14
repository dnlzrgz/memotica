from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Select, Static, Switch, TextArea
from memotica.models import Flashcard, Deck


class EditFlashcardModal(ModalScreen):
    """
    A modal screen to edit cards.
    """

    def __init__(self, flashcard: Flashcard, decks: list[Deck] | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.flashcard = flashcard
        self.decks = decks

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--edit-card"):
            yield Container(
                Container(
                    Static("Reversible", classes="label"),
                    Switch(value=self.flashcard.reversible, animate=False),
                    classes="modal__reversible",
                ),
                Select(
                    allow_blank=True,
                    options=((deck.name, deck.id) for deck in self.decks),
                    prompt="Deck",
                    value=self.flashcard.deck_id,
                ),
                classes="modal__options",
            )

            yield Container(
                Static("Front"),
                TextArea.code_editor(
                    language="markdown",
                    show_line_numbers=False,
                    text=self.flashcard.front,
                    tab_behavior="focus",
                ),
                classes="modal__front",
            )

            yield Container(
                Static("Back"),
                TextArea.code_editor(
                    language="markdown",
                    show_line_numbers=False,
                    text=self.flashcard.back,
                    tab_behavior="focus",
                ),
                classes="modal__back",
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
        self.app.pop_screen()

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        modal.border_title = "Edit card"
        modal.border_subtitle = "^q/esc to Close"

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
