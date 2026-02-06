# AGENTS.md

Project guidelines for Codex and other agents.

## Project overview
- Python CLI project named `plex-metadata`.
- CLI entry point: `plex-metadata` -> `plex_metadata.cli:app`.
- Commands live as top-level packages under `src/` (e.g., `src/posters/`).
- Root-level shared code lives directly under `src/` (e.g., `src/domain.py`, `src/schemas.py`).

## Package layout
- `src/plex_metadata/`: main CLI package (Typer app, command wiring).
- `src/<command>/`: command package (e.g., `src/posters/`).
- `src/<command>/tests/`: tests for that command package.
- `src/<command>/repositories/tests/`: tests for repositories in that command.
- `src/tests/`: tests for root-level/shared code.

## Domain and schemas
- Each command package has:
  - `domain.py` for command-specific domain objects.
  - `schemas.py` for CLI/input schemas owned by that command.
- Repository-specific domain/schema objects must live under the repository package that uses them (e.g., `src/<command>/repositories/schemas.py`). Keep types close to their owners rather than at the command root.
- Root-level equivalents exist only for code shared across commands:
  - `src/domain.py`
  - `src/schemas.py`

## Repositories pattern
- Each command package has a `repositories/` package.
- Repositories encapsulate interactions with external systems (e.g., Plex).
- For posters: `src/posters/repositories/plex_posters.py`.

## Dependencies and tooling
- Dependency management: `uv` with `pyproject.toml`.
- Linting/formatting: `ruff` (check + format).
- Type checking: `pyrefly`.
- Pre-commit hooks for ruff and pyrefly via `pre-commit`.
- Tests: `pytest`.
- Pytest discovery configured in `pyproject.toml`:
  - `testpaths = ["src"]`
  - `python_files = ["test_*.py"]`

## CLI conventions
- Use Typer for CLI commands.
- Prefer env vars for Plex credentials:
  - `PLEX_BASE_URL`, `PLEX_TOKEN`, `PLEX_LIBRARY`.
- Handle request/network errors in the CLI layer (not in repositories).
- Repositories can raise; CLI should present friendly errors and exit non-zero.

## Plex integration
- Use `plexapi` as the client library.
- Access to Plex should be encapsulated in repositories.

## Tests
- Prefer function-based pytest tests.
- Use `unittest.mock` for mocks (avoid custom fake classes unless needed).
- For patched methods on frozen dataclasses, use `patch.object` instead of assignment.
- For CLI commands, use Typer's `CliRunner` and mock external dependencies.
- Use `src/tests/cli_mixin.py` and inherit from `CliCommandMixin` for new command CLI tests.

## Git and signing
- Git commit signing uses 1Password SSH signing.
- SSH agent should point at `~/.1password/agent.sock`.

## Common commands
- Install deps: `uv sync --extra dev`
- Activate venv (needed for pre-commit hooks): `source .venv/bin/activate`
- Run tests: `pytest`
- Run hooks: `pre-commit run --all-files`

## Formatting
- All `*.yaml`/`*.yml` files must start with a document separator (`---`).
