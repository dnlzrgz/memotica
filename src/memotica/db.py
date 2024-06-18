from memotica.models import Base


def init_db(engine) -> None:
    Base.metadata.create_all(engine)
