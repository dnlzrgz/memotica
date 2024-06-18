import click
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from memotica.db import init_db
from memotica.tui import MemoticaApp
from memotica.config import Config


@click.command()
def run():
    config = Config()
    engine = create_engine(
        f"{config.sqlite_url}", connect_args={"check_same_thread": False}
    )
    init_db(engine)

    with Session(engine) as session:
        app = MemoticaApp(session)
        app.run()
