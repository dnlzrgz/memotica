from datetime import datetime, timedelta
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


class UpdateReview(Message):
    def __init__(
        self,
        review_id: int,
        repetitions: int,
        ef: float,
        interval: int,
    ) -> None:
        super().__init__()
        self.review_id = review_id
        self.repetitions = repetitions
        self.ef = ef
        self.interval = interval

        now = datetime.now()

        self.next_review = now.date() + timedelta(days=interval)
        self.last_updated_at = now
