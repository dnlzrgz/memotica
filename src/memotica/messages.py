from textual.message import Message


class AddDeck(Message):
    pass


class SelectDeck(Message):
    def __init__(self, deck_name: str | None = None) -> None:
        super().__init__()
        self.deck_name = deck_name


class EditDeck(Message):
    pass


class DeleteDeck(Message):
    pass


class AddFlashcard(Message):
    pass


class EditFlashcard(Message):
    def __init__(self, flashcard_id: int) -> None:
        super().__init__()
        self.flashcard_id = flashcard_id


class DeleteFlashcard(Message):
    def __init__(self, flashcard_id: int) -> None:
        super().__init__()
        self.flashcard_id = flashcard_id
