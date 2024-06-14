from typing import List
from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))

    flashcards: Mapped[List["Flashcard"]] = relationship(
        back_populates="deck",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Deck(id={self.id!r}, name={self.name!r})"


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True)

    front: Mapped[str]
    back: Mapped[str]
    reversible: Mapped[bool] = mapped_column(Boolean(), default=True)

    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"))
    deck: Mapped["Deck"] = relationship(back_populates="flashcards")

    def __repr__(self) -> str:
        return f"Flashcard(id={self.id!r}, front={self.front!r}, back={self.back!r}, reversible={self.reversible!r})"
