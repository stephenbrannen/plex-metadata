"""Shared helpers for Typer CLI tests."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer import Typer
from typer.testing import CliRunner


class CliCommandMixin(ABC):
    """Base mixin for CLI command tests."""

    @property
    @abstractmethod
    def app(self) -> Typer:  # pragma: no cover - abstract
        raise NotImplementedError

    @property
    @abstractmethod
    def command_name(self) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    @staticmethod
    def runner() -> CliRunner:
        return CliRunner()

    def invoke(
        self,
        args: list[str],
    ):
        return self.runner().invoke(self.app, args)

    def default_args(self) -> list[str]:
        return [
            self.command_name,
            "download",
            "--base-url",
            "http://localhost:32400",
            "--token",
            "token",
            "--library",
            "Movies",
            "--output-dir",
            "posters",
        ]

    def patch_repository(self, repository_attr: str):
        return patch(f"{self.command_name}.cli.{repository_attr}")

    def patch_server(self):
        return patch(f"{self.command_name}.cli.PlexServer")

    @contextmanager
    def setup_mocks(
        self,
        repository_targets: Iterable[Path] | None = None,
        sections: Iterable[str] | None = None,
        repository_attr: str = "PlexPostersRepository",
    ) -> Iterator[MagicMock]:
        with (
            self.patch_server() as plex_server,
            self.patch_repository(repository_attr) as repository_cls,
        ):
            plex = MagicMock()
            if sections is not None:
                plex.library.sections.return_value = [MagicMock(title=s) for s in sections]
            plex_server.return_value = plex
            repository = repository_cls.return_value
            if repository_targets is not None:
                repository.iter_targets.return_value = list(repository_targets)
            yield repository
