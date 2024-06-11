from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Static


class MessageModal(ModalScreen):
    """
    A modal screen to display messages and notifications.
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
    ]

    def __init__(self, message: str, is_error: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.is_error = is_error

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal modal--message"):
            yield Container(
                Static(f"{self.message}", classes="message"),
                classes="message-container",
            )

            yield Button(
                label="Understood",
                variant="error",
                classes="submit submit--error",
            )

    def action_quit(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self) -> None:
        self.app.pop_screen()
