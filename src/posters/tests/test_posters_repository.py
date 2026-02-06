"""
  1. Project language level
      - File → Project Structure…
      - Set Project SDK to the venv interpreter
      - Set Project language level to 3.14 (or at least 3.10)
  2. Inspection profile language level
      - Settings → Editor → Inspections
      - At the top, ensure the profile is tied to the project SDK (not “Python 2.7”)
      - If there’s a Python Language Level selector, set it to your SDK
  3. Invalidate caches
      - File → Invalidate Caches / Restart…

  If the warning persists, tell me the exact inspection name and the file it flags, and I’ll pinpoint the
  setting to adjust.
"""

from __future__ import annotations

from collections.abc import Buffer
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from posters.domain import PosterJob
from posters.repositories.plex_posters import PlexPostersRepository


@pytest.fixture()
def sample_items() -> tuple[MagicMock, MagicMock]:
    return (
        MagicMock(title="Movie One", posterUrl="http://example.com/1.jpg"),
        MagicMock(title="Movie Two", posterUrl="http://example.com/2.jpg"),
    )


@pytest.fixture()
def fake_plex(sample_items: tuple[MagicMock, MagicMock]) -> MagicMock:
    plex = MagicMock()
    section = MagicMock()
    section.all.return_value = sample_items
    plex.library.section.return_value = section
    return plex


@pytest.fixture()
def repository(fake_plex: MagicMock) -> PlexPostersRepository:
    return PlexPostersRepository(plex=fake_plex)


def test_safe_filename_falls_back_on_empty_title() -> None:
    name = PlexPostersRepository._safe_filename("", 3)
    assert name == "poster_3"


def test_iter_posters_yields_only_items_with_urls(
    sample_items: tuple[MagicMock, MagicMock]
) -> None:
    first_item, _ = sample_items
    items = [
        first_item,
        MagicMock(title="Movie Two", posterUrl=None),
    ]
    plex = MagicMock()
    section = MagicMock()
    section.all.return_value = items
    plex.library.section.return_value = section
    repo = PlexPostersRepository(plex=plex)

    posters = list(repo.iter_posters("Movies"))

    assert len(posters) == 1
    (poster,) = posters
    assert poster.title == "Movie One"
    assert poster.url == "http://example.com/1.jpg"


def test_download_posters_writes_files(
    tmp_path: Path, repository: PlexPostersRepository
) -> None:
    def fake_download(_self: PlexPostersRepository, _url: str, target: Path) -> None:
        target.write_bytes(cast(Buffer, b"fake"))

    with patch.object(PlexPostersRepository, "_download", autospec=True) as mock_download:
        mock_download.side_effect = fake_download
        job = PosterJob(output_dir=str(tmp_path), library="Movies", base_url="http://x")
        count = repository.download_posters(job=job)

    assert count == 2
    assert (tmp_path / "Movie_One.jpg").exists()
    assert (tmp_path / "Movie_Two.jpg").exists()


def test_download_posters_respects_limit(
    tmp_path: Path, repository: PlexPostersRepository
) -> None:
    def fake_download(_self: PlexPostersRepository, _url: str, target: Path) -> None:
        target.write_bytes(cast(Buffer, b"fake"))

    with patch.object(PlexPostersRepository, "_download", autospec=True) as mock_download:
        mock_download.side_effect = fake_download
        job = PosterJob(output_dir=str(tmp_path), library="Movies", base_url="http://x")
        count = repository.download_posters(job=job, limit=1)

    assert count == 1
    assert (tmp_path / "Movie_One.jpg").exists()
    assert not (tmp_path / "Movie_Two.jpg").exists()
