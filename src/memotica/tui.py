from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Header
from memotica.config import Config
from memotica.db import init_db
from memotica.messages import (
    AddDeck,
    AddFlashcard,
    DeleteDeck,
    DeleteFlashcard,
    EditDeck,
    EditFlashcard,
    SelectDeck,
    UpdateReview,
)
from memotica.modals import HelpModal
from memotica.deck_tree import DeckTree
from memotica.flashcards_table import FlashcardsTable
from memotica.modals.flashcard_modal import FlashcardModal
from memotica.models import Deck, Flashcard, Review
from memotica.repositories import FlashcardRepository, DeckRepository, ReviewRepository
from memotica.modals import DeckModal, ConfirmationModal
from memotica.review_screen import ReviewScreen


class Memotica(App):
    """
    An Anki-like application for the terminal.
    """

    TITLE = "Memotica"
    CSS_PATH = "global.tcss"

    BINDINGS = [
        Binding("f1", "show_help", "Help", show=True),
        Binding("f5", "refresh", "Refresh data", show=False),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", show=False),
        Binding("ctrl+b", "toggle_sidebar", "Toggle Sidebar", show=False),
        Binding("ctrl+s", "start_review", "Start Review", show=True),
        Binding("ctrl+n", "add_deck", "Add Deck", show=True),
        Binding("ctrl+a", "add_flashcard", "Add Flashcard", show=True),
        Binding("ctrl+r", "reset_reviews", "Reset Deck's Flashcards", show=False),
    ]

    show_sidebar: reactive[bool] = reactive(True)
    selected_deck: reactive[Deck | None] = reactive(None)
    decks: reactive[list[Deck] | None] = reactive(None)

    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
        self.flashcards_repository = FlashcardRepository(session)
        self.decks_repository = DeckRepository(session)
        self.reviews_repository = ReviewRepository(session)

    def compose(self) -> ComposeResult:
        yield Header()
        yield DeckTree()
        yield FlashcardsTable()
        yield Footer()

    def on_mount(self) -> None:
        self.flashcards_table = self.query_one(FlashcardsTable)
        self.deck_tree = self.query_one(DeckTree)

        self.__reload()

    def on_quit(self) -> None:
        self.session.flush()
        self.app.exit()

    def on_add_deck(self, _: AddDeck) -> None:
        def callback(result: Deck) -> None:
            self.decks_repository.add(result)
            self.__reload()

        self.push_screen(DeckModal(decks=self.decks), callback)

    def on_select_deck(self, message: SelectDeck) -> None:
        if message.deck_name:
            deck = self.decks_repository.get_by_name(message.deck_name)
            self.selected_deck = deck
            self.__reload_flashcards()
            self.flashcards_table.focus()

    def on_edit_deck(self, _: EditDeck) -> None:
        if not self.selected_deck:
            return

        def callback(result: Deck) -> None:
            assert self.selected_deck

            self.decks_repository.update(
                self.selected_deck.id,
                name=result.name,
                parent_id=result.parent_id,
            )

            self.notify(
                "Deck updated!",
                severity="information",
                timeout=5,
            )

            self.__reload()

        assert self.decks

        self.push_screen(
            DeckModal(self.selected_deck, self.decks),
            callback,
        )

    def on_delete_deck(self, _: DeleteDeck) -> None:
        if not self.selected_deck:
            return

        def callback(_: bool) -> None:
            assert self.selected_deck

            self.decks_repository.delete(self.selected_deck.id)
            self.__reload()

        self.app.push_screen(
            ConfirmationModal(
                f"Are you sure that you want to delete '{self.selected_deck.name}'? All the flashcards will be deleted to!"
            ),
            callback,
        )

    def on_add_flashcard(self, _: AddFlashcard) -> None:
        if not self.decks:
            self.notify(
                "You need to add a Deck first! Check the help if you need to.",
                severity="error",
                timeout=5,
            )
            return

        def callback(result: Flashcard) -> None:
            flashcard = self.flashcards_repository.add(result)
            self.reviews_repository.add(Review(flashcard=flashcard))

            if result.reversible:
                self.reviews_repository.add(
                    Review(flashcard_id=flashcard.id, reversed=True)
                )

            self.__reload_flashcards()

        self.push_screen(
            FlashcardModal(decks=self.decks, current_deck=self.selected_deck), callback
        )

    def on_edit_flashcard(self, message: EditFlashcard) -> None:
        flashcard = self.flashcards_repository.get(message.flashcard_id)
        if not flashcard:
            return

        def callback(result: Flashcard) -> None:
            self.flashcards_repository.update(
                flashcard.id,
                reversible=result.reversible,
                front=result.front,
                back=result.back,
                deck_id=result.deck_id,
                last_updated_at=datetime.now(),
            )

            self.reviews_repository.delete_by_flashcard(flashcard.id)

            self.reviews_repository.add(Review(flashcard=flashcard))
            if result.reversible:
                self.reviews_repository.add(Review(flashcard=flashcard, reversed=True))

            self.notify(
                "Flashcard updated",
                severity="information",
                timeout=5,
            )

            self.__reload_flashcards()

        assert self.decks

        self.app.push_screen(
            FlashcardModal(self.decks, self.selected_deck, flashcard), callback
        )

    def on_delete_flashcard(self, message: DeleteFlashcard) -> None:
        def callback(_: bool) -> None:
            self.flashcards_repository.delete(message.flashcard_id)
            self.__reload_flashcards()

        self.app.push_screen(
            ConfirmationModal("Are you sure that you want to delete this flashcard?"),
            callback,
        )

    def on_update_review(self, message: UpdateReview) -> None:
        review_id = message.review_id
        self.reviews_repository.update(
            review_id,
            repetitions=message.repetitions,
            ef=message.ef,
            interval=message.interval,
            next_review=message.next_review,
            last_updated_at=message.last_updated_at,
        )

    def action_show_help(self) -> None:
        self.push_screen(HelpModal())

    def action_refresh(self) -> None:
        self.__reload()

    def action_toggle_sidebar(self) -> None:
        self.show_sidebar = not self.show_sidebar
        self.deck_tree.can_focus = self.show_sidebar

        if self.show_sidebar:
            self.deck_tree.remove_class("hide")
        else:
            self.deck_tree.add_class("hide")

    def action_add_deck(self) -> None:
        self.deck_tree.add_deck()

    def action_add_flashcard(self) -> None:
        self.flashcards_table.add_flashcard()

    def action_start_review(self) -> None:
        if not self.selected_deck:
            self.notify(
                "You need to select a Deck first!",
                severity="error",
                timeout=5,
            )
            return

        deck_and_subdecks = self.decks_repository.get_with_subdecks(
            self.selected_deck.id
        )
        reviews = [
            review
            for deck in deck_and_subdecks
            for review in self.reviews_repository.get_pending(deck.id)
        ]

        if not reviews:
            self.notify(
                "Great job! You've reviewed all your flashcards for now.",
                severity="information",
                timeout=5,
            )
            return

        self.push_screen(ReviewScreen(reviews=reviews, name="review"))

    def action_reset_reviews(self) -> None:
        if not self.selected_deck:
            self.notify(
                "You need to select a Deck first!",
                severity="error",
                timeout=5,
            )
            return

        def callback(_: bool) -> None:
            assert self.selected_deck

            deck_and_subdecks = self.decks_repository.get_with_subdecks(
                self.selected_deck.id
            )
            ids = [deck.id for deck in deck_and_subdecks]
            flashcards = self.flashcards_repository.get_by_decks(ids)

            for flashcard in flashcards:
                self.reviews_repository.delete_by_flashcard(flashcard.id)
                self.reviews_repository.add(Review(flashcard=flashcard))
                if flashcard.reversible:
                    self.reviews_repository.add(
                        Review(flashcard_id=flashcard.id, reversed=True)
                    )

            self.__reload()

        self.app.push_screen(
            ConfirmationModal(
                f"Are you sure you want to reset your review information for '{self.selected_deck.name}' and its sub-decks (if any)?"
            ),
            callback,
        )

    def __reload_decks(self) -> None:
        self.decks = self.decks_repository.get_all()
        self.deck_tree.reload(self.decks)

    def __reload_flashcards(self) -> None:
        if self.selected_deck:
            deck_and_subdecks = self.decks_repository.get_with_subdecks(
                self.selected_deck.id
            )
            ids = [deck.id for deck in deck_and_subdecks]
            flashcards = self.flashcards_repository.get_by_decks(ids)
            self.flashcards_table.reload(flashcards)
        else:
            flashcards = self.flashcards_repository.get_all()
            self.flashcards_table.reload(flashcards)

    def __reload(self) -> None:
        self.__reload_decks()
        self.__reload_flashcards()


if __name__ == "__main__":
    config = Config()
    engine = create_engine(f"{config.sqlite_url}")
    init_db(engine)

    with Session(engine) as session:
        app = Memotica(session)
        app.run()
