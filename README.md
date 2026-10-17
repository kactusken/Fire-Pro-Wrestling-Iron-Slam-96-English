# Fire Pro Wrestling Iron Slam 96 — English Translation

An English translation patch for **Fire Pro Wrestling Iron Slam 96**, the 1996 PlayStation wrestling
game released only in Japan.

All of the game's text is in English: the menus, match settings, wrestler select and results
screens, circuit mode, the belt bet and belt history screens, belt name entry and the memory card
prompts. That covers 246 messages, among them the names of the 71 finishing moves. The twelve
wrestlers carry the names of the real wrestlers they parody. The game draws its text into video
memory once and never clears it, so English shorter than the Japanese left fragments of the old
text behind. The patch adds a small hook to the game's text routine so English text is padded and
lined up properly. Names too long for the game's font use narrow letters drawn for the patch.

**[See screenshots](docs/SCREENSHOTS.md)** of the patched game.

> **Status: first public beta (v0.1).** Everything is translated. Circuit mode, exhibition matches,
> belt bets, belt history, belt name entry and the memory card screens have been played through.
> Please report problems
> ([how to report](#reporting-problems)). [CHANGELOG.md](CHANGELOG.md) lists what's in each release.

**AI Disclosure**

This project was created with the assistance of AI for reverse-engineering the game's text routines.

## Downloads

Get the latest zip from the [Releases](../../releases) page. It contains 3 patches. Pick one:

| Patch | What you get |
|---|---|
| **Fire Pro Wrestling Iron Slam 96 (English)** | The translation, with the game otherwise unchanged. |
| **Fire Pro Wrestling Iron Slam 96 (English) (Bosses Unlocked)** | The translation, with the two hidden bosses, Minoru Suzuki and Antonio Inoki, selectable from the start. |
| **Fire Pro Wrestling Iron Slam 96 (Japan) (Bosses Unlocked)** | The original Japanese game, with the two bosses selectable from the start. |

Each patch applies to the original disc image on its own. Don't apply one patch on top of another.

## How to patch

You need your own copy of the original Japanese disc. Disc images are not provided here.

- Game: *Fire Pro Wrestling Iron Slam '96* (Japan), serial SLPS-00277.
- The image must match: `Fire Pro Wrestling - Iron Slam '96 (Japan).bin`, 556894800 bytes, CRC32 `ff62bf08`,
  SHA-1 `2b06e910a32742579cf17280fed22f5533cd5d3a`. This is the Redump dump: a single-track .bin with a .cue.

Then:

1. Apply the `.xdelta` patch with an xdelta tool:
   - [Rom Patcher JS](https://www.marcrobledo.com/RomPatcher.js/) runs in your web browser.
   - Delta Patcher is a desktop app for Windows, macOS and Linux.
   - On the command line: `xdelta3 -d -s "Fire Pro Wrestling - Iron Slam '96 (Japan).bin" "patch.xdelta" "patched.bin"`
2. Rename the patched .bin to the name in the patch's `.cue` file from the zip, and keep both
   files in the same folder.
3. Open the `.cue` in your emulator. Tested in DuckStation.

## Notes for players

- **Names.** The characters are parodies of real wrestlers, and the patch uses the real names:
  Jushin Liger, The Great Muta, Mitsuharu Misawa, Stan Hansen, Nobuhiko Takada, Big Van Vader,
  Super Delfin, Yoshiaki Fujiwara, Hulk Hogan and Akira Maeda, plus the bosses Minoru Suzuki and
  Antonio Inoki.
- **What's still in Japanese.** The match time on the results screen (分 = minutes, 秒 = seconds),
  the save's title in the memory card manager, the movies and the voices. The logos, credits and
  mode menu were already in English.
- **Saves.** The patch doesn't change the save data, so saves from the original game work with
  the patched one and the other way round.
- **Bosses.** To unlock Suzuki and Inoki without the unlocked patch, win circuit mode with each of
  the ten starting wrestlers and save each champion belt to the memory card. They then appear at
  wrestler select after the memory card is read before a match.
- **Hidden content.** See [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md).

## Reporting problems

Open an [issue](../../issues) with:

- a screenshot,
- which patch you used,
- where you were: the mode and menu, or roughly what had just happened.

Text that is cut off, overlaps, shows leftover fragments, or still shows Japanese (other than the
match time) is especially helpful.

## For ROM hackers and contributors

Everything needed to rebuild the patches from the original disc is in this repository: the
translated text, the patching code (Python 3, no dependencies for the build) and documentation of
the game's formats.

| Document | What's in it |
|---|---|
| [docs/BUILDING.md](docs/BUILDING.md) | Setting up, building, making patches, and the checking tools |
| [docs/TRANSLATION.md](docs/TRANSLATION.md) | Text file formats, scope, style guide, glossary, and naming decisions |
| [docs/EDITING.md](docs/EDITING.md) | Editing the in-game text graphics |
| [docs/PATCHES.md](docs/PATCHES.md) | How each code patch works |
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | The game's disc layout, archive, fonts, text encoding and message table |
| [docs/PLATFORM.md](docs/PLATFORM.md) | PS1 pitfalls for this kind of work |
| [docs/HIDDEN_CONTENT.md](docs/HIDDEN_CONTENT.md) | Unlockables, debug features, and unused and cut content |
| [tools/README.md](tools/README.md) | Every tool, what it's for and how to run it |

Quick start:

```sh
python3 tools/extract.py                 # unpack the disc in rom/ into extracted/
python3 build.py                         # -> build/Fire Pro Wrestling Iron Slam 96 (English).bin
python3 make_patches.py --version v0.1   # -> release/*.xdelta and a zip (needs xdelta3)
```

This translation was made with the help of an AI assistant (Claude), and checked by playing the
game.
