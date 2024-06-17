from collections import deque
from datetime import datetime, timedelta
from sqlalchemy import update
from sqlalchemy.orm import Session
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Markdown, Button
from memotica.models import Review
from memotica.sm2 import sm2


class ReviewScreen(Screen):
    BINDINGS = [
        Binding(
            "ctrl+q", "app.pop_screen", "Exit Review Session", show=True, priority=True
        ),
        Binding("escape", "app.pop_screen", "Stop Review", show=False, priority=True),
        Binding("ctrl+s", "app.pop_screen", "Stop Review", show=False, priority=True),
        Binding("ctrl+a", "disable_binding", "Nothing", show=False, priority=True),
        Binding("ctrl+n", "disable_binding", "Nothing", show=False, priority=True),
    ]

    reviews: reactive[deque[Review]] = reactive(deque())
    current_review: reactive[Review | None] = reactive(None)
    front: reactive[str] = reactive("", recompose=True)
    back: reactive[str] = reactive("", recompose=True)

    def __init__(self, session: Session, reviews: list[Review], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

        self.reviews = deque(reviews)
        self.current_review = self.reviews.popleft()

        if self.current_review.direction == "ftb":
            self.front = self.current_review.flashcard.front
            self.back = self.current_review.flashcard.back
        else:
            self.front = self.current_review.flashcard.back
            self.back = self.current_review.flashcard.front

    def compose(self) -> ComposeResult:
        yield Container(
            Markdown(
                self.front,
                classes="review__screen__question",
            ),
            Container(
                Button("Show", variant="primary"),
                classes="review__screen__controls",
            ),
            classes="review__screen review__screen--question",
        )

        yield Container(
            Markdown(
                self.front,
                classes="review__screen__front",
            ),
            Markdown(
                self.back,
                classes="review__screen__back",
            ),
            Container(
                Button("Wrong", variant="error"),
                Button("Good", variant="warning"),
                Button("Easy", variant="success"),
                classes="review__screen__controls",
            ),
            classes="review__screen review__screen--answer hide",
        )

        yield Footer()

    def action_disable_binding(self) -> None:
        return None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        answer = self.query(".review__screen--answer")
        question = self.query(".review__screen--question")

        if f"{event.button.label}" == "Show":
            answer.remove_class("hide")
            question.add_class("hide")
            return

        if f"{event.button.label}" == "Good":
            self.update_reviews(q=3)
        elif f"{event.button.label}" == "Easy":
            self.update_reviews(q=5)
        else:
            self.update_reviews()

        self.next_review()
        answer.add_class("hide")
        question.remove_class("hide")

    def next_review(self) -> None:
        if not self.reviews:
            self.notify(
                "There are no more cards to review. Well done!",
                severity="information",
                timeout=5,
            )
            self.app.pop_screen()
            return

        self.current_review = self.reviews.popleft()

        if self.current_review.direction == "ftb":
            self.front = self.current_review.flashcard.front
            self.back = self.current_review.flashcard.back
        else:
            self.front = self.current_review.flashcard.back
            self.back = self.current_review.flashcard.front

    def update_reviews(self, q: int = 0) -> None:
        assert self.current_review is not None

        (n, ef, i) = sm2(
            self.current_review.repetitions,
            self.current_review.ef,
            self.current_review.interval,
            q,
        )

        next_review_time = datetime.now() + timedelta(days=i)

        stmt = (
            update(Review)
            .where(Review.id == self.current_review.id)
            .values(
                repetitions=n,
                ef=ef,
                interval=i,
                next_review=next_review_time,
                last_updated_at=datetime.now(),
            )
        )

        self.session.execute(stmt)
        self.session.commit()

        self.current_review.repetitions = n
        self.current_review.ef = ef
        self.current_review.interval = i
        self.current_review.next_review = next_review_time

        if q == 0:
            self.reviews.append(self.current_review)
