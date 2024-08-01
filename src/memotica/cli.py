import click
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from memotica.config import Config
from memotica.db import init_db
from memotica.tui import Memotica
from memotica.commands.import_command import import_group
from memotica.commands.export_command import export_group


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx) -> None:
    """
    memotica is an easy, fast and minimalist application for your terminal that allows you
    to learn using space repetition.
    """

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
    Starts the TUI.
    """
    engine = ctx.obj["engine"]
    with Session(engine) as session:
        app = Memotica(session)
        app.run()


cli.add_command(import_group)
cli.add_command(export_group)
