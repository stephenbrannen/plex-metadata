# plex-metadata

CLI tools for Plex metadata management. Current focus: downloading poster artwork from a Plex library.

## Requirements

- Python 3.12+ (project uses a local virtualenv)
- `uv` for dependency management
- A Plex Media Server you can access

## Setup

```bash
cd /Users/sbrannen/python/plex-metadata
uv venv
uv sync --extra dev
source .venv/bin/activate
```

Pre-commit hooks (optional but recommended):

```bash
pre-commit install
```

## Configuration

Set these environment variables:

```bash
export PLEX_BASE_URL="http://localhost:32400"
export PLEX_TOKEN="YOUR_PLEX_TOKEN"
export PLEX_LIBRARY="Movies"
```

You can also pass these as CLI options (`--base-url`, `--token`, `--library`).

## Install

Editable install (recommended for development):

```bash
pip install -e ".[dev]"
```

## Usage

Download posters:

```bash
plex-metadata posters download --output-dir "plex-posters"
```

Limit downloads:

```bash
plex-metadata posters download --limit 10
```

Dry run (no files written):

```bash
plex-metadata posters download --dry-run
```

## Output behavior

- Files are saved into `--output-dir` (default: `posters`).
- Filenames include the title and year (if available) plus an index to prevent collisions:
  - `Title_1999_0.jpg`
  - `Title_2004_1.jpg`

## Missing posters report

If a poster URL returns a 404, it is skipped and reported at the end:

- Downloaded count
- Number of skipped 404s
- Table of missing titles and URLs

## Development

Run tests:

```bash
pytest
```

Run hooks:

```bash
pre-commit run --all-files
```

Note: activate the venv before committing so the pre-commit hook can find `pyrefly`.
