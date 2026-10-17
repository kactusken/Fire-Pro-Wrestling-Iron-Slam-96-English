# Tools

Everything is Python 3 and runs from the project folder or anywhere else; every tool has `--help`
(or prints its usage). Folder locations come from [paths.py](paths.py) and can be moved with the
folder options. `build.py`, `make_patches.py` and everything they import use only the standard
library; the tools marked *Pillow* or *capstone* need `.venv` (`pip install -r requirements.txt`).

Set up from the translation kit (version fb308a7-dirty). Tools marked *game* are stubs to fill in.

## Used by the build

| Tool | What it does |
|---|---|
| [../build.py](../build.py) | builds the translated image (text steps, code patches, images, write-back) |
| [paths.py](paths.py) | every folder location and the folder options |
| [image.py](image.py) | the output image: fresh copy or fast restore from a journal; checksums |
| [disc.py](disc.py) | reads and writes files in the disc image (PS1) |
| [codepatch.py](codepatch.py) | applies code patch tables, checking the original bytes first |
| [catalog.py](catalog.py) | the image catalogue: which file the build uses, fingerprints, stale renders |
| [gfx.py](gfx.py) | *game*: exports the original images, imports the English ones |
| [pngio.py](pngio.py) | PNG reading and indexed PNG writing without dependencies |
| [blocks.py](blocks.py), [textdb.py](textdb.py) | message block files; every translatable string as one list |
| [msgtext.py](msgtext.py) | the executable's message strings: font codec, `dump` to translation/text/messages.csv, build step |
| [narrow.py](narrow.py) | narrow letters: `[TEXT]` runs drawn into spare font cells (translation/fonts/narrow.txt) |
| [filelink.py](filelink.py) | FILELINK.BIN, the game's archive: read, rebuild (`verify` proves the round trip), unpack |
| [tim.py](tim.py) | PS1 TIM images: reading and PNG export |
| [mips_asm.py](mips_asm.py) | a small MIPS assembler for hooks (mind the delay slots) |

## Checking

| Tool | What it does |
|---|---|
| [check.py](check.py) | runs every check (`--quick` for the pre-commit hook, `--control` for a lossless-build proof) |
| [lint.py](lint.py) | text: leftover source text, control codes, line/char/byte limits, glossary |
| [status.py](status.py) | how far along the text and images are |
| [records.py](records.py) | fixed-record text tables (names, items, menus of records): `dump` the CSV, `verify` the layout, `measure` unknown data, build step - configure `TABLES` |
| [stepcheck.py](stepcheck.py) | run one build text step against `extracted/` (no image, nothing written) and list what it changed - for testing a step while the image is busy |

## Translating

| Tool | What it does |
|---|---|
| [fill_text.py](fill_text.py) | fills repeated strings from a source → English table |
| [render.py](render.py) | *Pillow*: automatic English renders, only redrawing what changed |
| [edit.py](edit.py) | *Pillow*: hand-edit workflow - start, check, approve, reset, sheets |
| [compare.py](compare.py) | *Pillow*: original \| English sheets |
| [contact.py](contact.py) | *Pillow*: every original image on labelled sheets |

## Releasing

Steps and rules: [../docs/RELEASING.md](../docs/RELEASING.md).

| Tool | What it does |
|---|---|
| [../make_patches.py](../make_patches.py) | builds every variant, makes and re-verifies the xdelta patches, README.txt and the zip |
| [publish.py](publish.py) | copies the committed project into the public repository (no history); stops on changes made there |
| [announce.py](announce.py) | drafts the GitHub release notes, Reddit post and romhacking.net submissions with the facts filled in |
| [shots.py](shots.py) | *Pillow*: scales screenshots to the sizes screenshot sites accept, with readable names |

## Research

| Tool | What it does |
|---|---|
| [extract.py](extract.py) | unpacks the disc into `extracted/` and exports the images (*game*: `unpack()`) |
| [sjisscan.py](sjisscan.py) | finds Shift-JIS text in binary files |
| [mipsdis.py](mipsdis.py) | *capstone*: disassembler with reference and call search |
| [mipsim.py](mipsim.py) | a small R3000 interpreter for offline hook tests (delay slots honoured) |
| [bss_scan.py](bss_scan.py) | estimates how far past its end a code module's memory use reaches |
| [gdbrsp.py](gdbrsp.py) | minimal GDB remote client for DuckStation: RAM, registers, run to an address |
