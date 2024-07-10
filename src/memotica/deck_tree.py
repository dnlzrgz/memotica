from textual.binding import Binding
from textual.widgets import Tree
from memotica.messages import AddDeck, DeleteDeck, EditDeck, SelectDeck
from memotica.models import Deck


class DeckTree(Tree):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(label="*", *args, **kwargs)

    BINDINGS = [
        Binding("backspace", "delete", "Delete"),
        Binding("ctrl+e", "edit", "Edit"),
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
    ]

    def on_mount(self) -> None:
        self.border_title = "Decks"

    def on_tree_node_selected(self, selectedNode: Tree.NodeSelected) -> None:
        node_label = f"{selectedNode.node.label}"
        if node_label == "*":
            self.post_message(SelectDeck())
        else:
            self.post_message(SelectDeck(node_label))

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")

    def add_deck(self) -> None:
        self.post_message(AddDeck())

    def action_edit(self) -> None:
        self.post_message(EditDeck())

    def action_delete(self) -> None:
        self.post_message(DeleteDeck())

    def reload(self, decks: list[Deck] | None = None) -> None:
        self.loading = True
        self.clear()

        self.post_message(SelectDeck())
        self.guide_depth = 3
        self.root.expand()

        if not decks:
            self.loading = False
            return

        root_decks = [deck for deck in self.app.decks if deck.parent_id is None]

        def add_deck_to_tree(parent, deck):
            if not deck.sub_decks:
                node = parent.add_leaf(deck.name)
                return

            node = parent.add(deck.name)
            for sub_deck in deck.sub_decks:
                add_deck_to_tree(node, sub_deck)

        for root_deck in root_decks:
            add_deck_to_tree(self.root, root_deck)

        self.loading = False
