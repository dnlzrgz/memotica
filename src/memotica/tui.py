from textwrap import shorten
from sqlalchemy import update
from sqlalchemy.orm import Session
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Tree
from memotica.db import engine, init_db
from memotica.modals import HelpModal, AddDeckModal, AddCardModal, EditDeckModal
from memotica.modals.delete_deck_modal import DeleteDeckModal
from memotica.models import Card, Deck


class DeckTree(Tree):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(label="*", *args, **kwargs)

    BINDINGS = [
        Binding("backspace", "delete", "Delete Deck"),
        Binding("ctrl+e", "edit", "Edit Deck"),
    ]

    selected_deck: reactive[str | None] = reactive(None)

    def on_mount(self) -> None:
        self.loading = True
        self.border_title = "Decks"

    def reload_decks(self, decks: list[Deck] | None = None) -> None:
        self.loading = True
        self.clear()
        self.selected_deck = None
        self.guide_depth = 3
        self.root.expand()

        if decks is None:
            self.loading = False
            return

        self.decks = decks
        for deck in self.decks:
            self.root.add_leaf(deck.name)

        self.loading = False

    def on_tree_node_selected(self, selectedNode: Tree.NodeSelected) -> None:
        self.selected_deck = f"{selectedNode.node.label}"
        self.post_message(self.DeckSelectedMessage(self.selected_deck))

    def action_edit(self) -> None:
        if self.selected_deck is None:
            return

        self.post_message(self.EditMessage(self.selected_deck))

    def action_delete(self) -> None:
        if self.selected_deck is None:
            return

        self.post_message(self.DeleteMessage(self.selected_deck))

    class DeleteMessage(Message):
        def __init__(self, deck_name: str) -> None:
            self.deck_name = deck_name
            super().__init__()

    class EditMessage(Message):
        def __init__(self, deck_name: str) -> None:
            self.deck_name = deck_name
            super().__init__()

    class DeckSelectedMessage(Message):
        def __init__(self, deck_name: str) -> None:
            self.deck_name = deck_name
            super().__init__()


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
        Binding("ctrl+n", "add_deck", "Add Deck", show=True),
        Binding("ctrl+a", "add_card", "Add Card", show=True),
    ]

    show_sidebar: reactive[bool] = reactive(True)

    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        cards_table = Container(
            DataTable(classes="cards__table"),
            classes="cards",
        )
        cards_table.border_title = "Cards"

        yield Header()
        yield DeckTree()
        yield cards_table
        yield Footer()

    def on_mount(self) -> None:
        # load decks
        self.__reload_decks()

        # load cards
        cards_table = self.query_one(DataTable)
        cards_table.add_columns(*("Front", "Back", "Reversible", "Deck"))
        self.__reload_cards()

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

                session.execute(stmt)
                session.commit()

                self.notify(
                    f"Updated deck '{message.deck_name}' to '{result}'",
                    severity="information",
                    timeout=5,
                )

                self.__reload_decks()
                self.__reload_cards()

        self.push_screen(EditDeckModal(message.deck_name, self.decks), callback)

    def on_deck_tree_deck_selected_message(
        self, message: DeckTree.DeckSelectedMessage
    ) -> None:
        self.__reload_cards(message.deck_name)

    def action_show_help_screen(self) -> None:
        self.push_screen(HelpModal())

    def action_toggle_deck_tree(self) -> None:
        self.show_sidebar = not self.show_sidebar
        deck_tree = self.query_one(DeckTree)
        deck_tree.can_focus = self.show_sidebar

        if self.show_sidebar:
            deck_tree.remove_class("hidden")
        else:
            deck_tree.add_class("hidden")

    def action_add_deck(self) -> None:
        def callback(result: Deck) -> None:
            self.session.add(result)
            self.session.commit()
            self.__reload_decks()

        self.push_screen(AddDeckModal(self.decks), callback)

    def action_add_card(self) -> None:
        if len(self.decks) <= 0:
            self.notify(
                "You need to add a Deck first! Check the help if you need to.",
                severity="error",
                timeout=5,
            )
            return

        def callback(result: Card) -> None:
            self.session.add(result)
            self.session.commit()
            self.__reload_cards()

        self.push_screen(AddCardModal(self.decks), callback)

    def __reload_decks(self) -> None:
        deck_tree = self.query_one(DeckTree)
        self.decks = self.session.query(Deck).all()
        deck_tree.reload_decks(self.decks)

    def __reload_cards(self, deck: str | None = None) -> None:
        cards_table = self.query_one(DataTable)
        cards_table.loading = True
        cards_table.clear()

        if deck:
            self.cards = (
                self.session.query(Card).join(Deck).filter(Deck.name == deck).all()
            )
        else:
            self.cards = self.session.query(Card).join(Deck).all()

        for card in self.cards:
            cards_table.add_row(
                shorten(card.front, width=20, placeholder="..."),
                shorten(card.back, width=20, placeholder="..."),
                card.reversible,
                card.deck.name,
            )

        cards_table.loading = False


if __name__ == "__main__":
    init_db()
    with Session(engine) as session:
        app = MemoticaApp(session)
        app.run()
