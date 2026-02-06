"""Posters domain objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PosterJob:
    output_dir: str
    library: str
    base_url: str
