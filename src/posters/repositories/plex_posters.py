"""Plex repositories for poster retrieval."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from plexapi.server import PlexServer

from posters.domain import PosterJob


class HttpResponse(Protocol):
    def raise_for_status(self) -> None: ...

    def iter_content(self, chunk_size: int) -> Iterable[bytes]: ...


class HttpSession(Protocol):
    def get(self, url: str, **kwargs) -> HttpResponse:  # type: ignore[override]
        ...


@dataclass(frozen=True)
class PosterAsset:
    title: str
    url: str
    key: str | None = None


@dataclass(frozen=True)
class PlexPostersRepository:
    plex: PlexServer
    session: HttpSession | None = None

    def __post_init__(self) -> None:
        if self.session is None:
            # noinspection PyProtectedMember
            object.__setattr__(self, "session", self.plex._session)

    def iter_posters(self, library: str) -> Iterable[PosterAsset]:
        """Yield poster assets for items in a library section."""
        section = self.plex.library.section(library)
        for item in section.all():
            if item.posterUrl:
                key = str(getattr(item, "ratingKey", "")) or None
                yield PosterAsset(title=item.title, url=item.posterUrl, key=key)

    def iter_targets(self, job: PosterJob, limit: int | None = None) -> Iterable[Path]:
        """Yield target file paths for poster assets."""
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for index, asset in enumerate(self.iter_posters(job.library)):
            if limit is not None and index >= limit:
                break
            filename = self._safe_filename(asset.title, index, asset.key)
            yield output_dir / f"{filename}.jpg"

    def download_posters(self, job: PosterJob, limit: int | None = None) -> int:
        """Download posters to the job output directory. Returns count."""
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        for index, asset in enumerate(self.iter_posters(job.library)):
            if limit is not None and index >= limit:
                break
            filename = self._safe_filename(asset.title, index, asset.key)
            target = output_dir / f"{filename}.jpg"
            self._download(asset.url, target)
            downloaded += 1
        return downloaded

    def _download(self, url: str, target: Path) -> None:
        session = self.session
        if session is None:
            raise RuntimeError("HTTP session is not configured.")
        response = session.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)

    @staticmethod
    def _safe_filename(title: str, index: int, key: str | None = None) -> str:
        cleaned = "".join(ch for ch in title if ch.isalnum() or ch in (" ", "-", "_")).strip()
        cleaned = "_".join(cleaned.split())
        if not cleaned:
            cleaned = "poster"
        if key:
            return f"{cleaned}_{key}"
        return f"{cleaned}_{index}"
