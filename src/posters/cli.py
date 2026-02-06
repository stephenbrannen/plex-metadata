import typer

from posters.schemas import PostersDownloadRequest

app = typer.Typer(help="Download poster artwork")


@app.command()
def download(output_dir: str = "posters") -> None:
    """Placeholder command to download posters."""
    request = PostersDownloadRequest(output_dir=output_dir)
    typer.echo(
        "Posters download not implemented yet. "
        f"Output dir: {request.output_dir}"
    )
