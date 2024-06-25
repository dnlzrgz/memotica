from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from memotica.models import Base, Deck, Flashcard, Review
from memotica.repositories import DeckRepository, FlashcardRepository, ReviewRepository


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def deck_repository(session):
    return DeckRepository(session)


@pytest.fixture
def flashcard_repository(session):
    return FlashcardRepository(session)


@pytest.fixture
def review_repository(session):
    return ReviewRepository(session)


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
        self.flashcard_repository.add(
            Flashcard(front="Wasser", back="Water", deck=self.deck)
        )
        self.flashcard_repository.add(
            Flashcard(front="Kuh", back="Cow", deck=self.deck)
        )

        flashcards_by_deck = self.flashcard_repository.get_by_deck(self.deck.id)
        assert len(flashcards_by_deck) == 2

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
        self.review_repository.add(Review(flashcard=self.flashcard, direction="btf"))

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

        self.review_repository.update(original_review.id, direction="btf")
        updated_review = self.review_repository.get(original_review.id)
        assert updated_review is not None
        assert updated_review.id == original_review.id
        assert updated_review.direction == "btf"

    def test_delete(self):
        review = self.review_repository.add(Review(flashcard=self.flashcard))
        assert review is not None

        self.review_repository.delete(review.id)
        deleted_review = self.review_repository.get(review.id)
        assert deleted_review is None
