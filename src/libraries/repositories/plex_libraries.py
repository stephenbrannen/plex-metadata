"""Plex repository for library listing."""

from dataclasses import dataclass

from plexapi.server import PlexServer

from libraries.domain import LibraryInfo


@dataclass(frozen=True)
class PlexLibrariesRepository:
    plex: PlexServer

    def list_libraries(self) -> list[LibraryInfo]:
        return [
            LibraryInfo(title=section.title, type=section.type)
            for section in self.plex.library.sections()
        ]
