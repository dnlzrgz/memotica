from textwrap import shorten
from rich.text import Text
from textual.binding import Binding
from textual.widgets import DataTable
from memotica.messages import AddFlashcard, DeleteFlashcard, EditFlashcard
from memotica.models import Flashcard


class FlashcardsTable(DataTable):
    def __init__(self, *args, **kwargs):
        super().__init__(cursor_type="row", zebra_stripes=True, *args, **kwargs)

    BINDINGS = [
        Binding("backspace", "delete", "Delete", priority=True),
        Binding("ctrl+e", "edit", "Edit", priority=True),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
    ]

    def on_mount(self) -> None:
        self.add_columns("Front", "Back", "Reversible", "Deck")
        self.border_title = "Flashcards"

    def add_flashcard(self):
        self.post_message(AddFlashcard())

    def action_edit(self) -> None:
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        flashcard_id = int(row_key.value)
        self.post_message(EditFlashcard(flashcard_id))

    def action_delete(self) -> None:
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        flashcard_id = int(row_key.value)
        self.post_message(DeleteFlashcard(flashcard_id))

    def reload(self, flashcards: list[Flashcard] | None = None) -> None:
        self.loading = True
        self.clear()

        if not flashcards:
            self.loading = False
            return

        for flashcard in flashcards:
            self.add_row(
                shorten(flashcard.front, width=40, placeholder="..."),
                shorten(flashcard.back, width=40, placeholder="..."),
                Text(
                    str("✔" if flashcard.reversible else "✗"),
                    style="bold",
                    justify="center",
                ),
                flashcard.deck.name,
                key=f"{flashcard.id}",
            )

        self.loading = False
