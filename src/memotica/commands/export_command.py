import os
import zipfile
from io import BytesIO
from datetime import datetime
import click
import pandas as pd
from sqlalchemy import text


@click.group(
    name="export",
    invoke_without_command=True,
)
@click.pass_context
def export_group(ctx):
    """
    Exports your decks, flashcards, and reviews.
    """

    if ctx.invoked_subcommand is None:
        ctx.forward(export_flashcards)


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
@click.option(
    "--decks",
    "-d",
    multiple=True,
    help="List of decks to filter by. By default all decks will be exported.",
)
@click.pass_context
def export_all(ctx, path, decks):
    """
    Export all your decks, flashcards, and reviews to a ZIP file
    in the specified directory.
    """

    engine = ctx.obj["engine"]
    today = datetime.now()
    zip_filename = os.path.join(path, f'memotica_{today.strftime("%Y-%m-%d")}.zip')

    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for table in ["decks", "flashcards", "reviews"]:
            df = pd.read_sql_table(
                table,
                con=engine.connect(),
            )

            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            zipf.writestr(f"{table}.csv", csv_buffer.getvalue())

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
@click.option(
    "--decks",
    "-d",
    multiple=True,
    help="List of decks to filter by. By default all decks will be exported.",
)
@click.pass_context
def export_flashcards(ctx, file, decks):
    """
    Export your flashcards to a CSV file.

    Note that this export file only includes decks that contains
    flashcards.
    """

    engine = ctx.obj["engine"]
    query = text("""
        SELECT f.front, f.back, f.reversible, d.name as deck
        FROM flashcards AS f
        LEFT JOIN decks AS d ON f.deck_id = d.id
        """)

    df = pd.read_sql_query(query, engine)

    if decks:
        df = df[df["deck"].isin(decks)]

    df.to_csv(file, index=False)

    click.echo(f"Flashcards exported successfully to {file}")


export_group.add_command(export_all)
export_group.add_command(export_flashcards)
