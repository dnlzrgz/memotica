from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Select, Static, Switch, TextArea
from memotica.models import Card, Deck


class CardModal(ModalScreen):
    """
    A modal screen to add/edit cards.
    """

    def __init__(self, decks: list[Deck] | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.decks = decks

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--card"):
            yield Container(
                Container(
                    Static("Reversible", classes="label label--reversible"),
                    Switch(value=False, animate=False, classes="switch"),
                    classes="modal__reversible",
                ),
                Select(
                    allow_blank=True,
                    classes="modal__decks-select",
                    options=((deck.name, deck.id) for deck in self.decks),
                    prompt="Deck",
                    value=self.decks[0].id,
                ),
                classes="modal__options",
            )

            yield Container(
                Static("Front", classes="label label--textarea"),
                TextArea.code_editor(
                    language="markdown",
                    show_line_numbers=False,
                    classes="modal__textarea modal__textarea--first",
                ),
                classes="modal__first",
            )

            yield Container(
                Static("Back", classes="label label--textarea"),
                TextArea.code_editor(
                    language="markdown",
                    show_line_numbers=False,
                    classes="modal__textarea modal__textarea--second",
                ),
                classes="modal__second",
            )

            yield Button(
                label="Submit",
                variant="success",
                classes="submit submit--success",
            )

    def action_quit(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self) -> None:
        card = Card(
            front=self.query(TextArea)[0].text,
            back=self.query(TextArea)[1].text,
            reversible=self.query_one(Switch).value,
            deck_id=self.query_one(Select).value,
        )
        self.dismiss(card)
