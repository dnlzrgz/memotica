from sqlalchemy import create_engine
from memotica.models import Base

# TODO: add env variables or settings file
engine = create_engine("sqlite:///memotica.db", echo=True)


def init_db() -> None:
    # TODO: tables should be created by alembic
    Base.metadata.create_all(engine)
