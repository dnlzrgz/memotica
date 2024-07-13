import zipfile
import click
import pandas as pd
from sqlalchemy.orm import Session
from memotica.models import Deck, Flashcard, Review
from memotica.repositories import FlashcardRepository, DeckRepository, ReviewRepository


@click.group(name="import")
@click.pass_context
def import_group(_):
    """
    Import your decks, flashcards, and reviews.
    """
    pass


@click.command(name="all")
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
    Import all your data from a ZIP file.

    This command allows you to import all your previously exported data,
    including decks, flashcards, and reviews, from a ZIP file.
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


@click.command(name="flashcards")
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
        decks = {
            deck_name: decks_repository.add(Deck(name=deck_name))
            for deck_name in df["deck"].unique()
        }

        for _, row in df.iterrows():
            flashcard = flashcards_repository.add(
                Flashcard(
                    front=row["front"],
                    back=row["back"],
                    reversible=row["reversible"],
                    deck=decks[row["deck"]],
                )
            )

            reviews_repository.add(Review(flashcard=flashcard))
            if flashcard.reversible:
                reviews_repository.add(
                    Review(
                        flashcard=flashcard,
                        reversed=True,
                    )
                )

            session.commit()

        click.echo(f"Flashcards imported successfully from '{file}'!")


import_group.add_command(import_all)
import_group.add_command(import_flashcards)
