"""Shared domain objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaItem:
    key: str
    title: str
    year: int | None = None
