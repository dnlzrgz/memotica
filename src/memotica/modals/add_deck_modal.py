from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.validation import Function
from textual.containers import Container, VerticalScroll
from textual.widgets import Input
from memotica.models import Deck


class AddDeckModal(ModalScreen):
    """
    A modal screen to add/edit decks.
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, decks: list[Deck] | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deck_names = [deck.name for deck in decks] if decks else []

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--add-deck"):
            yield Container(
                Input(
                    placeholder="Deck name",
                    max_length=50,
                    validators=[
                        Function(
                            self.validate_deck_already_exists,
                            "A deck with that name already exists.",
                        ),
                        Function(
                            self.validate_value_is_not_empty,
                            "Deck needs to have a valid name.",
                        ),
                    ],
                    validate_on=["submitted"],
                ).focus(),
                classes="input-field",
            )

    def action_quit(self) -> None:
        self.app.pop_screen()

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        modal.border_title = "Add a new deck"
        modal.border_subtitle = "^q/esc to Close"

    @on(Input.Submitted)
    def save_deck(self, event: Input.Submitted) -> None:
        if not event.validation_result.is_valid:
            for description in event.validation_result.failure_descriptions:
                self.notify(
                    description,
                    severity="error",
                    timeout=5,
                )
            return

        deck = Deck(name=event.value)
        self.dismiss(deck)

    def validate_deck_already_exists(self, value) -> bool:
        return True if value not in self.deck_names else False

    def validate_value_is_not_empty(self, value) -> bool:
        return True if value.strip() else False
