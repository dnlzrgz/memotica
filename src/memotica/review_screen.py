from collections import deque
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Markdown, Button
from memotica.messages import UpdateReview
from memotica.models import Review
from memotica.sm2 import sm2


class ReviewScreen(Screen):
    BINDINGS = [
        Binding(
            "ctrl+q", "app.pop_screen", "Exit Review Session", show=True, priority=True
        ),
        Binding("escape", "app.pop_screen", "Stop Review", show=False, priority=True),
        Binding("ctrl+s", "app.pop_screen", "Stop Review", show=False, priority=True),
        Binding("f5", "disable_binding", "Nothing", show=False, priority=True),
        Binding("ctrl+a", "disable_binding", "Nothing", show=False, priority=True),
        Binding("ctrl+n", "disable_binding", "Nothing", show=False, priority=True),
    ]

    front_content: reactive[str] = reactive("", recompose=True)
    back_content: reactive[str] = reactive("", recompose=True)

    def __init__(self, reviews: list[Review], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review_queue = deque(reviews)
        self.current_review = self.review_queue.popleft()

        if self.current_review.reversed:
            self.front_content = self.current_review.flashcard.back
            self.back_content = self.current_review.flashcard.front
        else:
            self.front_content = self.current_review.flashcard.front
            self.back_content = self.current_review.flashcard.back

    def compose(self) -> ComposeResult:
        yield Container(
            Markdown(
                self.front_content,
                classes="review__screen__question",
            ),
            Container(
                Button("Show", variant="primary", id="show"),
                classes="review__screen__controls",
            ),
            classes="review__screen review__screen--question",
        )

        yield Container(
            Markdown(
                self.front_content,
                classes="review__screen__front",
            ),
            Markdown(
                self.back_content,
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

        button_label = f"{event.button.label}"

        if button_label == "Show":
            answer.remove_class("hide")
            question.add_class("hide")
        else:
            if button_label == "Easy":
                self.update_review(5)
            elif button_label == "Good":
                self.update_review(3)
            else:
                self.update_review()

            self.load_next_review()
            answer.add_class("hide")
            question.remove_class("hide")

    def load_next_review(self) -> None:
        if not self.review_queue:
            self.notify(
                "There are no more cards to review. Well done!",
                severity="information",
                timeout=5,
            )
            self.app.pop_screen()
            return

        self.current_review = self.review_queue.popleft()

        if self.current_review.reversed:
            self.front_content = self.current_review.flashcard.back
            self.back_content = self.current_review.flashcard.front
        else:
            self.front_content = self.current_review.flashcard.front
            self.back_content = self.current_review.flashcard.back

    def update_review(self, q: int = 0) -> None:
        (n, ef, i) = sm2(
            self.current_review.repetitions,
            self.current_review.ef,
            self.current_review.interval,
            q,
        )

        self.post_message(UpdateReview(self.current_review.id, n, ef, i))

        if q < 3:
            self.current_review.repetitions = n
            self.current_review.ef = ef
            self.current_review.interval = i

            self.review_queue.append(self.current_review)
