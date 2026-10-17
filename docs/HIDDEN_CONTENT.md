# Hidden content

Unlockables, debug features, button codes and unused content, each marked *verified in game* or
*from the code*. No earlier documentation of this game's hidden content was found (2026-10-17).
Addresses are RAM; the research scripts are in build/work/hidden_*/ (not committed).

## Hidden wrestlers: Minoru Suzuki and Antonio Inoki (*from the code*)

Wrestler select normally cycles through 10 wrestlers. The byte at 0x800D88F0 widens it to all 12,
adding Minoru Suzuki (乱取 みのる, wrestler 8) and Antonio Inoki (キラー武蔵, wrestler 11):
- the cursor routine 0x80046A0C wraps at 9 or 11 depending on the byte (also 0x80045BD4), and the
  random picks at 0x8003A9B8 (CPU opponent) and 0x800467F0 draw from 10 or 12;
- only two instructions write it: 0x80041E64 clears it at power-on (in the start-up routine
  0x80041DD8), and 0x8003EE44 sets it in the memory card read before a match (0x8003E7F8).

**How to unlock:** win circuit mode with each of the ten starting wrestlers and save the champion
belt to the memory card each time. The read routine checks the save with 0x80042E28: the first
0x78 bytes are 12 records of 10 bytes, one per wrestler (first byte = wrestler + 1 when a belt is
saved), and it needs records 0-7, 9 and 10 filled - every wrestler except the two bosses. Once a
card like that is read (the memory card step before a match), both bosses are selectable until the
console is reset. *Verified in game* with the `bosses` patch (2026-10-17): both selectable in
exhibition mode, names and portraits right on the pre-match screen; the card unlock itself was not
played through.

Circuit mode is 11 matches (counter 0x800D8903, opponents from the table at 0x800B1150, COM level
1-11 by match from 0x800B11D4). Every route ends with Suzuki and then Inoki, so the bosses are
fought even while locked; Inoki's own route ends with Hogan and Maeda, Suzuki's with Fujiwara and
Inoki. Winning the 11th match runs the belt flow (0x800362B8: name entry, card save of the champion
record via 0x80042A04 at 0x80036B04), then the ending and staff roll. *Probably* champion belts
won from another card in a belt bet count too (0x8003E2F0-0x8003E348 write a transferred belt into
the champion records); not confirmed. The optional `bosses` patch skips all this (PATCHES.md).

## Alternate costumes: hold R1 at wrestler select (*from the code*)

Every wrestler has two costumes (two sets of 3 textures in their FILELINK group). At wrestler
select, holding R1 picks the second costume and holding L1 forces the first (0x800468B8-0x80046A04:
held buttons at 0x800BC1B0/B2, costume flags 0x800D88F3/F4, passed to the wrestler loader 0x800157AC
at 0x80043284/0x800432B4). With neither held, the second player gets the other costume when both
pick the same wrestler. *That the flag selects the texture set is from the group layout; not yet
seen in game.*

## Attract mode (*from the code*)

After 600 frames (10 s) without input on the title menu, the game alternates between a CPU demo
match (state 3, 0x8003A8A0) and the opening movie (state 4). Main state table: 0x80010D1C (5
entries: circuit, exhibition, belt history, demo, movie); every state is reachable.

## Cut setting: 2-COUNT MATCH (*from the code*)

The RULES option offers two values (row maxima at 0x800B12A8: 3, 2, 10, 2, 2, 3, 2, 4), shown by
`rules·32 + 0x10` (0x8003A334-0x8003A390): 3-COUNT MATCH (slot 13) and SUBMISSION ONLY (slot 15).
The configuration screen still draws slot 14, 2-COUNT MATCH, into VRAM at the row between them, but
no value shows it. Whether the match code still handles a third rule value is not known (the
settings reach it through the match object at match+0xDFC, 0x80015B18).

## COM level (*from the code*)

The menu's COM LEVEL 1-4 is stored as 0, 4, 8 or 12 (divided by 4 for display at 0x80039C84,
multiplied back at 0x80039FD0). Circuit mode sets levels 1-11 by match, so exhibition level 4 (12) is
above the circuit's final boss. Values 13-15 fit but nothing sets them; their effect is unknown.
Lumberjack forces ring-out OFF (0x80015B3C).

## Finishers (*from the code*)

The results screen's finish name is `96 + value` from a 44-byte table per wrestler (record pointers
at 0x800B06DC, 28 bytes per wrestler; tables 0x800B0474-0x800B0658), or a fixed value for the
match-ending types (0x3D-0x42: double ring out, time-limit draw, ring out, DQ, KO, referee stop),
written only at 0x80015C40-0x80015D8C. Two of the 71 names are in no table, so no match can end with
them: **SWINGING SLEEPER** (slot 144) and **SMALL PACKAGE HOLD** (slot 163).

Two quirks of the original: every table also holds 0 (HI-ANGLE SUNSET FLIP, slot 96) as filler for
states with no finish, and Takada's and Maeda's tables have no PINFALL (9) where the others do -
their pin wins may show another name. *Not seen in game.*

| Wrestler | Finish values (slot = 96 + value) |
|---|---|
| Jushin Liger | 1-9, 68 |
| The Great Muta | 4, 9-13, 56 |
| Mitsuharu Misawa | 9, 14-23 |
| Stan Hansen | 9, 18, 24-26, 51 |
| Nobuhiko Takada | 26, 36, 40, 41 |
| Big Van Vader | 9, 24, 26, 34, 42-47 |
| Super Delfin | 7, 27-33, 69, 70 |
| Yoshiaki Fujiwara | 5, 9, 34-39 |
| Minoru Suzuki | 9, 15, 16, 34-40, 49 |
| Hulk Hogan | 9, 12, 18, 24-26, 47, 50, 51 |
| Akira Maeda | 4, 34, 36, 39, 52, 53 |
| Antonio Inoki | 9, 12, 34, 40, 42, 54-60 |

## Moves and animations (*from the code and data*)

No orphaned moves or animations were found.
- Each wrestler has 43 move states (the byte at wrestler+0x13D). The 28-byte record at
  0x800B06DC + 28·wrestler holds 7 per-state tables: finish name (p0), flags (p1), first animation of
  each state (p2), per-frame scripts (p3) and parameters (p4-p6).
- A wrestler's moves are animated from his FILELINK group entries +12..+23, one file per opponent
  (0x80024A7C picks it by the opponent's id; every pairing exists, including mirror matches and the
  bosses): u16 count, u16 2, count × {u32 offset, u32 frames}, data. In every file the count equals
  the last state start + 16, so **every animation belongs to a move state: no extra data, no
  gaps**. Counts: Liger 258, Muta 231, Misawa 248, Hansen 194, Takada 202, Vader 230, Delfin 232,
  Fujiwara 218, Suzuki 240, Hogan 218, Maeda 212, Inoki 247.
- Entry +5 is a shared set of 102 general animations per wrestler (same layout with u16 3), played
  by action id (0x800250C0 / 0x80023D78); entries +0..+3 are the models (2·slot + costume), +4 a
  460-byte table; 346+n and 358+n are per-wrestler voice banks (VAB header and samples).
- The animation player (0x80032938) plays from the shared set, the wrestler's own move file or the
  attacker's (a thrown wrestler is animated from the attacker's file).
- Empty move states: some wrestlers have short 4-frame stub animations with no flags in states 8 and
  15-19 - a move class (probably aerial) they don't have: Muta 18; Vader, Hogan, Inoki 8, 18, 19;
  Suzuki 8, 17-19; Hansen, Takada, Fujiwara, Maeda 8, 15-19. Placeholders, not cut moves.
- Curiosity: Liger's move file against Big Van Vader (entry 61) is byte-identical to the one
  against Super Delfin (62), so he handles both the same way.
- Not proven: that every animation inside a state plays (picked at run time) and that all 102
  shared animations are used - 76 of the 108 calls pass one of 46 fixed ids, the rest compute them.
  A debugger watch on wrestler+0x13D and +0xAA during play would settle it.

## Music (*from the code and data*)

14 tracks, all used (table at 0x800897CC: file, parameters, channel and volume). WRS_BGM1.XA
channels 0-7 and WRS_BGM2.XA channels 0-3 are the twelve wrestlers' themes, played in matches by
wrestler id (0x8001E300); BGM2 channel 4 is the menu music (0x80042F7C), channel 5 the circuit
ending and staff roll (0x8004F1EC). Suzuki's (BGM2 ch 0) and Inoki's (BGM2 ch 3) themes are only
heard once they're selectable, or in their circuit matches. BGM2 channel 4 holds 3:16 of music and
about 5 minutes of silence padding. Nothing lies outside the two files' sectors.

## Unused text (*from the code*)

Message slots no screen draws (the screen records at 0x800B191C reach slots 180-245; slots below
that are loaded directly or by index - see TECHNICAL.md):

| Slot | Japanese | Meaning |
|---|---|---|
| 14 | 2カウントマッチ | "2-count match": drawn but never shown (cut RULES value, see above) |
| 35 | 選手権試合 | "Title match" |
| 184-186 | ベルトを賭けて戦い、途中で負けた場合は / コンティニューはできません / この設定は途中で変更はできません | "If you bet a belt and lose partway, you can't continue. This setting can't be changed partway." - a cut warning for betting belts in circuit mode |
| 190 | ベルトを賭けずに戦う場合は | "To fight without betting a belt" (the screen uses another wording) |
| 203, 205 | 書き込みに失敗しました / 読み込みに失敗しました | "Save failed" / "Load failed" (the format and access error screens are used instead) |
| 241 | もう一度初期化をする場合は | "To format again" |

They are translated anyway, in case something reaches them.

## Unused data (*from the code*)

- FILELINK.BIN entries 34-43: a 10-entry wrestler group that no load reaches (the 12 wrestler groups
  start at the u16 table 0x80010048). Every file is a byte copy of one in use: Big Van Vader's
  motions and model (34/35 = 218, 36 = 222, 37 = 223) with Nobuhiko Takada's textures (38-43 =
  200-202, 204) - a development leftover, no new model or animation.
- No orphaned models, animations or textures at the file level: every other entry is loaded, and
  each of the 12 wrestler groups is complete (models, 2 costumes, move files for all 12 opponents).
  Inside the files: see "Moves and animations".
- Portraits 370-403 (all loaded at start-up, loop at 0x80041FA4): 370-399 are the ten starting
  wrestlers, three each (a large portrait per costume and a small icon); 400-403 are the two
  bosses' large portraits, with no small icons - 10 × 3 + 2 × 2 = 34. *Verified in game*
  (2026-10-17, bosses patch): Suzuki shows the dark red-lit head, Inoki the silver one.
- `AAA.BBB` on the disc: 37 MB of filler that nothing loads.
- Unused code: the sound driver's sound-effect name lookups (0x800206BC, 0x800213D0; their data now
  holds English text, see PATCHES.md), four unused variants of a camera routine (0x8001A3D4,
  0x8001A530, 0x8001A68C, 0x8001A7E8), a few unused wrestler-position helpers. None draws text or
  reads the pad: there is no debug menu.

## Not found

- No debug menus, debug flags or button codes: the only multi-button checks are "any of" tests
  (START or ○, → or ○). SYS_INIT / INIT OK! / MAIN LOOP go to the debug serial port only.
- No 13th wrestler: every per-wrestler table has 12 entries.
- Not checked (the user chose to document these without proving them): the AI's handling of COM
  levels 13-15, a third RULES value in the match code, and the PlayStation library code above
  0x80050000.
