from textual.binding import Binding
from textual.message import Message
from textual.widgets import DataTable


class FlashcardsTable(DataTable):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(cursor_type="row", *args, **kwargs)

    BINDINGS = [
        Binding("backspace", "delete", "Delete Flashcard", priority=True),
        Binding("ctrl+e", "edit", "Edit Flashcard", priority=True),
    ]

    def on_mount(self) -> None:
        self.add_columns("Front", "Back", "Reversible", "Deck")
        self.border_title = "Flashcards"

    def action_edit(self) -> None:
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        self.post_message(self.EditMessage(row_key.value))

    def action_delete(self) -> None:
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        self.post_message(self.DeleteMessage(row_key.value))

    class DeleteMessage(Message):
        def __init__(self, row_key: str) -> None:
            self.row_key = row_key
            super().__init__()

    class EditMessage(Message):
        def __init__(self, row_key: str) -> None:
            self.row_key = row_key
            super().__init__()
