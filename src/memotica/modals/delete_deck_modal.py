from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static


class DeleteDeckModal(ModalScreen):
    """
    A modal screen to delete decks.
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, deck_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.deck_name = deck_name

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--delete-deck"):
            yield Static(f"Are you sure that you want to delete '{self.deck_name}'?")

            yield Container(
                Button(label="Cancel", variant="success"),
                Button(label="Delete", variant="error"),
                classes="modal__options modal__options--delete",
            )

    def action_quit(self) -> None:
        self.dismiss(False)

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        modal.border_title = f"Delete modal '{self.deck_name}'"
        modal.border_subtitle = "^q/esc to cancel"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if f"{event.button.label}" == "Delete":
            self.dismiss(True)
        else:
            self.dismiss(False)
