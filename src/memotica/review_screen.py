from sqlalchemy.orm import Session
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Markdown, Button
from memotica.models import Review


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

    number_reviews: reactive[int] = reactive(0)
    current_review_idx: reactive[int] = reactive(0, recompose=True)
    current_review_front: reactive[str] = reactive("", recompose=True)
    current_review_back: reactive[str] = reactive("", recompose=True)

    def __init__(self, session: Session, reviews: list[Review], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
        self.reviews = reviews

        self.number_reviews = len(reviews)

        current_flashcard = self.reviews[0].flashcard
        if self.reviews[0].direction == "ftb":
            self.current_review_front = current_flashcard.front
            self.current_review_back = current_flashcard.back
        else:
            self.current_review_front = current_flashcard.back
            self.current_review_back = current_flashcard.front

    def compose(self) -> ComposeResult:
        yield Container(
            Markdown(
                self.current_review_front,
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
                self.current_review_front,
                classes="review__screen__front",
            ),
            Markdown(
                self.current_review_back,
                classes="review__screen__back",
            ),
            Container(
                Button("Again", variant="error"),
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
        else:
            if self.current_review_idx == self.number_reviews - 1:
                self.current_review_idx = 0
            else:
                self.current_review_idx += 1

                current_flashcard = self.reviews[self.current_review_idx].flashcard
                if self.reviews[self.current_review_idx].direction == "ftb":
                    self.current_review_front = current_flashcard.front
                    self.current_review_back = current_flashcard.back
                else:
                    self.current_review_front = current_flashcard.back
                    self.current_review_back = current_flashcard.front

            answer.add_class("hide")
            question.remove_class("hide")
