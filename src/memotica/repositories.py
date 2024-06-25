from datetime import datetime
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy import update
from memotica.models import Deck, Flashcard, Review


class Repository[T](ABC):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)

        return entity

    @abstractmethod
    def get(self, id: int) -> T | None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[T]:
        raise NotImplementedError

    @abstractmethod
    def update(self, id: int, **kwargs) -> None:
        raise NotImplementedError

    def delete(self, id: int) -> None:
        entity = self.get(id)
        if entity:
            self.session.delete(entity)
            self.session.commit()


class DeckRepository(Repository[Deck]):
    def get(self, id: int) -> Deck | None:
        return self.session.query(Deck).where(Deck.id == id).one_or_none()

    def get_by_name(self, name: str) -> Deck | None:
        return self.session.query(Deck).where(Deck.name == name).one_or_none()

    def get_all(self) -> list[Deck]:
        return self.session.query(Deck).order_by(Deck.name).all()

    def update(self, id: int, **kwargs) -> None:
        stmt = update(Deck).where(Deck.id == id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()

    def delete(self, id: int) -> None:
        deck = self.get(id)
        if deck:
            self.session.query(Deck).filter(Deck.parent_id == deck.id).update(
                {"parent_id": None}
            )
            self.session.delete(deck)

            self.session.commit()


class FlashcardRepository(Repository[Flashcard]):
    def get(self, id: int) -> Flashcard | None:
        return self.session.query(Flashcard).where(Flashcard.id == id).one_or_none()

    def get_by_deck(self, deck_id: int) -> list[Flashcard]:
        return self.session.query(Flashcard).join(Deck).filter(Deck.id == deck_id).all()

    def get_all(self) -> list[Flashcard]:
        return self.session.query(Flashcard).order_by(Flashcard.front).all()

    def update(self, id: int, **kwargs) -> None:
        stmt = update(Flashcard).where(Flashcard.id == id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()


class ReviewRepository(Repository[Review]):
    def get(self, id: int) -> Review | None:
        return self.session.query(Review).where(Review.id == id).one_or_none()

    def get_by_flashcard(self, flashcard_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .join(Flashcard)
            .filter(Flashcard.id == flashcard_id)
            .all()
        )

    def get_by_deck(self, deck_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .join(Flashcard)
            .filter(Flashcard.deck_id == deck_id)
            .all()
        )

    def get_all(self) -> list[Review]:
        return self.session.query(Review).all()

    def get_pending(self, deck_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .join(Flashcard)
            .filter(Flashcard.deck_id == deck_id)
            .filter(Review.next_review <= datetime.now().date())
            .order_by(Review.next_review, Review.ef, Review.interval)
            .all()
        )

    def update(self, id: int, **kwargs) -> None:
        stmt = update(Review).where(Review.id == id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()
