import typer
from plexapi.server import PlexServer
from requests import RequestException

from posters.domain import PosterJob
from posters.repositories.plex_posters import DownloadReport, PlexPostersRepository
from posters.schemas import PostersDownloadRequest

app = typer.Typer(help="Download poster artwork")


@app.command()
def download(
    base_url: str = typer.Option(..., envvar="PLEX_BASE_URL"),
    token: str = typer.Option(..., envvar="PLEX_TOKEN"),
    library: str = typer.Option(..., envvar="PLEX_LIBRARY"),
    output_dir: str = typer.Option("posters"),
    limit: int | None = typer.Option(None),
    dry_run: bool = typer.Option(False),
) -> None:
    """Download posters for a library section."""
    request = PostersDownloadRequest(
        base_url=base_url,
        token=token,
        library=library,
        output_dir=output_dir,
        limit=limit,
        dry_run=dry_run,
    )
    plex = PlexServer(request.base_url, request.token)
    repository = PlexPostersRepository(plex=plex)
    job = PosterJob(
        output_dir=request.output_dir,
        library=request.library,
        base_url=request.base_url,
    )
    try:
        if request.dry_run:
            targets = list(repository.iter_targets(job=job, limit=request.limit))
            typer.echo(f"Dry run: {len(targets)} posters would be downloaded.")
            for target in targets[:5]:
                typer.echo(f"  - {target}")
            if len(targets) > 5:
                typer.echo("  - ...")
            return
        report = repository.download_posters(job=job, limit=request.limit)
    except RequestException as exc:
        typer.secho(f"Request failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        typer.secho(f"Configuration error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    _print_report(report, request.output_dir)


def _print_report(report: DownloadReport, output_dir: str) -> None:
    typer.echo(f"Downloaded {report.downloaded} posters to {output_dir}")
    if report.skipped_404 == 0:
        return
    typer.secho(f"Skipped {report.skipped_404} posters (404)", fg=typer.colors.YELLOW)
    typer.echo("Missing posters:")
    typer.echo("Title | URL")
    typer.echo("--- | ---")
    for asset in report.missing:
        typer.echo(f"{asset.title} | {asset.url}")
