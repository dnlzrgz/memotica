import os
import zipfile
from datetime import datetime
import click
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from memotica.db import init_db
from memotica.tui import MemoticaApp
from memotica.config import Config


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx) -> None:
    ctx.ensure_object(dict)

    config = Config()
    engine = create_engine(f"{config.sqlite_url}")
    init_db(engine)

    ctx.obj["engine"] = engine

    if ctx.invoked_subcommand is None:
        ctx.forward(run)


@cli.command()
@click.pass_context
def run(ctx):
    """
    Starts the memotica TUI.
    """
    engine = ctx.obj["engine"]
    with Session(engine) as session:
        app = MemoticaApp(session)
        app.run()


@cli.command()
@click.pass_context
@click.option(
    "--path",
    default=".",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
)
def export(ctx, path):
    """
    Exports your memotica data.
    """

    engine = ctx.obj["engine"]

    today = datetime.now()
    zip_filename = os.path.join(path, f"memotica_{today.strftime('%Y-%m-%d')}.zip")

    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for table_name in ["decks", "flashcards", "reviews"]:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, engine)
            txt = df.to_csv(index=False)
            zipf.writestr(f"{table_name}.csv", txt)

    click.echo("Data exported successfully!")
