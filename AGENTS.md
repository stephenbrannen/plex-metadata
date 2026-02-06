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
- `src/tests/`: tests for root-level/shared code.

## Domain and schemas
- Each command package has:
  - `domain.py` for domain objects.
  - `schemas.py` for input/request schemas (Pydantic).
- Root-level equivalents:
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

## Git and signing
- Git commit signing uses 1Password SSH signing.
- SSH agent should point at `~/.1password/agent.sock`.

## Common commands
- Install deps: `uv sync --extra dev`
- Run tests: `uv run pytest`
- Run hooks: `uv run pre-commit run --all-files`
