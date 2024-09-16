from typing import TypeVar, Generic, Type, Union
from datetime import datetime, timezone
from functools import lru_cache
from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, update, func
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

        return result.scalars().all()

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

    def delete_by_flashcard(self, flashcard_id: int) -> None:
        reviews = self.get_by_flashcard(flashcard_id)
        if reviews:
            for review in reviews:
                self.delete(review.id)


class StatisticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @lru_cache
    def count_flashcards(self, deck_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Flashcard)
        if deck_id:
            stmt = stmt.where(Flashcard.deck_id == deck_id)

        count = self.session.execute(stmt).scalar()
        return count if count else 0

    @lru_cache
    def count_reviews(self, deck_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Review)
        if deck_id:
            stmt = stmt.join(Flashcard).where(Flashcard.deck_id == deck_id)

        count = self.session.execute(stmt).scalar()
        return count if count else 0

    @lru_cache
    def count_pending_reviews(self, deck_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Review)
        if deck_id:
            stmt = stmt.join(Flashcard).where(Flashcard.deck_id == deck_id)

        stmt = stmt.where(Review.next_date <= datetime.now(timezone.utc).date())

        count = self.session.execute(stmt).scalar()
        return count if count else 0

    @lru_cache
    def count_reviewed_reviews(self, deck_id: int | None = None) -> int:
        stmt = select(func.count()).select_from(Review)
        if deck_id:
            stmt = stmt.join(Flashcard).where(Flashcard.deck_id == deck_id)

        stmt = stmt.where(Review.next_date > datetime.now(timezone.utc).date())

        count = self.session.execute(stmt).scalar()
        return count if count else 0

    @lru_cache
    def calc_avg_review_score(self, deck_id: int | None = None) -> float:
        stmt = select(func.avg(Review.ef)).select_from(Review)
        if deck_id:
            stmt = stmt.join(Flashcard).where(Flashcard.deck_id == deck_id)

        avg_score = self.session.execute(stmt).scalar()
        return avg_score if avg_score else 0

    def calc_learning_rate(self, deck_id: int | None = None) -> float:
        return 0
