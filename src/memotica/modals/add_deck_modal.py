from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Input, Static
from memotica.models import Deck


class DeckModal(ModalScreen):
    """
    A modal screen to add/edit decks.
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--deck"):
            yield Container(
                Static("Name", classes="label label--name"),
                Input(placeholder="Deck name", classes="input modal__input"),
            )

            yield Button(
                label="Submit",
                variant="success",
                classes="submit submit--success",
            )

    def action_quit(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self) -> None:
        deck = Deck(
            name=self.query_one(Input).value,
        )
        self.dismiss(deck)
