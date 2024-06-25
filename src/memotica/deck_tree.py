from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Tree
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

    current_node_label: reactive[str | None] = reactive(None)

    def on_mount(self) -> None:
        self.loading = True
        self.border_title = "Decks"

    def reload_decks(self, decks: list[Deck] | None = None) -> None:
        self.loading = True
        self.clear()

        self.current_node_label = None
        self.guide_depth = 3
        self.root.expand()

        if not decks:
            self.loading = False
            return

        root_decks = [deck for deck in decks if deck.parent_id is None]

        def add_deck_to_tree(parent, deck):
            node = parent.add(deck.name)
            for sub_deck in deck.sub_decks:
                add_deck_to_tree(node, sub_deck)

        for root_deck in root_decks:
            add_deck_to_tree(self.root, root_deck)

        self.loading = False

    def on_tree_node_selected(self, selectedNode: Tree.NodeSelected) -> None:
        node_label = f"{selectedNode.node.label}"
        if node_label == "*":
            return

        self.current_node_label = node_label
        self.post_message(self.DeckSelectedMessage(self.current_node_label))

    def on_focus(self) -> None:
        self.add_class("focused")

    def on_blur(self) -> None:
        self.remove_class("focused")

    def action_edit(self) -> None:
        if self.current_node_label is None:
            return

        self.post_message(self.EditMessage(self.current_node_label))

    def action_delete(self) -> None:
        if self.current_node_label is None:
            return

        self.post_message(self.DeleteMessage(self.current_node_label))

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
