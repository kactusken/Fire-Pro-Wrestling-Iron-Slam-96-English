# Translation

## Where the text is

| File | Holds | Checked by |
|---|---|---|
| `translation/script/*.txt` | *(story/dialogue)* | `tools/lint.py` |
| `translation/text/messages.csv` | the executable's 246 strings: menus, match settings, wrestler names, finishers, results, belt and memory card messages | `tools/lint.py`, the build (fit), `tools/msgtext.py preview` |
| `translation/graphics.csv` | images with text | `tools/check.py` |

## File formats

Message blocks: `@ id`, source lines (`JP `), translation lines (`EN `); no `EN` lines = original
kept. A file's header says what it holds and its limits (`# limit lines=3 chars=28` is checked by
lint). Tables: original columns beside English ones (`japanese`/`english`, or `X`/`en_X`). See
`tools/blocks.py` and `tools/textdb.py`.

messages.csv: `font` is the font the English is written in: `small` (8 px glyphs, font 406) or
`large` (16 px, font 407). `width` is the original's width in pixels, and **the English must not
be wider** (each string has a fixed place in video memory). The build fills the rest with blank
cells. `align` is `left` or `center` (to 4 px); its default follows the original (centred if it
is blank at both ends). All wrestler names are centred.
`msgtext.py preview` draws both as the game will.

**Narrow letters**: `[TEXT]` in the English is drawn with 3 px letters (translation/fonts/narrow.txt,
our own design in the game's style) into spare font cells, about 4 px per letter instead of 8. Use
them only where normal letters don't fit: the cells are limited (85 of 16 px, 21 of 8 px; the build
reports how many are used). `tools/narrow.py show TEXT` prints a run and its width.

**Column markers**: `|N|` fills with blank cells up to pixel N. Use it where one string holds
several pieces (a question and its YES and NO, button legends): keep each piece at the column where
the Japanese piece started (`msgtext.py decode` / the dump shows the original's layout), since the
screen may show the pieces as separate sprites.

Control codes: `{□}` `{△}` `{○}` `{×}` button icons; `{XXXX}` any other glyph by its hex code
(for example `{03E0}` = a blank 16 px cell the game draws numbers over, `{00C8}`... = tiny HUD letters).

Characters available in English: `A-Z 0-9 space` in both fonts; `- ' ・ ( ) ? 、` in small;
`- ' ! ? , / _ ・ : & ○ × △ ☆` in large. **There is no full stop yet**: a dot glyph can go into an
empty cell (407 cells 241-247 are blank) when it's needed.

## Style guide

- Name order, romanization: *(decide)*
- Quotes, ellipses, speaker labels, continuation-line indent: *(decide)*
- Voice and register per character type: *(decide)*
- Case: UPPERCASE (only glyphs the fonts have)
- Line and box limits: each string's original pixel width (`width` column): small font = width/8
  letters, large = width/16
- Moves: established English wrestling names (セントーン... → common Western terms). Moves named
  after a character use the real wrestler's own name for it (カイザーボム → LIGER BOMB, ドルフィン
  クラッチ → DELFIN CLUTCH). Shorten (REV, SUPER FRANKENSTEINER) rather than use narrow letters:
  those cells are kept for names.
- Belts: 統一ベルト = UNIFIED (belt list), チャンピオンベルト = CHAMPION; 防衛 = defend/RETAINS;
  賭ける = BET. Players are 1P / 2P as in the game's own English.
- Memory card: CARD, SLOT 1/2, FORMAT (初期化), SAVE/LOAD FAILED, PRESS ○ TO ...
- Falls: 1本勝負 = 1 FALL, 3本勝負 = 2 OF 3 (best two out of three falls); 無制限 = UNTIMED

## Glossary

`translation/glossary.csv` (`japanese, english, notes`): lint warns when a source line contains a
term and the English doesn't use its translation (several accepted forms: `A | B`). Prefer
established community names (existing English guides) over new coinages.

## Decisions

| Decision | Who / why |
|---|---|
| Scope: all text (menus, messages, moves, wrestler names and profiles, memory card title, image text such as the title screen and HUD) | user, 2026-10-17 |
| Uppercase only to start, using the game's own A-Z glyphs; move to lowercase or a VWF only if the text doesn't fit or read well | user, 2026-10-17 |
| Wrestler names: use the real wrestlers each character parodies, not romanized parody names (mapping in the glossary) | user, 2026-10-17 |
| Name order: given name first (MINORU SUZUKI); short names are surnames | proposed, 2026-10-17 |
| Wrestler names are all centred (the originals mixed centred and full-width names) | user, 2026-10-17 |
| Names that don't fit use narrow letters (`[ ]`); all short names are narrow so the two shown side by side match | user chose narrow letters, 2026-10-17 |

## Coverage (audit of 2026-10-17)

Every file on the disc was checked for text: the executable and all 441 FILELINK.BIN entries were
scanned for the game's encoding and for Shift-JIS, all 162 images were looked at, and the code
that reads the save title was traced. Details: TECHNICAL.md.

| Where | What | State |
|---|---|---|
| Executable, message table (246 strings) | every menu, prompt, result, belt and memory card message, names, moves | **done** except slot 70; 15 originals already English or kept by choice are marked `[keep]` |
| Message slot 70 | name-entry tabs L1 英数 カタカナ ひらがな その他 終了 R1 | **done**: ABC KATA HIRA MISC DONE, each at its original column |
| Belt-name keyboard | how players type belt names | nothing to translate: the tabs are ranges of the font, and ABC already gives A-Z, 0-9 and space (TECHNICAL.md) |
| Memory card save title | ファイヤープロレスリング　アイアンスラム’９６　ベルトデータ, Shift-JIS, 3 copies, shown by the BIOS | kept: the user doesn't want the save data touched (2026-10-17) |
| Save file name | `BISLPS-00277FP96BELT` | keep: it's how the game finds its saves |
| Memory card icon | 16x16 picture next to the title | kept: no memory card changes (user, 2026-10-17) |
| Executable, anything else | | no other text |
| Images (162 TIMs) | fonts, logos, HUD, belt icons, credits, wrestler textures | no visible Japanese: logos, mode menu, credits and HUD are already English; the katakana labels under the body textures (ヨコ, ウシロ, ウチ, マエ) are artists' notes off the models |
| FILELINK data (265 entries) | models, animations, sound banks | no text, no code |
| Movies (11 STR) | opening, one entrance per wrestler | kept: out of scope (user, 2026-10-17) |
| Music, voices (XA, VAB) | | kept (scope) |
| `AAA.BBB` | | filler: nothing names it, never loaded |

*Verified in game* (user, 2026-10-17): circuit mode, the belt-bet flow and outcomes, belt-name
entry, Belt History and belt select, memory card screens.

## Wrestlers

| Character | Real wrestler | Full name (15 letters) | Short (5) |
|---|---|---|---|
| レッドカイザー Red Kaiser | Jushin Thunder Liger | JUSHIN LIGER | [LIGER] |
| 黒龍 Kokuryu | The Great Muta | THE GREAT MUTA | [MUTA] |
| 氷川 光秀 Mitsuhide Hikawa | Mitsuharu Misawa | [MITSUHARU MISAWA] | [MISAWA] |
| スター・バイソン Star Bison | Stan Hansen | STAN HANSEN | [HANSEN] |
| 真田 延久 Nobuhisa Sanada | Nobuhiko Takada | NOBUHIKO TAKADA | [TAKADA] |
| ザ・セイバー The Saber | Big Van Vader | BIG VAN VADER | [VADER] |
| ザ・ドルフィン The Dolphin | Super Delfin | SUPER DELFIN | [DELFIN] |
| 梶原 丈 Joh Kajiwara | Yoshiaki Fujiwara | [YOSHIAKI FUJIWARA] | [FUJIWARA] |
| 乱取 みのる Minoru Randori | Minoru Suzuki | MINORU SUZUKI | [SUZUKI] |
| アックス・ドゥガン Axe Duggan | Hulk Hogan | HULK HOGAN | [HOGAN] |
| 冴刃 明 Akira Saeba | Akira Maeda | AKIRA MAEDA | [MAEDA] |
| キラー武蔵 Killer Musashi | Antonio Inoki | ANTONIO INOKI | [INOKI] |

Mapping from the user (2026-10-17); 黒龍 = The Great Muta by elimination (the user's list calls the
character "Blade Musha"). `[ ]` = narrow letters.

## What stays untranslated

- Logos (Iron Slam '96, Fire Pro Wrestling, HWA): stylized art.
- Staff credits and the mode menu (images 431, 435-440): already in English.
- Voices, music (XA) and the opening and entrance movies (STR).
- Strings already in English in the original are marked `[keep]` in messages.csv when they mix both
  fonts or rely on their spacing; the rest carry their own text as English.
- The memory card save title, icon and everything else in the save data (user, 2026-10-17).
- The movies (OPENING.STR and the entrance movies), whatever text they hold (user, 2026-10-17).
- The match time 分/秒 (slots 53, 66): the game draws the digits over these strings at fixed
  places; the user judged 4分38秒 clear enough (2026-10-17).
