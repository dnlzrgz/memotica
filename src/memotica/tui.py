from textwrap import shorten
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Footer, Header
from memotica.config import Config
from memotica.db import init_db
from memotica.modals import (
    AddDeckModal,
    EditDeckModal,
    DeleteDeckModal,
    AddFlashcardModal,
    DeleteFlashcardModal,
    EditFlashcardModal,
    HelpModal,
)
from memotica.deck_tree import DeckTree
from memotica.flashcards_table import FlashcardsTable
from memotica.models import Flashcard, Deck, Review
from memotica.repositories import FlashcardRepository, DeckRepository, ReviewRepository
from memotica.review_screen import ReviewScreen


class MemoticaApp(App):
    """
    An Anki-like application for the terminal.
    """

    TITLE = "Memotica"
    CSS_PATH = "global.tcss"

    BINDINGS = [
        Binding("f1", "show_help_screen", "Help", show=True),
        Binding("f5", "refresh", "Refresh data", show=False),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", show=False),
        Binding("ctrl+b", "toggle_deck_tree", "Toggle Sidebar", show=False),
        Binding("ctrl+s", "start_review", "Start Review", show=True),
        Binding("ctrl+n", "add_deck", "Add Deck", show=True),
        Binding("ctrl+a", "add_flashcard", "Add Flashcard", show=True),
    ]

    show_sidebar: reactive[bool] = reactive(True)
    deck_id: reactive[int | None] = reactive(None)

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
        self.__reload_decks()
        self.__reload_cards()

    def on_quit(self) -> None:
        self.session.flush()
        self.app.exit()

    def on_deck_tree_delete_message(self, _: DeckTree.DeleteMessage) -> None:
        deck = self.decks_repository.get(self.deck_id)

        def callback(result: bool) -> None:
            if result:
                self.decks_repository.delete(deck.id)
                self.__reload_decks()
                self.__reload_cards()

        self.push_screen(DeleteDeckModal(deck.name), callback)

    def on_deck_tree_edit_message(self, message: DeckTree.EditMessage) -> None:
        def callback(result: str) -> None:
            if result:
                self.decks_repository.update(self.deck_id, name=message.deck_name)

                self.notify(
                    "Deck updated!",
                    severity="information",
                    timeout=5,
                )

                self.__reload_decks()
                self.__reload_cards()

        self.push_screen(EditDeckModal(message.deck_name, self.decks), callback)

    def on_deck_tree_deck_selected_message(
        self,
        message: DeckTree.DeckSelectedMessage,
    ) -> None:
        deck = self.decks_repository.get_by_name(message.deck_name)
        if deck:
            self.deck_id = deck.id
            self.__reload_cards()

    def on_flashcards_table_delete_message(
        self,
        message: FlashcardsTable.DeleteMessage,
    ) -> None:
        flashcard = self.flashcards_repository.get(int(message.row_key))

        def callback(result: bool) -> None:
            if result:
                self.flashcards_repository.delete(flashcard.id)
                self.__reload_cards()

        self.push_screen(DeleteFlashcardModal(), callback)

    def on_flashcards_table_edit_message(
        self,
        message: FlashcardsTable.EditMessage,
    ) -> None:
        flashcard_id = int(message.row_key)

        def callback(result: Flashcard) -> None:
            if result:
                self.flashcards_repository.update(
                    flashcard_id,
                    reversible=result.reversible,
                    front=result.front,
                    back=result.back,
                    deck_id=result.deck_id,
                    last_updated_at=datetime.now(),
                )

                reviews = self.reviews_repository.get_by_flashcard(flashcard_id)
                for review in reviews:
                    self.reviews_repository.delete(review.id)

                self.reviews_repository.add(Review(flashcard_id=flashcard_id))

                if result.reversible:
                    self.reviews_repository.add(
                        Review(flashcard_id=flashcard_id, direction="btf")
                    )

                self.notify(
                    "Flashcard updated",
                    severity="information",
                    timeout=5,
                )

                self.__reload_cards()

        flashcard = self.flashcards_repository.get(flashcard_id)
        assert flashcard is not None
        self.push_screen(EditFlashcardModal(flashcard, self.decks), callback)

    def action_show_help_screen(self) -> None:
        self.push_screen(HelpModal())

    def action_refresh(self) -> None:
        self.__reload_decks()
        self.__reload_cards()

    def action_toggle_deck_tree(self) -> None:
        self.show_sidebar = not self.show_sidebar
        deck_tree = self.query_one(DeckTree)
        deck_tree.can_focus = self.show_sidebar

        if self.show_sidebar:
            deck_tree.remove_class("hide")
        else:
            deck_tree.add_class("hide")

    def action_add_deck(self) -> None:
        def callback(result: Deck) -> None:
            self.decks_repository.add(result)
            self.__reload_decks()

        self.push_screen(AddDeckModal(self.decks), callback)

    def action_add_flashcard(self) -> None:
        if len(self.decks) <= 0:
            self.notify(
                "You need to add a Deck first! Check the help if you need to.",
                severity="error",
                timeout=5,
            )
            return

        def callback(result: Flashcard) -> None:
            self.flashcards_repository.add(result)
            self.reviews_repository.add(Review(flashcard_id=result.id))

            if result.reversible:
                self.reviews_repository.add(
                    Review(flashcard_id=result.id, direction="btf")
                )

            self.__reload_cards()

        self.push_screen(AddFlashcardModal(self.decks), callback)

    def action_start_review(self) -> None:
        if not self.deck_id:
            self.notify(
                "You need to select a Deck first!",
                severity="error",
                timeout=5,
            )
            return

        reviews = self.reviews_repository.get_pending(self.deck_id)

        if not reviews:
            self.notify(
                "Great job! You've reviewed all your flashcards for now.",
                severity="information",
                timeout=5,
            )
            return

        self.push_screen(
            ReviewScreen(
                session=self.session,
                deck_id=self.deck_id,
                name="review",
            )
        )

    def __reload_decks(self) -> None:
        deck_tree = self.query_one(DeckTree)
        self.decks = self.decks_repository.get_all()
        deck_tree.reload_decks(self.decks)

    def __reload_cards(self) -> None:
        flashcards_table = self.query_one(FlashcardsTable)
        flashcards_table.loading = True
        flashcards_table.clear()

        if self.deck_id:
            self.flashcards = self.flashcards_repository.get_by_deck(self.deck_id)
        else:
            self.flashcards = self.flashcards_repository.get_all()

        for flashcard in self.flashcards:
            flashcards_table.add_row(
                shorten(flashcard.front, width=40, placeholder="..."),
                shorten(flashcard.back, width=40, placeholder="..."),
                flashcard.reversible,
                flashcard.deck.name,
                key=f"{flashcard.id}",
            )

        flashcards_table.loading = False


if __name__ == "__main__":
    config = Config()
    engine = create_engine(f"{config.sqlite_url}")
    init_db(engine)

    with Session(engine) as session:
        app = MemoticaApp(session)
        app.run()
