import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from memotica.models import Base
from memotica.repositories import DeckRepository, FlashcardRepository, ReviewRepository


@pytest.fixture(scope="function", autouse=True)
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def deck_repository(session: Session):
    return DeckRepository(session)


@pytest.fixture
def flashcard_repository(session: Session):
    return FlashcardRepository(session)


@pytest.fixture
def review_repository(session: Session):
    return ReviewRepository(session)
