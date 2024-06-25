from datetime import datetime, date
from typing import List
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    parent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("decks.id"), nullable=True
    )
    parent = relationship("Deck", remote_side=[id], back_populates="sub_decks")
    sub_decks = relationship("Deck", back_populates="parent")

    flashcards: Mapped[List["Flashcard"]] = relationship(
        back_populates="deck",
        cascade="all,delete",
    )

    def __repr__(self) -> str:
        return f"Deck(id={self.id!r}, name={self.name!r}, parent={self.parent!r})"


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True)

    front: Mapped[str]
    back: Mapped[str]
    reversible: Mapped[bool] = mapped_column(Boolean(), default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), index=True)
    deck: Mapped["Deck"] = relationship(back_populates="flashcards")

    reviews: Mapped[List["Review"]] = relationship(
        back_populates="flashcard", cascade="all,delete"
    )

    def __repr__(self) -> str:
        return f"Flashcard(id={self.id!r}, front={self.front!r}, back={self.back!r}, reversible={self.reversible!r})"


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    ef: Mapped[float] = mapped_column(Float, default=2.5)
    interval: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[date] = mapped_column(Date, default=datetime.now().date())
    direction: Mapped[str] = mapped_column(String, default="ftb")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    last_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    flashcard_id: Mapped[int] = mapped_column(ForeignKey("flashcards.id"), index=True)
    flashcard: Mapped["Flashcard"] = relationship(back_populates="reviews")

    def __repr__(self) -> str:
        return f"Review(id={self.id!r}, ef={self.ef!r}, interval={self.interval!r}, repetitions={self.repetitions!r}, next_review={self.next_review!r}, direction={self.direction!r})"
