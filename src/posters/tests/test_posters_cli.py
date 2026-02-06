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
        targets = [tmp_path / "Movie_One_1.jpg", tmp_path / "Movie_Two_2.jpg"]

        with self.setup_mocks(repository_targets=targets) as repository:
            result = self.invoke(self.default_args(tmp_path) + ["--dry-run"])

        assert result.exit_code == 0
        assert "Dry run: 2 posters would be downloaded." in result.output
        assert f"  - {targets[0]}" in result.output
        assert f"  - {targets[1]}" in result.output
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
