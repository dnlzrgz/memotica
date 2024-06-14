from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Tree
from memotica.models import Deck


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
