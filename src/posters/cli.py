import typer
from plexapi.server import PlexServer
from requests import RequestException

from posters.domain import PosterJob
from posters.repositories.plex_posters import DownloadReport, PlexPostersRepository
from posters.repositories.schemas import PostersDownloadRequest

app = typer.Typer(help="Download poster artwork")


@app.command()
def download(
    base_url: str = typer.Option(..., envvar="PLEX_BASE_URL"),
    token: str = typer.Option(..., envvar="PLEX_TOKEN"),
    library: str | None = typer.Option(None, envvar="PLEX_LIBRARY"),
    all_libraries: bool = typer.Option(False, "--all-libraries"),
    output_dir: str = typer.Option("posters"),
    limit: int | None = typer.Option(None),
    dry_run: bool = typer.Option(False),
) -> None:
    """Download posters for a library section."""
    if not library and not all_libraries:
        raise typer.BadParameter("Provide --library or --all-libraries.")
    if library and all_libraries:
        raise typer.BadParameter("Use --library or --all-libraries, not both.")
    request = PostersDownloadRequest(
        base_url=base_url,
        token=token,
        library=library,
        all_libraries=all_libraries,
        output_dir=output_dir,
        limit=limit,
        dry_run=dry_run,
    )
    plex = PlexServer(request.base_url, request.token)
    repository = PlexPostersRepository(plex=plex)
    try:
        if request.dry_run:
            targets = []
            for library_name in _resolve_libraries(plex, request.library, request.all_libraries):
                typer.echo(f"Library: {library_name}")
                job = PosterJob(
                    output_dir=request.output_dir,
                    library=library_name,
                    base_url=request.base_url,
                )
                targets.extend(repository.iter_targets(job=job, limit=request.limit))
            typer.echo(f"Dry run: {len(targets)} posters would be downloaded.")
            for target in targets[:5]:
                typer.echo(f"  - {target}")
            if len(targets) > 5:
                typer.echo("  - ...")
            return
        report = DownloadReport(downloaded=0, skipped_404=0, missing=[])
        for library_name in _resolve_libraries(plex, request.library, request.all_libraries):
            typer.echo(f"Library: {library_name}")
            job = PosterJob(
                output_dir=request.output_dir,
                library=library_name,
                base_url=request.base_url,
            )
            library_report = repository.download_posters(job=job, limit=request.limit)
            report = _merge_reports(report, library_report)
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


def _merge_reports(left: DownloadReport, right: DownloadReport) -> DownloadReport:
    return DownloadReport(
        downloaded=left.downloaded + right.downloaded,
        skipped_404=left.skipped_404 + right.skipped_404,
        missing=[*left.missing, *right.missing],
    )


def _resolve_libraries(plex: PlexServer, library: str | None, all_libraries: bool) -> list[str]:
    if all_libraries:
        return [section.title for section in plex.library.sections()]
    return [library] if library else []
