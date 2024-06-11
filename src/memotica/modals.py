from pathlib import Path
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Button, Input, Select, Static, Switch, TextArea, Markdown
from memotica.models import Card, Deck


class HelpModal(ModalScreen):
    header_text = """memotica help:""".split()

    def compose(self) -> ComposeResult:
        markdown_path = Path(__file__).parent / "help_modal.md"
        with open(markdown_path, "r") as f:
            markdown = f.read()

        with VerticalScroll(classes="modal modal--help"):
            yield Static(" ".join(self.header_text), classes="modal__header")
            with VerticalScroll(classes="help__content"):
                yield Markdown(markdown=markdown)

    def on_mount(self) -> None:
        self.body = self.query_one(".help__content")

    def on_key(self, event: events.Key) -> None:
        event.stop()

        if event.key == "up":
            self.body.scroll_up()
        elif event.key == "down":
            self.body.scroll_down()
        elif event.key == "left":
            self.body.scroll_left()
        elif event.key == "right":
            self.body.scroll_right()
        elif event.key == "pageup":
            self.body.scroll_page_up()
        elif event.key == "pagedown":
            self.body.scroll_page_down()
        else:
            self.app.pop_screen()


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
