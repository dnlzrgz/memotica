from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.validation import Function
from textual.containers import VerticalScroll
from textual.widgets import Input, Select
from memotica.models import Deck


class DeckModal(ModalScreen):
    """
    A modal screen to edit an existing deck or add a new one.
    """

    # Bindings to close the modal
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(
        self,
        deck: Deck | None = None,
        decks: list[Deck] = [],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.deck = deck
        self.decks = decks
        self.available_decks = (
            decks
            if self.deck is None
            else [deck for deck in self.decks if deck.id != self.deck.id]
        )
        self.decks_names = []

        if self.available_decks:
            self.decks_names = [deck.name for deck in self.available_decks]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--deck"):
            yield Select(
                allow_blank=True,
                options=((deck.name, deck.id) for deck in self.available_decks),
                value=(
                    self.deck.parent_id
                    if self.deck and self.deck.parent_id
                    else Select.BLANK
                ),
                prompt="Parent deck",
            )

            yield Input(
                placeholder="Deck name",
                max_length=50,
                value=self.deck.name if self.deck else "",
                validators=[
                    Function(
                        self.validate_deck_already_exists,
                        "A deck with that name already exists.",
                    ),
                    Function(
                        self.validate_value_is_not_empty,
                        "A deck needs to have a valid name.",
                    ),
                ],
                validate_on=["submitted"],
                classes="input-field",
            ).focus()

    def action_quit(self) -> None:
        """
        Quits the modal.
        """

        self.dismiss()

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        if self.deck:
            modal.border_title = f"Edit '{self.deck.name}'"
        else:
            modal.border_title = "Add a new deck"

        modal.border_subtitle = "^q/esc to Close/Cancel"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Handles the "form" submission.
        """

        if not event.validation_result.is_valid:
            for description in event.validation_result.failure_descriptions:
                self.notify(
                    description,
                    severity="error",
                    timeout=5,
                )
            return

        selected_parent = self.query_one(Select)
        parent = None
        if selected_parent.value != Select.BLANK:
            parent = selected_parent.value

        deck = Deck(
            name=event.value,
            parent_id=parent,
        )

        self.dismiss(deck)

    def validate_deck_already_exists(self, value) -> bool:
        if self.deck and value == self.deck.name:
            return True

        return True if value not in self.decks_names else False

    def validate_value_is_not_empty(self, value) -> bool:
        return bool(value.strip())
