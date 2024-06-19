from textwrap import shorten
from datetime import datetime
from sqlalchemy import create_engine, update, delete
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
from memotica.review_screen import ReviewScreen


class MemoticaApp(App):
    """
    An Anki-like application for the terminal.
    """

    TITLE = "Memotica"
    CSS_PATH = "global.tcss"

    BINDINGS = [
        Binding("f1", "show_help_screen", "Help", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", show=False),
        Binding("ctrl+b", "toggle_deck_tree", "Toggle Sidebar", show=False),
        Binding("ctrl+s", "start_review", "Start Review", show=True),
        Binding("ctrl+n", "add_deck", "Add Deck", show=True),
        Binding("ctrl+a", "add_flashcard", "Add Flashcard", show=True),
    ]

    show_sidebar: reactive[bool] = reactive(True)
    current_deck: reactive[str | None] = reactive(None)

    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

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

    def on_deck_tree_delete_message(self, message: DeckTree.DeleteMessage) -> None:
        deck_in_db = (
            self.session.query(Deck)
            .filter(Deck.name == message.deck_name)
            .one_or_none()
        )

        def callback(result: bool) -> None:
            if result:
                self.session.delete(deck_in_db)
                self.session.commit()
                self.__reload_decks()
                self.__reload_cards()

        if deck_in_db is not None:
            self.push_screen(DeleteDeckModal(message.deck_name), callback)

    def on_deck_tree_edit_message(self, message: DeckTree.EditMessage) -> None:
        def callback(result: str) -> None:
            if result:
                stmt = (
                    update(Deck)
                    .where(Deck.name == message.deck_name)
                    .values(name=result)
                )

                self.session.execute(stmt)
                self.session.commit()

                self.notify(
                    f"Updated deck '{message.deck_name}' to '{result}'",
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
        self.current_deck = message.deck_name
        self.__reload_cards(message.deck_name)

    def on_flashcards_table_delete_message(
        self,
        message: FlashcardsTable.DeleteMessage,
    ) -> None:
        flashcard_in_db = self.session.get(Flashcard, message.row_key)

        def callback(result: bool) -> None:
            if result:
                self.session.delete(flashcard_in_db)
                self.session.commit()
                self.__reload_cards()

        if flashcard_in_db is not None:
            self.push_screen(DeleteFlashcardModal(), callback)

    def on_flashcards_table_edit_message(
        self,
        message: FlashcardsTable.EditMessage,
    ) -> None:
        flashcard_id = message.row_key

        def callback(result: Flashcard) -> None:
            if result:
                stmt = (
                    update(Flashcard)
                    .where(Flashcard.id == flashcard_id)
                    .values(
                        reversible=result.reversible,
                        front=result.front,
                        back=result.back,
                        deck_id=result.deck_id,
                        last_updated_at=datetime.now(),
                    )
                )
                self.session.execute(stmt)

                if not result.reversible:
                    stmt = (
                        delete(Review)
                        .where(Review.flashcard_id == flashcard_id)
                        .where(Review.direction == "btf")
                    )
                    self.session.execute(stmt)
                else:
                    self.session.add(
                        Review(
                            flashcard_id=message.row_key,
                            direction="btf",
                        )
                    )

                self.session.commit()

                self.notify(
                    "Flashcard updated",
                    severity="information",
                    timeout=5,
                )

                self.__reload_cards()

        flashcard_in_db = (
            self.session.query(Flashcard)
            .where(Flashcard.id == flashcard_id)
            .one_or_none()
        )
        if flashcard_in_db:
            self.push_screen(EditFlashcardModal(flashcard_in_db, self.decks), callback)
        else:
            self.notify(
                "Oops! This flashcard doesn't seem to be in the database.",
                severity="error",
                timeout=5,
            )

    def action_show_help_screen(self) -> None:
        self.push_screen(HelpModal())

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
            self.session.add(result)
            self.session.commit()
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
            # Add flashcards
            self.session.add(result)
            self.session.commit()
            self.session.refresh(result)

            # Create review data
            review_ftb = Review(flashcard_id=result.id, direction="ftb")
            self.session.add(review_ftb)

            if result.reversible:
                review_btf = Review(flashcard_id=result.id, direction="btf")
                self.session.add(review_btf)

            self.session.commit()
            self.__reload_cards()

        self.push_screen(AddFlashcardModal(self.decks), callback)

    def action_start_review(self) -> None:
        if self.current_deck is None:
            self.notify(
                "You need to select a Deck first!",
                severity="error",
                timeout=5,
            )
            return

        deck = self.session.query(Deck).filter_by(name=self.current_deck).one_or_none()
        if deck is None:
            self.notify(
                f"Selected deck '{self.current_deck}' not found!",
                severity="error",
                timeout=5,
            )
            return

        reviews = (
            self.session.query(Review)
            .join(Flashcard)
            .filter(Flashcard.deck_id == deck.id)
            .filter(Review.next_review <= datetime.now().date())
            .order_by(Review.next_review)
            .all()
        )

        if not reviews:
            self.notify(
                "Great job! You've reviewed all your flashcards for now.",
                severity="error",
                timeout=5,
            )
            return

        self.push_screen(
            ReviewScreen(
                session=self.session,
                reviews=reviews,
                name="review",
            )
        )

    def __reload_decks(self) -> None:
        deck_tree = self.query_one(DeckTree)
        self.decks = self.session.query(Deck).all()
        deck_tree.reload_decks(self.decks)

    def __reload_cards(self, deck: str | None = None) -> None:
        flashcards_table = self.query_one(FlashcardsTable)
        flashcards_table.loading = True
        flashcards_table.clear()

        if deck:
            self.flashcards = (
                self.session.query(Flashcard).join(Deck).filter(Deck.name == deck).all()
            )
        else:
            self.flashcards = self.session.query(Flashcard).join(Deck).all()

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
