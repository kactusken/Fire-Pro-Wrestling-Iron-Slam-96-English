# Patches

What the build changes besides text and images, one section per patch: what the original code
does, what changed, why it works, the tool that makes it, limits to respect, and whether it was
*verified in game*.

## Translation patches (always on with the translation)

### Pad and back codes for message strings (`tools/msgtext.py`; *verified in game*)
- **Problem** (*verified in game*): each message is drawn into a fixed place in VRAM that the game
  doesn't clear, and shown as a sprite as wide as the original string. Shorter English left the
  rest of the place showing old VRAM contents (coloured noise after the label).
- **Change**: two new codes (`0x0600` stays the end code). `0x06nn` draws *nn* blank 8 px cells
  (font 406 cell 197, palette index 4, which is opaque); `0x07nn` moves the drawing position back *nn*
  VRAM units (4 px each). The renderer `0x800424DC` makes its only call to the glyph routine at
  0x80042558 (`jal 0x800425CC`); that call now goes to a 128-byte hook at 0x800103D8, which passes
  glyph codes straight on and handles the two new codes by adjusting the renderer's x (`s0`). The
  hook sits in the unused `SE_` debug names (docs/TECHNICAL.md#message-table), checked by SHA-1
  before they're reused.
- **The build** starts every English string that is narrower than the original with `0x06nn` (blank
  the whole place) and `0x07nn` (back to the text's start), so it can be left-aligned or centred to
  4 px (the `align` column) and never draws past its place. It stops if a string is wider.
- **Check**: `msgtext.py hooktest` runs the game's own renderer with the hook in `tools/mipsim.py`,
  on test strings and on every English string as built (each must cover exactly its place).
- *Verified in game* (2026-10-17): match settings and wrestler select screens show no leftovers;
  centred names sit in the middle of their bars.

## Optional patches (`--unlocks`)

### Bosses unlocked (`bosses`; *verified in game*, 2026-10-17: Suzuki and Inoki at exhibition select, with their names and portraits)
- **Original**: wrestler select cycles through 10 wrestlers while the byte 0x800D88F0 is 0, and
  through all 12 (adding Minoru Suzuki and Antonio Inoki) when it's 1. The start-up routine
  0x80041DD8 clears it (0x80041E64, `sb zero, -0x7710(at)`); the memory card read before a match sets
  it once the card holds a champion belt for each of the ten starting wrestlers
  (docs/HIDDEN_CONTENT.md).
- **Change**: 0x80041E64 stores `v0` instead (`0xA02088F0` -> `0xA02288F0`); `v0` is 1 from
  0x80041E34, and only `lui at`/`sb` run in between. Nothing else writes the byte, so it stays 1.
- **Side effect**, as with a normal unlock: the two can also come up as random CPU opponents
  (0x8003A9B8, 0x800467F0).
- Release variants: English, English + bosses unlocked, Japanese + bosses unlocked
  (`make_patches.py` VARIANTS).
