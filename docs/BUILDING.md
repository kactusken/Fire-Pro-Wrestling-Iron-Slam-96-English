# Building

## Requirements

- Python 3.9+ - `build.py` and `make_patches.py` use only the standard library
- `xdelta3` for release patches (`apt install xdelta3`)
- For the image and research tools: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`

## Setup (once)

1. Put `Fire Pro Wrestling - Iron Slam '96 (Japan).bin` in `rom/` (or pass `--rom`). Expected SHA-1 `2b06e910a32742579cf17280fed22f5533cd5d3a`.
2. `python3 tools/extract.py` - unpacks the disc into `extracted/`, exports every image to
   `review/images-original/`.
3. `python3 build.py` - first build (copies the image; later builds only restore what changed).

## I want to...

| I want to... | Do this |
|---|---|
| Build the translation | `python3 build.py` → `build/Fire Pro Wrestling Iron Slam 96 (English).bin` |
| See how far along it is | `python3 tools/status.py` |
| Check everything | `python3 tools/check.py` (`--control`: prove the build is lossless) |
| Check text only | `python3 tools/lint.py --warnings` |
| Fill repeated strings | `python3 tools/fill_text.py <table>` (tables in `translation/fill/`) |
| Redraw changed image renders | `.venv/bin/python tools/render.py` |
| See every image original vs English | `.venv/bin/python tools/compare.py` → `review/compare/` |
| Find an image | `.venv/bin/python tools/edit.py list <words>` or `review/contact-sheets/` |
| Edit an image by hand | [EDITING.md](EDITING.md) |
| Make release patches | `python3 make_patches.py --version v0.1` |
| Release and announce | [RELEASING.md](RELEASING.md): screenshots, public repository, GitHub release, Reddit, romhacking.net |
| Update the public repository | `python3 tools/publish.py --dry-run`, then `python3 tools/publish.py -m "v0.2" --tag v0.2` |
| Run checks before every commit | `python3 tools/check.py --install-hook` |

## Build options

| Option | |
|---|---|
| `--name NAME` | output name (default `Fire Pro Wrestling Iron Slam 96 (English)`) |
| `--clean` | copy the original instead of restoring the last build |
| `--unlocks all\|none\|GROUP,...` | gameplay patches (`CODE_PATCHES` in build.py) |
| `--no-translation` | skip text and images; alone the result is identical to the original |
| `--boot PART` | test build that starts in PART (`BOOT_PATCHES`) |
| `--no-text FILE` | developer: leave one text file untranslated |
| `--skip-verify` | don't hash the original |

## Folder options

Every tool takes `--root`, `--rom`, `--translation`, `--extracted`, `--build`, `--review` (see
`--help`); the defaults are the folders in [tools/paths.py](../tools/paths.py).
