from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from requests import RequestException
from typer import Typer

from plex_metadata.cli import app
from tests.cli_mixin import CliCommandMixin


class TestPostersCli(CliCommandMixin):
    @property
    def app(self) -> Typer:
        return app

    @property
    def command_name(self) -> str:
        return "posters"

    def test_download_success(self, tmp_path: Path) -> None:
        with self.setup_mocks() as repository:
            repository.download_posters.return_value = MagicMock(
                downloaded=3, skipped_404=0, missing=[]
            )
            result = self.invoke(self.default_args(tmp_path))

        assert result.exit_code == 0
        assert "Downloaded 3 posters to" in result.output
        repository.download_posters.assert_called_once()

    def test_download_reports_missing(self, tmp_path: Path) -> None:
        with self.setup_mocks() as repository:
            repository.download_posters.return_value = MagicMock(
                downloaded=1,
                skipped_404=1,
                missing=[MagicMock(title="Missing Movie", url="http://example.com/missing.jpg")],
            )
            result = self.invoke(self.default_args(tmp_path))

        assert result.exit_code == 0
        assert "Skipped 1 posters (404)" in result.output
        assert "Missing posters:" in result.output
        assert "Missing Movie | http://example.com/missing.jpg" in result.output

    def test_dry_run_lists_targets(self, tmp_path: Path) -> None:
        targets = (tmp_path / "Movie_One_1.jpg", tmp_path / "Movie_Two_2.jpg")

        with self.setup_mocks(repository_targets=targets) as repository:
            result = self.invoke(self.default_args(tmp_path) + ["--dry-run"])

        assert result.exit_code == 0
        assert "Dry run: 2 posters would be downloaded." in result.output
        first, second = targets
        assert f"  - {first}" in result.output
        assert f"  - {second}" in result.output
        repository.download_posters.assert_not_called()

    def test_download_request_error(self, tmp_path: Path) -> None:
        with self.setup_mocks() as repository:
            repository.download_posters.side_effect = RuntimeError("boom")
            result = self.invoke(self.default_args(tmp_path))

        assert result.exit_code == 1
        assert "Configuration error:" in result.output

    def test_download_network_error(self, tmp_path: Path) -> None:
        with self.setup_mocks() as repository:
            repository.download_posters.side_effect = RequestException("network")
            result = self.invoke(self.default_args(tmp_path))

        assert result.exit_code == 1
        assert "Request failed:" in result.output

    def test_requires_library_or_all_libraries(self, tmp_path: Path) -> None:
        args = [
            "posters",
            "download",
            "--base-url",
            "http://localhost:32400",
            "--token",
            "token",
            "--output-dir",
            str(tmp_path),
        ]
        result = self.invoke(args)

        assert result.exit_code == 2
        assert "Provide --library or --all-libraries" in result.output

    def test_all_libraries_downloads_each_section(self, tmp_path: Path) -> None:
        with self.setup_mocks(sections=["Movies", "Shows"]) as repository:
            repository.download_posters.return_value = MagicMock(
                downloaded=1, skipped_404=0, missing=[]
            )
            args = [
                "posters",
                "download",
                "--base-url",
                "http://localhost:32400",
                "--token",
                "token",
                "--all-libraries",
                "--output-dir",
                str(tmp_path),
            ]
            result = self.invoke(args)

        assert result.exit_code == 0
        assert repository.download_posters.call_count == 2

    def test_movie_library_dry_run_uses_library(self, tmp_path: Path) -> None:
        movie_target = tmp_path / "Movie Name (1999)" / "poster.jpg"

        with self.setup_mocks() as repository:
            repository.iter_targets.return_value = [movie_target]
            args = [
                "posters",
                "download",
                "--base-url",
                "http://localhost:32400",
                "--token",
                "token",
                "--library",
                "Movies",
                "--dry-run",
            ]
            result = self.invoke(args)

        assert result.exit_code == 0
        assert f"  - {movie_target}" in result.output
        repository.iter_targets.assert_called_once()

    def test_tv_library_dry_run_uses_library(self, tmp_path: Path) -> None:
        show_target = tmp_path / "Show Name" / "poster.jpg"

        with self.setup_mocks() as repository:
            repository.iter_targets.return_value = [show_target]
            args = [
                "posters",
                "download",
                "--base-url",
                "http://localhost:32400",
                "--token",
                "token",
                "--library",
                "TV",
                "--dry-run",
            ]
            result = self.invoke(args)

        assert result.exit_code == 0
        assert f"  - {show_target}" in result.output
        repository.iter_targets.assert_called_once()
