from typing import TypeVar, Generic, Type, Union
from datetime import datetime
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, update
from memotica.models import Deck, Flashcard, Review

T = TypeVar("T", bound=Union[Deck, Flashcard, Review])


class Repository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]) -> None:
        self.session = session
        self.model = model

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)

        return entity

    def get(self, id: int) -> T | None:
        return self.session.query(self.model).where(self.model.id == id).one_or_none()

    def get_all(self) -> list[T]:
        return self.session.query(self.model).all()

    def update(self, id: int, **kwargs) -> None:
        stmt = update(self.model).where(self.model.id == id).values(**kwargs)
        self.session.execute(stmt)
        self.session.commit()

    def delete(self, id: int) -> None:
        entity = self.get(id)
        if entity:
            self.session.delete(entity)
            self.session.commit()


class DeckRepository(Repository[Deck]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Deck)

    def get_with_subdecks(self, id: int) -> list[Deck]:
        deck_alias = aliased(Deck)

        cte = select(Deck.id).where(Deck.id == id).cte(name="subdecks", recursive=True)

        subdecks = cte.union_all(
            select(deck_alias.id).where(deck_alias.parent_id == cte.c.id)
        )

        result = self.session.execute(
            select(Deck).where(Deck.id.in_(select(subdecks.c.id)))
        )

        return result.all()

    def get_by_name(self, name: str) -> Deck | None:
        return self.session.query(Deck).where(Deck.name == name).one_or_none()


class FlashcardRepository(Repository[Flashcard]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Flashcard)

    def get_by_deck(
        self,
        deck_id: int,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Flashcard]:
        query = self.session.query(Flashcard).join(Deck).filter(Deck.id == deck_id)

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        return query.all()

    def get_by_decks(
        self,
        deck_ids: list[int],
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Flashcard]:
        query = self.session.query(Flashcard).filter(Flashcard.deck_id.in_(deck_ids))

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        return query.all()


class ReviewRepository(Repository[Review]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Review)

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

    def get_pending(self, deck_id: int) -> list[Review]:
        return (
            self.session.query(Review)
            .join(Flashcard)
            .filter(Flashcard.deck_id == deck_id)
            .filter(Review.next_review <= datetime.now().date())
            .order_by(Review.ef, Review.interval, Review.next_review)
            .all()
        )
