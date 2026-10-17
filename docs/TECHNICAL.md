# Technical notes - Fire Pro Wrestling Iron Slam 96

**Conventions:** numbers in hex with `0x`; addresses are RAM addresses unless marked as file
offsets; `u16`/`u32` little-endian unless marked BE. Findings are marked *verified in game* or
*from the code*.

## Contents
- [Image](#image) · [Disc layout](#disc-layout) · [Executable and memory](#executable-and-memory)
- [Archives and compression](#archives-and-compression) · [Text](#text) · [Images](#images)
- [Open questions](#open-questions)

## Image
`Fire Pro Wrestling - Iron Slam '96 (Japan).bin`, 556894800 bytes, SHA-1 `2b06e910a32742579cf17280fed22f5533cd5d3a`.

## Disc layout
| LBA | Size | File | Contents |
|---|---|---|---|
| 23 | 69 | `/SYSTEM.CNF` |  |
| 24 | 784384 | `/SLPS_002.77` |  |
| 407 | 39399205 | `/FILELINK.BIN` |  |
| 19645 | 156991488 | `/WRS_BGM1.XA` |  |
| 96301 | 161595392 | `/WRS_BGM2.XA` |  |
| 175205 | 16852992 | `/OPENING.STR` |  |
| 183434 | 7153664 | `/BISON.STR` |  |
| 186927 | 7176192 | `/DOLPHINE.STR` |  |
| 190431 | 7176192 | `/DUGGAN.STR` |  |
| 193935 | 7176192 | `/HIKAWA.STR` |  |
| 197439 | 7176192 | `/KAISER.STR` |  |
| 200943 | 7176192 | `/KAZIWARA.STR` |  |
| 204447 | 7176192 | `/KOKURYU.STR` |  |
| 207951 | 7176192 | `/SABER.STR` |  |
| 211455 | 7176192 | `/SAEBA.STR` |  |
| 214959 | 7176192 | `/SANADA.STR` |  |
| 218463 | 37193792 | `/AAA.BBB` |  |

Contents: `SLPS_002.77` is the executable (holds the text, see [Text](#text)); `FILELINK.BIN` is
the archive with every image, model and sound bank; `WRS_BGM*.XA` are the music; `*.STR` are the
opening movie and one entrance movie per wrestler; `AAA.BBB` is a repeating pattern that is probably filler
(not confirmed: check whether anything reads it).

## Executable and memory
PS-X EXE, loaded at 0x80010000 (RAM = file offset - 0x800 + 0x80010000), stack 0x801FFFF0.

## Archives and compression

### FILELINK.BIN (*from the data*)
- `u32 count` (441), 12 bytes of zeros, then `count` entries of 16 bytes:
  `u32 offset, u32 size, u32 0, u32 group`. Offsets are relative to the end of the table
  (`0x10 + 16·count` = 0x1BA0). The entries are packed back to back with no alignment.
- `group` counts down the members still to come in a load group: `n, n-1, ... 1, 0x10000` (the
  last member). Group 0 = entries 0-1, ... 38 groups in all; most of the 24-entry groups are one wrestler each
  (textures, model, sound).
- Entry types by magic: 162 TIM (`10 00 00 00`), 13 VAB (`pBAV`), 1 SEQ (`pQES`); the rest are not
  identified yet (models, code?). No compression found so far.
- Images with text: 406/407/408 fonts, 409-425 HUD and belts, 430 PUSH START BUTTON, 431 mode menu
  (already English), 435-440 staff credits (already English), 404/405/428/429 title and logos.

## Text
### Fonts (*from the data*)
Three 4bpp TIMs in FILELINK.BIN, laid out as grids:
- **406**: 8x16 cells, 32 per row: `0-9 A-Z`, katakana, hiragana, a few symbols and UI arrows.
- **407**: 16x16 cells, 16 per row: space, `A-Z`, `0-9`, katakana (plain, then voiced and small),
  hiragana (same order), symbols (`ー ○ × vs △ ！ ？ ’ ， ／ ＿ ・ ☆ ： ＆ Jr`), then kanji.
- **408**: 16x16 kanji, 16 per row (about 200).
Blank cells (palette index 4 only): font 408 cells 167-251 and font 406 cells 235-255. The build
draws narrow letters there (`tools/narrow.py`). Glyph palette indices: 4 background, 2 outline
(around every stroke), 1 upper strokes, b/c/d shading on rows 8-9/10-11/12-13; strokes on rows 2-13.
The screens recolour text by swapping the palette (the selected row turns red), so new glyphs must
use these indices.
Only **uppercase** Latin exists, in both 406 and 407. There is no Shift-JIS text on the disc except the
memory card title (`ファイヤープロレスリング　アイアンスラム’９６　ベルトデータ`, EXE 0x142C,
0x1484, 0x14DC).

### Encoding (*from the code*: renderer 0x800424DC)
Strings are `u16` codes ending with `0x0600`. `0x800424DC(string, x, y)` draws each code with
`0x800425CC` from the font TIM held in VRAM:
| Code | Glyph | Advance |
|---|---|---|
| `0x0000-0x01FF` | font 406 cell `code` (column `code % 32`, row `code / 32`) | 8 px |
| `0x0200 + 2·i` | font 407 cell *i* (`0x0200` space, `0x0202` A, `0x0236` 0, `0x03E0` blank cell) | 16 px |
| `0x0400 + 2·k` | font 408 cell *k* (`0x0402` 戦; `0x05F8/FA/FC/FE` = □ △ ○ × buttons) | 16 px |
| `0x0600` | end | |
Font 406 cells: 0-9, A-Z (10-35), katakana (36-115), hiragana (116-195), 196 ー, 197 space,
198 ・, 199 ▶, 200-215 tiny HUD letters `RETYMAINUCO1235D`, 216 ’, 217-218 ( ), 219 ?, 220 、,
221-232 HUD icons. Cell tables: `tools/msgtext.py`. Odd codes ≥ 0x200 would start half a cell in.

**The strings are drawn into VRAM, not to the screen** (*from the code*; *verified in game*: shorter
English left old VRAM contents showing, fixed by the pad code in docs/PATCHES.md): `x`/`y` are VRAM
coordinates (x in 16-bit units: +2 per 8 px glyph, +4 per 16 px glyph). Screens pre-draw their
strings into fixed places (e.g. 0x80039B74 draws slots 0-9 at x=0x2C0, y=16·slot, and slots 10-33 at
positions from the table at 0x800B1248) and then show them as sprites. So **English must not be
wider than the original string** or it overwrites the next one. The build lists any wider ones.

### Message table (*from the code*)
- 246 pointers at RAM 0x800B3644 (file 0xA3E44). The strings fill 0x800B1B5C-0x800B3644 exactly, each
  4-byte aligned, in slot order. No code builds a string's address directly (scan of every
  `lui`/`addiu` pair); screens load table slots (0x800B3644 + 4·n, 37 places in the code).
- A few original strings are duplicates (e.g. slots 206/210), stored twice.
- Room for longer English (*from the code*): the build also uses three pieces of dead data, each
  checked by SHA-1 before use (`SPARE` in tools/msgtext.py):
  - RAM 0x800103D8-0x800108E0 (1288 bytes), the `SE_PUNCH_2`... sound-effect debug names; the first
    0x80 bytes hold the pad hook (docs/PATCHES.md);
  - 0x80089DE8-0x80089F40 (344 bytes), a table of 86 pointers to those names, read only by
    `0x800206BC`, which nothing calls;
  - 0x8008A4E0-0x8008A668 (392 bytes), a table of 98 pointers to those names, reached only through the
    per-bank table at 0x8008A668, which is read only by `0x800213D0`, which nothing calls.
  (The 12-entry tables at 0x8008A3FC and 0x8008A4B0 just before them are live: indexed by sound
  bank, 0-11.) No `jal`, no pointer and no `lui`/`addiu` pair reaches either function.
  *Verified in game* (2026-10-17) for the SE_ names: slot 236, stored at 0x80010618, showed
  correctly on the memory card access screen. The two tables are not yet confirmed in game.
- Worst case, if every string used its full width in 8 px glyphs: 9696 bytes, against
  6888 + 1288 = 8176 bytes of room.
- Tool: `tools/msgtext.py` (dump, build step, `verify`, `preview`).

### How screens reach the slots (*from the code*)
- Slots 0-9 and 10-33: the configuration screen's loops (0x80039B74, 0x80039BBC); 16-25 also by the
  match-length byte 0x800D88FD.
- 36-47: by wrestler; 96-166: by the finish byte (byte 1 of `*0x800D88C0`); 167-178: base 166 + 1-12.
- 180-245: through 34 screen records listed at 0x800B191C (pointers; each record is a u16 count and
  10-byte entries with the slot - 180 at +0xA), drawn by `0x8003AA48` (181 call sites).
- Unused slots: docs/HIDDEN_CONTENT.md.

### Where names are drawn (*from the code*)
- Full names (slots 36-47): one per row at VRAM x 0x2C0 (0x80045994, 0x80047454...). 120 px each,
  the width of the sprite shown.
- Short names (slots 167-178): the two wrestlers side by side at x 0x2C0 and 0x2CA, y 0x90
  (0x80044B04-0x80044B94), so **40 px (5 small letters) is a hard limit** unless the code is changed.

### Belt-name entry (*from the code*: 0x8003B22C-0x8003BBC0)
There is no keyboard table. Each character of a belt name is a font 407 cell index (drawn as
`0x0200 + 2·i`), held in the state at 0x800E8928. The tabs of slot 70 are index ranges that the
cursor wraps around in: 英数 0-36 (space, A-Z, 0-9), カタカナ 37-116, ひらがな 117-196, その他
197-239 (ー ○ × vs △ ! ? ’ , / _ ・ ☆ : & Jr and the font's kanji). English belt names can be
typed from the first tab as they are; only the tab labels needed translating.

### Memory card save (*from the code*)
At 0x80010C14, 0x80010C6C and 0x80010CC4 (file 0x1414...), three copies of: the save file name
`BISLPS-00277FP96BELT` (20 bytes + padding) and the title (Shift-JIS, 64 bytes,
`ファイヤープロレスリング　アイアンスラム’９６　ベルトデータ`). The titles are passed to `0x8006B388`
with an icon pointer (`*0x800D8060`) and 3 (icon frames) to build the save header (0x80036580,
0x80036AD8 for the first copy): written, never compared, so the title can be translated. The file
name is what the game looks for: keep it.

### Not in the message table
- Coverage audit (2026-10-17, scripts in build/work): no other strings in the game's encoding in the
  executable or in any FILELINK.BIN entry; no Shift-JIS except the save titles; no code in
  FILELINK.BIN (all entries are data: 162 TIM, 13 VAB, 1 SEQ, 265 models/animations/other).
  The tables at 0x800B1B14/2C/44 are per-wrestler VRAM coordinates, not text. There are no
  wrestler profiles.
- `AAA.BBB` (37 MB of a repeating pattern) is named nowhere in the executable: filler.

### FILELINK.BIN loading (*from the code*)
The archive is opened at 0x80041F34; every entry is loaded with `0x80084F34(archive, 0, entry, 1)`
(86 call sites). Wrestler n's group starts at the u16 table 0x80010048 (44, 71, 95, 119, 194, 218,
143, 170, 290, 242, 266, 314): +0-3 models (2·slot + costume; 19 body parts), +4 a 460-byte table,
+5 102 shared animations, +6-11 three textures × two costumes, +12-23 the wrestler's move
animations against each opponent (0x80024A7C). Animation files: u16 count, u16 kind (3 shared, 2
moves), count × {u32 offset, u32 frames}, data (132 bytes per frame in the shared set). Liger
and Delfin also load entries 68-70 and 167-169. 346+n, 358+n: per-wrestler voice banks. Details:
docs/HIDDEN_CONTENT.md "Moves and animations".
Portraits: entries 370-403 (loop at 0x80041FA4); 346+n and 358+n per wrestler.

## Images

## Open questions
- How are slots 75/83/84/94 (a question with はい/いいえ in one string) shown: one sprite or one
  per piece? The English keeps each piece at its original column either way (`|N|`). The sprite
  rectangles are probably the u16 tables from 0x800B3A1C (not decoded yet).
- Confirm with a debugger watchpoint that the SPARE areas are never read or written by the game.
- Wrestler names and profiles: are they in the EXE or in the FILELINK entries?
- FILELINK.BIN: confirm in game that a rebuilt archive with a grown entry loads (the EXE opens it
  by name, `\FILELINK.BIN;1`, and has no copy of its table).
