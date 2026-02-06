"""Libraries domain objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LibraryInfo:
    title: str
    type: str
