from datetime import datetime, timedelta
import pytest
from memotica.models import Deck, Flashcard, Review


class TestDeckRepository:
    @pytest.fixture(autouse=True)
    def setup(self, deck_repository):
        self.deck_repository = deck_repository

    def test_add(self):
        deck = Deck(name="Testing 101")
        assert deck.id is None

        deck_in_db = self.deck_repository.add(deck)
        assert deck_in_db.id is not None
        assert deck_in_db.name == "Testing 101"

    def test_get(self):
        deck = self.deck_repository.add(Deck(name="Testing 101"))

        deck_in_db = self.deck_repository.get(deck.id)
        assert deck_in_db is not None
        assert deck_in_db.name == "Testing 101"

    def test_get_with_subdecks(self):
        NUM_CHILDREN = 5

        parent_deck = self.deck_repository.add(Deck(name="Parent"))
        children = [
            self.deck_repository.add(Deck(name=f"Child {i}", parent=parent_deck))
            for i in range(NUM_CHILDREN)
        ]

        for child in children:
            assert child.parent_id == parent_deck.id
            self.deck_repository.add(Deck(name=f"Child of {child.name}", parent=child))

        decks_in_db = self.deck_repository.get_with_subdecks(parent_deck.id)
        assert len(decks_in_db) == (NUM_CHILDREN * 2) + 1

    def test_get_by_name(self):
        deck = self.deck_repository.add(Deck(name="Testing 101"))

        deck_in_db = self.deck_repository.get_by_name("Testing 101")
        assert deck_in_db is not None
        assert deck_in_db.id == deck.id

    def test_get_all(self):
        decks_in_db = self.deck_repository.get_all()
        assert len(decks_in_db) == 0

        self.deck_repository.add(Deck(name="one"))
        self.deck_repository.add(Deck(name="two"))

        decks_in_db = self.deck_repository.get_all()
        assert len(decks_in_db) == 2

    def test_update(self):
        original_deck = self.deck_repository.add(Deck(name="Testing 101"))
        self.deck_repository.update(original_deck.id, name="Testing")

        updated_deck = self.deck_repository.get(original_deck.id)
        assert updated_deck is not None
        assert updated_deck.id == original_deck.id
        assert updated_deck.name == "Testing"

    def test_delete(self):
        deck = self.deck_repository.add(Deck(name="Testing 101"))
        assert deck is not None

        self.deck_repository.delete(deck.id)
        deleted_deck = self.deck_repository.get(deck.id)
        assert deleted_deck is None

    def test_delete_deck_with_sub_deck(self):
        parent_deck = self.deck_repository.add(Deck(name="Testing"))
        assert parent_deck is not None

        children_deck = self.deck_repository.add(
            Deck(name="Testing 101", parent=parent_deck)
        )
        assert children_deck is not None

        self.deck_repository.delete(parent_deck.id)

        children_deck = self.deck_repository.get(children_deck.id)
        assert children_deck.parent is None
        assert children_deck.parent_id is None

    def test_delete_sub_deck(self):
        parent_deck = self.deck_repository.add(Deck(name="Testing"))
        assert parent_deck is not None

        children_deck = self.deck_repository.add(
            Deck(name="Testing 101", parent=parent_deck)
        )
        assert children_deck is not None

        parent_deck = self.deck_repository.get(parent_deck.id)
        assert len(parent_deck.sub_decks) == 1

        self.deck_repository.delete(children_deck.id)

        parent_deck = self.deck_repository.get(parent_deck.id)
        assert len(parent_deck.sub_decks) == 0


class TestFlashcardRepository:
    @pytest.fixture(autouse=True)
    def setup(self, deck_repository, flashcard_repository):
        self.deck_repository = deck_repository
        self.deck = self.deck_repository.add(Deck(name="Testing 101"))

        self.flashcard_repository = flashcard_repository

    def test_add(self):
        flashcard = Flashcard(front="Wasser", back="Water", deck=self.deck)
        assert flashcard.id is None

        flashcard_in_db = self.flashcard_repository.add(flashcard)
        assert flashcard_in_db.id is not None
        assert flashcard_in_db.front == "Wasser"
        assert flashcard_in_db.back == "Water"
        assert flashcard_in_db.deck_id == self.deck.id
        assert not flashcard_in_db.reversible

    def test_get(self):
        flashcard = self.flashcard_repository.add(
            Flashcard(front="Wasser", back="Water", deck=self.deck)
        )
        assert flashcard is not None

        flashcard_in_db = self.flashcard_repository.get(flashcard.id)
        assert flashcard_in_db is not None
        assert flashcard_in_db.front == "Wasser"
        assert flashcard_in_db.back == "Water"
        assert flashcard_in_db.deck_id == self.deck.id

    def test_get_by_deck(self):
        flashcards = [
            self.flashcard_repository.add(
                Flashcard(front=f"Front {i}", back=f"Back {i}", deck=self.deck)
            )
            for i in range(10)
        ]

        flashcards_by_deck = self.flashcard_repository.get_by_deck(self.deck.id)
        assert len(flashcards_by_deck) == len(flashcards)

    def test_get_by_decks(self):
        NUM_FLASHCARDS = 10
        _ = [
            self.flashcard_repository.add(
                Flashcard(front=f"Front {i}", back=f"Back {i}", deck=self.deck)
            )
            for i in range(NUM_FLASHCARDS)
        ]

        sub_deck = self.deck_repository.add(Deck(name="Subdeck", parent=self.deck))
        assert sub_deck is not None

        _ = [
            self.flashcard_repository.add(
                Flashcard(front=f"Front {i}", back=f"Back {i}", deck=sub_deck)
            )
            for i in range(NUM_FLASHCARDS)
        ]

        flashcards_in_decks = self.flashcard_repository.get_by_decks(
            [self.deck.id, sub_deck.id]
        )
        assert len(flashcards_in_decks) == NUM_FLASHCARDS * 2

    def test_get_all(self):
        self.flashcard_repository.add(
            Flashcard(front="Wasser", back="Water", deck=self.deck)
        )
        self.flashcard_repository.add(
            Flashcard(front="Kuh", back="Cow", deck=self.deck)
        )

        flashcards_in_db = self.flashcard_repository.get_all()
        assert len(flashcards_in_db) == 2

    def test_update(self):
        original_flashcard = self.flashcard_repository.add(
            Flashcard(front="Wasser", back="Water", deck=self.deck)
        )
        self.flashcard_repository.update(original_flashcard.id, reversible=True)

        updated_flashcard = self.flashcard_repository.get(original_flashcard.id)
        assert updated_flashcard is not None
        assert updated_flashcard.id == original_flashcard.id
        assert updated_flashcard.front == original_flashcard.front
        assert updated_flashcard.back == original_flashcard.back
        assert original_flashcard.reversible

    def test_delete(self):
        flashcard = self.flashcard_repository.add(
            Flashcard(front="Wassert", back="Water", deck=self.deck)
        )
        assert flashcard is not None

        self.flashcard_repository.delete(flashcard.id)
        deleted_flashcard = self.flashcard_repository.get(flashcard.id)
        assert deleted_flashcard is None


class TestReviewRepository:
    @pytest.fixture(autouse=True)
    def setup(self, deck_repository, flashcard_repository, review_repository):
        self.deck_repository = deck_repository
        self.deck = self.deck_repository.add(Deck(name="Testing 101"))

        self.flashcard_repository = flashcard_repository
        self.flashcard = flashcard_repository.add(
            Flashcard(
                front="Wasser",
                back="Water",
                deck=self.deck,
            )
        )

        self.review_repository = review_repository

    def test_add(self):
        review = Review(flashcard=self.flashcard)
        review_in_db = self.review_repository.add(review)
        assert review_in_db.id is not None

    def test_get(self):
        review = self.review_repository.add(Review(flashcard=self.flashcard))
        assert review is not None

        review_in_db = self.review_repository.get(review.id)
        assert review_in_db is not None
        assert review_in_db.id == review.id

    def test_get_by_flashcard(self):
        review = self.review_repository.add(Review(flashcard=self.flashcard))
        assert review is not None

        reviews_in_db = self.review_repository.get_by_flashcard(self.flashcard.id)
        assert len(reviews_in_db) == 1
        assert reviews_in_db[0].id == review.id

    def test_get_by_deck(self):
        review = self.review_repository.add(Review(flashcard=self.flashcard))
        assert review is not None

        reviews_in_db = self.review_repository.get_by_deck(self.deck.id)
        assert len(reviews_in_db) == 1
        assert reviews_in_db[0].id == review.id

    def test_get_all(self):
        self.review_repository.add(Review(flashcard=self.flashcard))
        self.review_repository.add(Review(flashcard=self.flashcard, reversed=True))

        reviews_in_db = self.review_repository.get_all()
        assert len(reviews_in_db) == 2

    def test_get_pending(self):
        pending_review = self.review_repository.add(Review(flashcard=self.flashcard))
        self.review_repository.add(
            Review(flashcard=self.flashcard, next_review=datetime.now() + timedelta(1))
        )

        reviews_in_db = self.review_repository.get_all()
        assert len(reviews_in_db) == 2

        pending_reviews = self.review_repository.get_pending(self.deck.id)
        assert len(pending_reviews) == 1
        assert pending_reviews[0].id == pending_review.id

    def test_update(self):
        original_review = self.review_repository.add(Review(flashcard=self.flashcard))

        self.review_repository.update(original_review.id, reversed=True)
        updated_review = self.review_repository.get(original_review.id)
        assert updated_review is not None
        assert updated_review.id == original_review.id
        assert updated_review.reversed

    def test_delete(self):
        review = self.review_repository.add(Review(flashcard=self.flashcard))
        assert review is not None

        self.review_repository.delete(review.id)
        deleted_review = self.review_repository.get(review.id)
        assert deleted_review is None

    def test_delete_by_flashcard(self):
        review = self.review_repository.add(Review(flashcard=self.flashcard))
        assert review is not None

        self.review_repository.delete_by_flashcard(self.flashcard.id)
        deleted_review = self.review_repository.get(review.id)
        assert deleted_review is None
