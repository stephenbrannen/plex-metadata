import typer

from posters import cli as posters_cli

app = typer.Typer(help="CLI tools for Plex metadata management")
app.add_typer(posters_cli.app, name="posters")


if __name__ == "__main__":
    app()
