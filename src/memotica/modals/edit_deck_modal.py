from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.validation import Function
from textual.containers import VerticalScroll
from textual.widgets import Input, Select
from memotica.models import Deck


class EditDeckModal(ModalScreen):
    """
    A modal screen to edit decks.
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, deck: Deck, decks: list[Deck] | None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deck = deck
        self.decks = decks
        self.decks_names = []

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--edit-deck"):
            yield Select(
                allow_blank=True,
                options=(
                    (deck.name, deck.id)
                    for deck in self.decks
                    if deck.id != self.deck.id
                ),
                value=self.deck.parent_id if self.deck.parent_id else Select.BLANK,
                prompt="Parent deck",
            )

            yield Input(
                placeholder="Deck name",
                max_length=50,
                value=self.deck.name,
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
                classes="input-field",
            ).focus()

    def action_quit(self) -> None:
        self.app.pop_screen()

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        modal.border_title = "Edit deck"
        modal.border_subtitle = "^q/esc to Close/Cancel"

    @on(Input.Submitted)
    def update_deck(self, event: Input.Submitted) -> None:
        if not event.validation_result.is_valid:
            for description in event.validation_result.failure_descriptions:
                self.notify(
                    description,
                    severity="error",
                    timeout=5,
                )
            return

        selected_parent = self.query_one(Select)
        if selected_parent.value == Select.BLANK:
            parent_id = None
        else:
            parent_id = selected_parent.value

        deck = Deck(
            name=event.value,
            parent_id=parent_id,
        )

        self.dismiss(deck)

    def validate_deck_already_exists(self, value) -> bool:
        if not self.decks_names:
            self.decks_names = [
                deck.name for deck in self.decks if deck.name != self.deck.name
            ]

        return True if value not in self.decks_names else False

    def validate_value_is_not_empty(self, value) -> bool:
        return True if value.strip() else False
