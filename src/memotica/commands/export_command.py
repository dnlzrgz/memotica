from datetime import datetime
import os
import zipfile
import click
import pandas as pd


@click.group(name="export")
@click.pass_context
def export_group(_):
    """
    Exports your decks, flashcards, and reviews.
    """
    pass


@click.command(name="all")
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


@click.command(name="flashcards")
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


export_group.add_command(export_all)
export_group.add_command(export_flashcards)
