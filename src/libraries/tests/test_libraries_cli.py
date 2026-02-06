from unittest.mock import MagicMock

from typer import Typer

from plex_metadata.cli import app
from tests.cli_mixin import CliCommandMixin


class TestLibrariesCli(CliCommandMixin):
    @property
    def app(self) -> Typer:
        return app

    @property
    def command_name(self) -> str:
        return "libraries"

    def test_list_libraries(self) -> None:
        with self.setup_mocks(repository_attr="PlexLibrariesRepository") as repository:
            repository.list_libraries.return_value = [
                MagicMock(title="Movies", type="movie"),
                MagicMock(title="TV Shows", type="show"),
            ]
            result = self.invoke(self.default_args())

        assert result.exit_code == 0
        assert "Movies (movie)" in result.output
        assert "TV Shows (show)" in result.output

    def default_args(self) -> list[str]:
        return [
            self.command_name,
            "list",
            "--base-url",
            "http://localhost:32400",
            "--token",
            "token",
        ]
