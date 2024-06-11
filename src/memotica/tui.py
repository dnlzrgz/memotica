from sqlalchemy.orm import Session
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import DataTable, Footer, Header, Tree
from textual.reactive import reactive
from memotica.db import engine, init_db
from memotica.models import Card, Deck
from memotica.modals import CardModal, DeckModal, HelpModal, MessageModal


class MemoticaApp(App):
    """
    An Anki-like application for the terminal.
    """

    TITLE = "Memotica"
    CSS_PATH = "global.tcss"

    BINDINGS = [
        Binding("f1", "show_help_screen", "Help", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode", show=True),
        Binding("ctrl+n", "add_deck", "Add Deck", show=True),
        Binding("ctrl+a", "add_card", "Add Card", show=True),
    ]

    selected_deck: reactive[str | None] = reactive(None)

    def __init__(self, session: Session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session

    def compose(self) -> ComposeResult:
        deck_tree = VerticalScroll(
            Tree("*"),
            classes="tree",
        )
        deck_tree.border_title = "Decks"

        cards_table = Container(
            DataTable(classes="cards__table"),
            classes="cards",
        )
        cards_table.border_title = "Cards"

        yield Header()
        yield deck_tree
        yield cards_table
        yield Footer()

    def on_mount(self) -> None:
        # load decks
        self.__reload_decks()

        # load cards
        cards_table = self.query_one(DataTable)
        cards_table.loading = True
        self.cards = session.query(Card).join(Deck).all()
        cards_table.add_columns(*("Front", "Back", "Reversible", "Deck"))
        for card in self.cards:
            cards_table.add_row(card.front, card.back, card.reversible, card.deck.name)

        cards_table.loading = False

    def on_tree_node_selected(self, selectedNode: Tree.NodeSelected) -> None:
        self.selected_deck = f"{selectedNode.node.label}"

    def action_show_help_screen(self) -> None:
        self.push_screen(HelpModal())

    def action_add_deck(self) -> None:
        self.push_screen(DeckModal(), self.action_add_deck_callback)

    def action_add_deck_callback(self, result: Deck) -> None:
        self.session.add(result)
        self.session.commit()
        self.__reload_decks()

    def action_add_card(self) -> None:
        if len(self.decks) <= 0:
            self.push_screen(MessageModal("First, you need to add a Deck!", False))
            return

        self.push_screen(CardModal(self.decks), self.action_add_card_callback)

    def action_add_card_callback(self, result: Card) -> None:
        self.session.add(result)
        self.session.commit()
        self.__reload_cards(deck=None)

    def watch_selected_deck(self, old_deck: str, new_deck: str) -> None:
        if old_deck == new_deck:
            return None

        self.__reload_cards(deck=new_deck)

    def __reload_decks(self) -> None:
        deck_tree = self.query_one(Tree)
        deck_tree.loading = True
        deck_tree.clear()
        deck_tree.root.expand()

        self.decks = self.session.query(Deck).all()
        for deck in self.decks:
            deck_tree.root.add_leaf(deck.name)

        deck_tree.loading = False

    def __reload_cards(self, deck: str | None) -> None:
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
            cards_table.add_row(card.front, card.back, card.reversible, card.deck.name)

        cards_table.loading = False


if __name__ == "__main__":
    init_db()
    with Session(engine) as session:
        app = MemoticaApp(session)
        app.run()
