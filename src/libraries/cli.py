from __future__ import annotations

import typer
from plexapi.server import PlexServer

from libraries.repositories.plex_libraries import PlexLibrariesRepository
from libraries.schemas import LibrariesListRequest

app = typer.Typer(help="List Plex libraries")


@app.command()
def list(
    base_url: str = typer.Option(..., envvar="PLEX_BASE_URL"),
    token: str = typer.Option(..., envvar="PLEX_TOKEN"),
) -> None:
    """List Plex libraries."""
    request = LibrariesListRequest(base_url=base_url, token=token)
    plex = PlexServer(request.base_url, request.token)
    repository = PlexLibrariesRepository(plex=plex)

    for library in repository.list_libraries():
        typer.echo(f"{library.title} ({library.type})")
