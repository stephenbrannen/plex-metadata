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
If you prefer not to set `PLEX_LIBRARY`, use `--all-libraries`.

## Install

Editable install (recommended for development):

```bash
pip install -e ".[dev]"
```

## Usage

Download posters:

```bash
plex-metadata posters download --library "Movies" --output-dir "plex-posters"
```

Limit downloads:

```bash
plex-metadata posters download --limit 10
```

Dry run (no files written):

```bash
plex-metadata posters download --library "Movies" --dry-run
```

All libraries:

```bash
plex-metadata posters download --all-libraries --output-dir "plex-posters"
```

List libraries:

```bash
plex-metadata libraries list
```

## Output layout (Kometa asset folders)

The tool writes Kometa-compatible asset folders based on the media **folder name** in Plex. It strips file extensions and extra metadata, and prefers `Title (Year)` when present. Output follows the Kometa asset naming guide (`asset_folders: true`):

```
https://kometa.wiki/en/latest/kometa/guides/assets/?h=assets#asset-naming
```

### Movies

```
<output_dir>/<ASSET_NAME>/poster.jpg
```

`ASSET_NAME` is the movie folder name in Plex (e.g., `Movie Name (1999)`).

### TV Shows

```
<output_dir>/<ASSET_NAME>/poster.jpg
<output_dir>/<ASSET_NAME>/Season01.jpg
<output_dir>/<ASSET_NAME>/S01E01.jpg
```

Where:
- `ASSET_NAME` is the show folder name in Plex.
- Seasons use zero-padded numbers (`Season00` for specials).
- Episodes use zero-padded `S##E##`.

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
