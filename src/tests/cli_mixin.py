"""Shared helpers for Typer CLI tests."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator
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

    def runner(self) -> CliRunner:
        return CliRunner()

    def invoke(
        self,
        args: list[str],
    ):
        return self.runner().invoke(self.app, args)

    def default_args(
        self,
        tmp_path: Path,
    ) -> list[str]:
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
            str(tmp_path),
        ]

    def patch_repository(self):
        return patch(f"{self.command_name}.cli.PlexPostersRepository")

    def patch_server(self):
        return patch(f"{self.command_name}.cli.PlexServer")

    @contextmanager
    def setup_mocks(self, repository_targets: Iterable[Path] | None = None) -> Iterator[MagicMock]:
        with self.patch_server() as plex_server, self.patch_repository() as repository_cls:
            plex_server.return_value = MagicMock()
            repository = repository_cls.return_value
            if repository_targets is not None:
                repository.iter_targets.return_value = list(repository_targets)
            yield repository
