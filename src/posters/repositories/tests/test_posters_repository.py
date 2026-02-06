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
        MagicMock(
            title="Movie One", posterUrl="http://example.com/1.jpg", ratingKey="1", year=1999
        ),
        MagicMock(
            title="Movie Two", posterUrl="http://example.com/2.jpg", ratingKey="2", year=2004
        ),
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


def test_safe_filename_includes_year() -> None:
    name = PlexPostersRepository._safe_filename("Movie One", 3, 1999)
    assert name == "Movie_One_1999_3"


def test_iter_posters_yields_only_items_with_urls(
    sample_items: tuple[MagicMock, MagicMock],
) -> None:
    first_item, _ = sample_items
    items = [
        first_item,
        MagicMock(title="Movie Two", posterUrl=None, ratingKey="2"),
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
    assert poster.year == 1999


def test_download_posters_writes_files(tmp_path: Path, repository: PlexPostersRepository) -> None:
    def fake_download(_self: PlexPostersRepository, _url: str, target: Path, _title: str) -> bool:
        target.write_bytes(cast(Buffer, b"fake"))
        return True

    with patch.object(PlexPostersRepository, "_download", autospec=True) as mock_download:
        mock_download.side_effect = fake_download
        job = PosterJob(output_dir=str(tmp_path), library="Movies", base_url="http://x")
        count = repository.download_posters(job=job)

    assert count.downloaded == 2
    assert count.skipped_404 == 0
    assert (tmp_path / "Movie_One_1999_0.jpg").exists()
    assert (tmp_path / "Movie_Two_2004_1.jpg").exists()


def test_download_posters_respects_limit(tmp_path: Path, repository: PlexPostersRepository) -> None:
    def fake_download(_self: PlexPostersRepository, _url: str, target: Path, _title: str) -> bool:
        target.write_bytes(cast(Buffer, b"fake"))
        return True

    with patch.object(PlexPostersRepository, "_download", autospec=True) as mock_download:
        mock_download.side_effect = fake_download
        job = PosterJob(output_dir=str(tmp_path), library="Movies", base_url="http://x")
        count = repository.download_posters(job=job, limit=1)

    assert count.downloaded == 1
    assert count.skipped_404 == 0
    assert (tmp_path / "Movie_One_1999_0.jpg").exists()
    assert not (tmp_path / "Movie_Two_2004_1.jpg").exists()


def test_iter_targets_respects_limit(tmp_path: Path, repository: PlexPostersRepository) -> None:
    job = PosterJob(output_dir=str(tmp_path), library="Movies", base_url="http://x")
    targets = list(repository.iter_targets(job=job, limit=1))

    assert len(targets) == 1
    assert targets[0].name == "Movie_One_1999_0.jpg"
