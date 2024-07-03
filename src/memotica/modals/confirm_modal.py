from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static


class ConfirmationModal(ModalScreen):
    """
    A modal screen that handles actions that require a confirmation.
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, message: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--confirm"):
            yield Static(self.message)

            yield Container(
                Button(label="Cancel", variant="success").focus(),
                Button(label="Delete", variant="error"),
                classes="modal__options",
            )

    def action_quit(self) -> None:
        self.dismiss()

    def on_mount(self) -> None:
        modal = self.query_one(".modal")
        modal.border_title = "Confirmation required!"
        modal.border_subtitle = "^q/esc to cancel"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if f"{event.button.label}" == "Delete":
            self.dismiss(True)
        else:
            self.dismiss()
