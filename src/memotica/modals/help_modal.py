from pathlib import Path
from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import VerticalScroll
from textual.widgets import Static, Markdown


class HelpModal(ModalScreen):
    header_text = """memotica help:""".split()

    def compose(self) -> ComposeResult:
        markdown_path = Path(__file__).parent / "help_modal.md"
        with open(markdown_path, "r") as f:
            markdown = f.read()

        with VerticalScroll(classes="modal modal--help"):
            yield Static(" ".join(self.header_text))
            with VerticalScroll(id="content"):
                yield Markdown(markdown=markdown)

    def on_mount(self) -> None:
        self.body = self.query("#content")

        modal = self.query_one(".modal")
        modal.border_title = "Help"

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
