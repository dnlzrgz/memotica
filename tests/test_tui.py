import pytest
from sqlalchemy.orm import Session
from memotica.tui import Memotica


@pytest.mark.asyncio
async def test_user_cannot_add_flashcards_before_deck(session: Session):
    app = Memotica(session)
    async with app.run_test() as pilot:
        await pilot.press("ctrl+n")
        assert len(app.screen_stack) == 2, "Deck modal should be open"

        await pilot.press("ctrl+q")
        assert len(app.screen_stack) == 1, "Deck modal should be closed"

        await pilot.press("ctrl+a")
        assert (
            len(app.screen_stack) == 1
        ), "Flashcard modal can't be open since there are no decks yet"


@pytest.mark.asyncio
async def test_user_can_add_decks(session: Session):
    app = Memotica(session)
    async with app.run_test() as pilot:
        decks_in_app = pilot.app.decks
        assert len(decks_in_app) == 0, "There should be no decks"

        await pilot.press("ctrl+n")
        await pilot.press("t", "e", "s", "t")
        await pilot.press("enter")

        decks_in_app = pilot.app.decks
        assert len(decks_in_app) == 1, "There should be a deck"


@pytest.mark.asyncio
async def test_user_cannot_add_decks_with_same_name(session: Session):
    app = Memotica(session)
    async with app.run_test() as pilot:
        decks_in_app = pilot.app.decks
        assert len(decks_in_app) == 0, "There should be no decks"

        await pilot.press("ctrl+n")
        await pilot.press("t", "e", "s", "t")
        await pilot.press("enter")
        assert len(app.screen_stack) == 1, "There should be a deck"

        await pilot.press("ctrl+n")
        await pilot.press("t", "e", "s", "t")
        await pilot.press("enter")
        assert (
            len(app.screen_stack) == 2
        ), "Deck modal cannot close since deck name is invalid"

        decks_in_app = pilot.app.decks
        assert len(decks_in_app) == 1, "There should be a deck"
