from __future__ import annotations

from collections.abc import Buffer
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

from pytest import fixture

from posters.domain import PosterJob
from posters.repositories.plex_posters import PlexPostersRepository


@fixture()
def sample_items() -> tuple[MagicMock, MagicMock]:
    return (
        MagicMock(
            title="Movie One",
            posterUrl="http://example.com/1.jpg",
            ratingKey="1",
            locations=["/media/Movies/Movie One (1999)"],
        ),
        MagicMock(
            title="Movie Two",
            posterUrl="http://example.com/2.jpg",
            ratingKey="2",
            locations=["/media/Movies/Movie Two (2004)"],
        ),
    )


@fixture()
def fake_plex(sample_items: tuple[MagicMock, MagicMock]) -> MagicMock:
    plex = MagicMock()
    section = MagicMock()
    section.all.return_value = sample_items
    section.type = "movie"
    plex.library.section.return_value = section
    return plex


@fixture()
def repository(fake_plex: MagicMock) -> PlexPostersRepository:
    return PlexPostersRepository(plex=fake_plex)


def test_asset_filename_for_movie() -> None:
    asset = MagicMock(kind="movie", season=None, episode=None)
    name = PlexPostersRepository._asset_filename(asset, 3)
    assert name == "poster"


def test_asset_name_strips_extension() -> None:
    asset_name = PlexPostersRepository._normalize_asset_name("Movie One (1999).mkv")
    assert asset_name == "Movie One (1999)"


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
    section.type = "movie"
    plex.library.section.return_value = section
    repo = PlexPostersRepository(plex=plex)

    posters = list(repo.iter_posters("Movies"))

    assert len(posters) == 1
    (poster,) = posters
    assert poster.title == "Movie One"
    assert poster.url == "http://example.com/1.jpg"
    assert poster.asset_name == "Movie One (1999)"


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
    assert (tmp_path / "Movie One (1999)" / "poster.jpg").exists()
    assert (tmp_path / "Movie Two (2004)" / "poster.jpg").exists()


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
    assert (tmp_path / "Movie One (1999)" / "poster.jpg").exists()
    assert not (tmp_path / "Movie Two (2004)" / "poster.jpg").exists()


def test_iter_targets_respects_limit(tmp_path: Path, repository: PlexPostersRepository) -> None:
    job = PosterJob(output_dir=str(tmp_path), library="Movies", base_url="http://x")
    targets = list(repository.iter_targets(job=job, limit=1))

    assert len(targets) == 1
    (target,) = targets
    assert target.name == "poster.jpg"
    assert target.parent.name == "Movie One (1999)"


def test_tv_assets_use_kometa_naming(tmp_path: Path) -> None:
    episode = MagicMock(episodeNumber=2, thumbUrl="http://example.com/e.jpg")
    season = MagicMock(
        seasonNumber=1,
        posterUrl="http://example.com/s.jpg",
        episodes=MagicMock(return_value=[episode]),
    )
    show = MagicMock(
        title="Show Name",
        posterUrl="http://example.com/show.jpg",
        seasons=MagicMock(return_value=[season]),
        locations=["/media/TV/Show Name"],
    )
    plex = MagicMock()
    section = MagicMock()
    section.type = "show"
    section.all.return_value = [show]
    plex.library.section.return_value = section
    repo = PlexPostersRepository(plex=plex)

    job = PosterJob(output_dir=str(tmp_path), library="TV", base_url="http://x")
    targets = list(repo.iter_targets(job=job))

    names = {t.relative_to(tmp_path).as_posix() for t in targets}
    assert "Show Name/poster.jpg" in names
    assert "Show Name/Season01.jpg" in names
    assert "Show Name/S01E02.jpg" in names


def test_tv_skips_missing_episode_numbers(tmp_path: Path) -> None:
    episode = MagicMock(episodeNumber=None, thumbUrl="http://example.com/e.jpg")
    season = MagicMock(
        seasonNumber=1,
        posterUrl="http://example.com/s.jpg",
        episodes=MagicMock(return_value=[episode]),
    )
    show = MagicMock(
        title="Show Name",
        posterUrl="http://example.com/show.jpg",
        seasons=MagicMock(return_value=[season]),
        locations=["/media/TV/Show Name"],
    )
    plex = MagicMock()
    section = MagicMock()
    section.type = "show"
    section.all.return_value = [show]
    plex.library.section.return_value = section
    repo = PlexPostersRepository(plex=plex)

    job = PosterJob(output_dir=str(tmp_path), library="TV", base_url="http://x")
    targets = list(repo.iter_targets(job=job))

    names = {t.relative_to(tmp_path).as_posix() for t in targets}
    assert "Show Name/poster.jpg" in names
    assert "Show Name/Season01.jpg" in names
    assert "Show Name/S01E00.jpg" not in names
