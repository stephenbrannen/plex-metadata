"""Plex repositories for poster retrieval."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from plexapi.server import PlexServer
from requests import HTTPError
from tqdm import tqdm

from posters.domain import PosterJob


class HttpResponse(Protocol):
    def raise_for_status(self) -> None: ...

    def iter_content(self, chunk_size: int) -> Iterable[bytes]: ...

    @property
    def headers(self) -> Mapping[str, str]: ...

    @property
    def status_code(self) -> int: ...


class HttpSession(Protocol):
    def get(self, url: str, **kwargs) -> HttpResponse:  # type: ignore[override]
        ...


@dataclass(frozen=True)
class PosterAsset:
    title: str
    url: str
    asset_name: str
    kind: str
    season: int | None = None
    episode: int | None = None


@dataclass(frozen=True)
class DownloadReport:
    downloaded: int
    skipped_404: int
    missing: list[PosterAsset]


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
        if section.type == "movie":
            for item in section.all():
                asset_name = self._asset_name_from_item(item)
                if item.posterUrl and asset_name:
                    yield PosterAsset(
                        title=item.title,
                        url=item.posterUrl,
                        asset_name=asset_name,
                        kind="movie",
                    )
            return
        if section.type == "show":
            for show in section.all():
                asset_name = self._asset_name_from_item(show)
                if not asset_name:
                    continue
                if show.posterUrl:
                    yield PosterAsset(
                        title=show.title,
                        url=show.posterUrl,
                        asset_name=asset_name,
                        kind="show",
                    )
                for season in show.seasons():
                    if season.posterUrl:
                        yield PosterAsset(
                            title=f"{show.title} Season {season.seasonNumber}",
                            url=season.posterUrl,
                            asset_name=asset_name,
                            kind="season",
                            season=season.seasonNumber,
                        )
                    for episode in season.episodes():
                        if episode.thumbUrl:
                            yield PosterAsset(
                                title=(
                                    f"{show.title} "
                                    f"S{season.seasonNumber:02d}E{episode.episodeNumber:02d}"
                                ),
                                url=episode.thumbUrl,
                                asset_name=asset_name,
                                kind="episode",
                                season=season.seasonNumber,
                                episode=episode.episodeNumber,
                            )
            return
        for item in section.all():
            asset_name = self._asset_name_from_item(item)
            if item.posterUrl and asset_name:
                yield PosterAsset(
                    title=item.title,
                    url=item.posterUrl,
                    asset_name=asset_name,
                    kind=section.type,
                )

    def iter_targets(self, job: PosterJob, limit: int | None = None) -> Iterable[Path]:
        """Yield target file paths for poster assets."""
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        assets = self._collect_assets(job.library, limit)
        for index, asset in enumerate(assets):
            asset_dir = output_dir / asset.asset_name
            asset_dir.mkdir(parents=True, exist_ok=True)
            filename = self._asset_filename(asset, index)
            yield asset_dir / f"{filename}.jpg"

    def download_posters(self, job: PosterJob, limit: int | None = None) -> DownloadReport:
        """Download posters to the job output directory. Returns report."""
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        skipped_404 = 0
        missing: list[PosterAsset] = []
        assets = self._collect_assets(job.library, limit)
        with tqdm(total=len(assets), desc="Posters", unit="poster") as poster_bar:
            for index, asset in enumerate(assets):
                asset_dir = output_dir / asset.asset_name
                asset_dir.mkdir(parents=True, exist_ok=True)
                filename = self._asset_filename(asset, index)
                target = asset_dir / f"{filename}.jpg"
                if self._download(asset.url, target, asset.title):
                    downloaded += 1
                else:
                    skipped_404 += 1
                    missing.append(asset)
                poster_bar.update(1)
        return DownloadReport(downloaded=downloaded, skipped_404=skipped_404, missing=missing)

    def _download(self, url: str, target: Path, title: str) -> bool:
        session = self.session
        if session is None:
            raise RuntimeError("HTTP session is not configured.")
        response = session.get(url, stream=True, timeout=30)
        try:
            response.raise_for_status()
        except HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return False
            raise
        total = int(response.headers.get("Content-Length", 0))
        with (
            target.open("wb") as handle,
            tqdm(
                total=total or None,
                desc=title,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=False,
            ) as file_bar,
        ):
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
                    if total:
                        file_bar.update(len(chunk))
        return True

    @staticmethod
    def _asset_filename(asset: PosterAsset, index: int) -> str:
        if asset.kind in ("movie", "show"):
            return "poster"
        if asset.kind == "season" and asset.season is not None:
            return f"Season{asset.season:02d}"
        if asset.kind == "episode" and asset.season is not None and asset.episode is not None:
            return f"S{asset.season:02d}E{asset.episode:02d}"
        return f"poster_{index}"

    @staticmethod
    def _asset_name_from_item(item) -> str | None:
        locations = getattr(item, "locations", None)
        if locations:
            return PlexPostersRepository._normalize_asset_name(Path(locations[0]).name)
        media = getattr(item, "media", None)
        if media:
            parts = getattr(media[0], "parts", None)
            if parts:
                raw = Path(parts[0].file).parent.name
                # If the media file is stored directly under a file-like folder, use the file name.
                if Path(raw).suffix:
                    raw = Path(parts[0].file).stem
                return PlexPostersRepository._normalize_asset_name(raw)
        show = getattr(item, "show", None)
        if show:
            show_obj = show()
            return PlexPostersRepository._asset_name_from_item(show_obj)
        return None

    @staticmethod
    def _normalize_asset_name(raw: str) -> str:
        raw = raw.strip()
        # Drop file extension if present.
        if Path(raw).suffix:
            raw = Path(raw).stem
        # Prefer "Title (YYYY)" if present.
        match = re.match(r"^(?P<title>.+?)\\s*\\((?P<year>\\d{4})\\)", raw)
        if match:
            title = match.group("title").strip()
            year = match.group("year")
            return f"{title} ({year})"
        # Otherwise strip common trailing tags.
        for token in (" {", " ["):
            if token in raw:
                raw = raw.split(token, 1)[0].strip()
        return raw

    def _collect_assets(self, library: str, limit: int | None) -> Sequence[PosterAsset]:
        assets = list(self.iter_posters(library))
        if limit is not None:
            return assets[:limit]
        return assets
