from datetime import datetime
import os
import zipfile
import click
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from memotica.config import Config
from memotica.db import init_db
from memotica.models import Deck, Flashcard, Review
from memotica.repositories import FlashcardRepository, DeckRepository, ReviewRepository
from memotica.tui import MemoticaApp


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
    Starts the memotica TUI.
    """
    engine = ctx.obj["engine"]
    with Session(engine) as session:
        app = MemoticaApp(session)
        app.run()


@cli.group(
    name="export",
)
@click.pass_context
def export_command_group(_):
    """
    Exports your decks, flashcards, and reviews all in one ZIP
    file, or just your flashcards in a CSV document.
    """
    pass


@export_command_group.command(name="all")
@click.option(
    "--path",
    default=".",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    help="Path to the directory where the export file will be saved.",
    show_default=True,
)
@click.pass_context
def export_all(ctx, path):
    """
    Export all your decks, flashcards, and reviews to a ZIP file
    in the specified directory.
    """

    engine = ctx.obj["engine"]
    today = datetime.now()
    zip_filename = os.path.join(path, f'memotica_{today.strftime('%Y-%m-%d')}.zip')

    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for table in ["decks", "flashcards", "reviews"]:
            df = pd.read_sql_query(
                f"SELECT * FROM {table}",
                engine,
            )
            csv_content = df.to_csv(index=False)
            zipf.writestr(f"{table}.csv", csv_content)

        click.echo(f"Data exported successfully to '{zip_filename}'!")


@export_command_group.command(name="flashcards")
@click.option(
    "--file",
    "-f",
    default="flashcards.csv",
    type=click.Path(
        exists=False,
        file_okay=True,
        dir_okay=False,
    ),
    show_default=True,
    help="Name of the file to export flashcards to.",
)
@click.pass_context
def export_flashcards(ctx, file):
    """
    Export your flashcards to a CSV file.

    Note that this export file only includes decks that contains
    flashcards.
    """
    engine = ctx.obj["engine"]
    df = pd.read_sql_query(
        """
        SELECT f.front, f.back, f.reversible, d.name as deck
        FROM flashcards AS f
        LEFT JOIN decks AS d ON f.deck_id = d.id
        """,
        engine,
    )
    df.to_csv(file, index=False)

    click.echo(f"Flashcards exported successfully to {file}")


@cli.group(name="import")
@click.pass_context
def import_command_group(_):
    """
    Import your decks, flashcards, and reviews.
    """
    pass


@import_command_group.command(name="all")
@click.argument(
    "file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
)
@click.pass_context
def import_all(ctx, file):
    """
    Import all your data (decks, flashcards, and reviews) from a ZIP file.
    """

    engine = ctx.obj["engine"]
    import_files = ("decks.csv", "flashcards.csv", "reviews.csv")

    with zipfile.ZipFile(file, "r") as zipf:
        files_in_zip = zipf.namelist()
        if len(files_in_zip) != len(import_files):
            click.echo(
                f"Somethings is wrong with your backup file. It should contain {len(import_files)} but instead contains {files_in_zip} files!"
            )
            return

        if any(file not in files_in_zip for file in import_files):
            click.echo(
                "Warning: one or more required files not found in the backup file."
            )
            return

        for import_file in import_files:
            with zipf.open(import_file, "r") as f:
                df = pd.read_csv(f)
                df.to_sql(
                    import_file[:-4],
                    engine,
                    if_exists="append",
                    index=False,
                )

    click.echo("Data imported successfully!")


@import_command_group.command(name="flashcards")
@click.argument(
    "file",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
)
@click.pass_context
def import_flashcards(ctx, file):
    """
    Import flashcard from a CSV file.

    This command will import flashcards from a CSV file and create the
    necessary decks.
    """
    engine = ctx.obj["engine"]
    with Session(engine) as session:
        flashcards_repository = FlashcardRepository(session)
        decks_repository = DeckRepository(session)
        reviews_repository = ReviewRepository(session)

        df = pd.read_csv(file)
        decks = {}
        for deck_name in df["deck"].unique():
            deck = decks_repository.add(Deck(name=deck_name))
            decks[deck_name] = deck.id

        for _, row in df.iterrows():
            flashcard = flashcards_repository.add(
                Flashcard(
                    front=row["front"],
                    back=row["back"],
                    reversible=row["reversible"],
                    deck_id=decks[row["deck"]],
                )
            )

            reviews_repository.add(Review(flashcard=flashcard))
            if flashcard.reversible:
                reviews_repository.add(Review(flashcard=flashcard, reversed=True))
