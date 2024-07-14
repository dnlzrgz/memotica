from collections import deque
from enum import Enum, auto
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Footer, Markdown, Button
from memotica.messages import UpdateReview
from memotica.models import Review
from memotica.sm2 import sm2


class ReviewStatus(Enum):
    LOADING = auto()
    SHOW_QUESTION = auto()
    SHOW_ANSWER = auto()


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

    review_status: reactive[ReviewStatus] = reactive(ReviewStatus.LOADING)

    def __init__(self, reviews: list[Review], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.review_queue = deque(reviews)
        self.loading = True

    def compose(self) -> ComposeResult:
        yield Container(
            Markdown(
                "",
                classes="review__question",
            ),
            Markdown(
                "",
                classes="review__answer hide",
            ),
            Container(
                Button("Show", variant="primary", id="show"),
                classes="review__show",
            ),
            Container(
                Button("Wrong", variant="error", id="wrong"),
                Button("Good", variant="warning", id="good"),
                Button("Easy", variant="success", id="easy"),
                classes="review__assestment hide",
            ),
            classes="review-screen",
        )

        yield Footer()

    def on_mount(self) -> None:
        self.question = self.query(".review__question").only_one()
        self.answer = self.query(".review__answer").only_one()
        self.show_button = self.query(".review__show").only_one()
        self.assestment_buttons = self.query(".review__assestment").only_one()

        self.load_next()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "show":
            self.review_status = ReviewStatus.SHOW_ANSWER
        else:
            if button_id == "easy":
                self.update_review(5)
            elif button_id == "good":
                self.update_review(3)
            else:
                self.update_review()

            self.load_next()

    def on_key(self, event: events.Key) -> None:
        key = event.key
        if (
            key == "space" or key == "enter"
        ) and self.review_status == ReviewStatus.SHOW_QUESTION:
            self.review_status = ReviewStatus.SHOW_ANSWER

        if key in ["1", "2", "3"] and self.review_status == ReviewStatus.SHOW_ANSWER:
            if key == "1":
                self.update_review()
            elif key == "2":
                self.update_review(3)
            elif key == "3":
                self.update_review(5)

            self.load_next()

    def action_disable_binding(self) -> None:
        return None

    def update_review(self, q: int = 0) -> None:
        (n, ef, i) = sm2(
            self.current_question.repetitions,
            self.current_question.ef,
            self.current_question.interval,
            q,
        )

        self.post_message(UpdateReview(self.current_question.id, n, ef, i))

        if q < 3:
            self.current_question.repetitions = n
            self.current_question.ef = ef
            self.current_question.interval = i

            self.review_queue.append(self.current_question)

    def watch_review_status(self, _: ReviewStatus, new_status: ReviewStatus) -> None:
        if new_status == ReviewStatus.LOADING:
            self.loading = True
        else:
            self.loading = False

            if new_status == ReviewStatus.SHOW_QUESTION:
                self.show_button.remove_class("hide")
                self.answer.add_class("hide")
                self.assestment_buttons.add_class("hide")
            else:
                self.show_button.add_class("hide")
                self.answer.remove_class("hide")
                self.assestment_buttons.remove_class("hide")

    def load_next(self) -> None:
        if not self.review_queue:
            self.notify(
                "There are no more cards to review. Well done!",
                severity="information",
                timeout=5,
            )
            self.app.pop_screen()
            return

        self.review_status = ReviewStatus.LOADING

        self.current_question = self.review_queue.popleft()
        if self.current_question.reversed:
            self.question.update(self.current_question.flashcard.back)
            self.answer.update(self.current_question.flashcard.front)
        else:
            self.question.update(self.current_question.flashcard.front)
            self.answer.update(self.current_question.flashcard.back)

        self.review_status = ReviewStatus.SHOW_QUESTION
