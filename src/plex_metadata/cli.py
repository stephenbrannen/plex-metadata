import typer

from libraries import cli as libraries_cli
from posters import cli as posters_cli

app = typer.Typer(help="CLI tools for Plex metadata management")
app.add_typer(posters_cli.app, name="posters")
app.add_typer(libraries_cli.app, name="libraries")


if __name__ == "__main__":
    app()
