#!/usr/bin/env python3
"""The executable's message strings: codec, dump to translation/text/messages.csv, build step.

  msgtext.py dump        write translation/text/messages.csv (keeps the English already there)
  msgtext.py verify      repacking the original strings gives back the executable byte for byte
  msgtext.py preview     draw every translated string, original above English, with the game's
                         fonts -> review/messages.png (red: wider than the original)
  msgtext.py hooktest    run the game's renderer with the pad hook in the simulator (tools/mipsim.py):
                         test strings, then every English string as the build step writes it,
                         which must fill exactly the original width
  msgtext.py decode HEX  decode u16 codes, e.g. `msgtext.py decode 0206 021e 0600`

Strings (docs/TECHNICAL.md#text): u16 codes ending with 0x0600, drawn by 0x800424DC from three
font TIMs in FILELINK.BIN. code < 0x200: font 406 cell `code` (8 px); 0x200 + 2i: font 407 cell i
(16 px); 0x400 + 2k: font 408 cell k (16 px). The code reaches them only through a table of 246
pointers (EXE 0x800B3644); the strings themselves fill 0x800B1B5C-0x800B3644, 4-byte aligned.
English that doesn't fit there goes into the SPARE areas: the unused sound-effect debug names and
their two pointer tables (docs/TECHNICAL.md#message-table), each checked by SHA-1 first. Identical
strings are stored once. Each string is drawn into a fixed place in VRAM that the game doesn't clear,
so English shorter than the original starts with two codes the hook below adds to the renderer
(docs/PATCHES.md): PAD + n (`0x06nn`) draws n blank 8 px cells over the whole place, then BACK + n
(`0x07nn`) moves back n VRAM units (4 px each) to where the text starts: left, or centred to 4 px.

messages.csv columns: slot (table index), ram (original address), font (`small` = 406, `large` =
407: the font the English is encoded in), align (`left` or `center`; the default follows the
original: centred if it is blank at both ends), width (original width in pixels), japanese,
english, notes. Text tokens: {□} {△} {○} {×} button icons; {XXXX} any other code, in hex; [TEXT] narrow
letters drawn into spare font cells (tools/narrow.py); |N| blank up to pixel N (for strings the
screen shows in pieces, such as a question with its YES and NO).
"""
import argparse
import csv
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import filelink  # noqa: E402
import mips_asm  # noqa: E402
import narrow  # noqa: E402
import paths  # noqa: E402
import tim  # noqa: E402

EXE = '/SLPS_002.77'
EXE_BASE = 0x80010000 - 0x800          # RAM address of file offset 0
TABLE = 0x800B3644                      # 246 string pointers
COUNT = 246
# Unused data the build may overwrite: (start, end, SHA-1 of the original bytes). All three are
# only reachable through 0x800206BC and 0x800213D0, two lookups nothing calls.
SPARE = [(0x800103D8, 0x800108E0, '1f18bdfafe5955b05119e620006e40c9175b5b36'),   # SE_ names
         (0x80089DE8, 0x80089F40, '2e4ccb8f599b8ef8a38e1ff281ef4286f21f11ec'),   # their table (86)
         (0x8008A4E0, 0x8008A668, '499f4a03abac4f773168cb29a043a7c302955b5e')]   # their table (98)
HOOK = SPARE[0][0]                      # the pad hook, then more strings
HOOK_ROOM = 0x80
AREAS = [(0x800B1B5C, 0x800B3644),      # where the strings live
         (HOOK + HOOK_ROOM, SPARE[0][1]), SPARE[1][:2], SPARE[2][:2]]
END = 0x0600
PAD = 0x0600                            # PAD + n: n blank 8 px cells (n = 1-255)
BACK = 0x0700                           # BACK + n: move back n VRAM units of 4 px (n = 1-255)
CSV_NAME = 'messages.csv'
FIELDS = ['slot', 'ram', 'font', 'align', 'width', 'japanese', 'english', 'notes']
ALIGN = ('left', 'center')
SPACE8 = 197                            # font 406's blank cell
DRAW_STRING = 0x800424DC
DRAW_GLYPH = 0x800425CC                 # (font x, font y, VRAM x, VRAM y)
GLYPH_CALL = 0x80042558                 # the renderer's only call to DRAW_GLYPH
GLYPH_CALL_ORIGINAL = 0x0C010973        # jal DRAW_GLYPH
# The renderer calls DRAW_GLYPH with the code in v1 and the VRAM x in s0, then adds 4 to s0 for a
# code >= 0x200. The hook passes glyph codes straight on; for PAD + n it draws n blank cells,
# advancing s0 by 2 each (2 VRAM units = 8 px); for BACK + n it takes n off s0. Both take off the 4
# the renderer adds.
HOOK_ASM = f'''
        slti  t0, v1, {PAD + 1:#x}
        beqz  t0, ours
        nop
        j     DRAW
        nop
ours:   slti  t0, v1, {BACK:#x}
        bnez  t0, pad
        andi  t0, v1, 0xff
        subu  s0, s0, t0
        jr    ra
        addiu s0, s0, -4
pad:    addiu sp, sp, -32
        sw    ra, 28(sp)
        sw    s5, 24(sp)
        sw    s6, 20(sp)
        andi  s5, v1, 0xff
        move  s6, a3
loop:   li    a0, {SPACE8 % 32 * 2}
        li    a1, {SPACE8 // 32 * 16}
        sll   a2, s0, 16
        sra   a2, a2, 16
        move  a3, s6
        jal   DRAW
        addiu s5, s5, -1
        bnez  s5, loop
        addiu s0, s0, 2
        addiu s0, s0, -4
        lw    ra, 28(sp)
        lw    s6, 20(sp)
        lw    s5, 24(sp)
        jr    ra
        addiu sp, sp, 32
'''


def hook_code():
    code, _ = mips_asm.assemble(HOOK_ASM, HOOK, {'DRAW': DRAW_GLYPH})
    if len(code) > HOOK_ROOM:
        raise SystemExit(f'msgtext: the pad hook is {len(code)} bytes, HOOK_ROOM is {HOOK_ROOM}')
    return code


def install_hook(exe):
    """Check the SPARE data is the original, put the pad hook at its start and call it from the
    renderer (checked to hold the original call). `exe` is changed in place."""
    for lo, hi, sha1 in SPARE:
        if hashlib.sha1(exe[Messages.off(lo):Messages.off(hi)]).hexdigest() != sha1:
            raise SystemExit(f'{EXE}: the spare data at {lo:#x} is not the original - wrong image, '
                             'or an earlier step used it')
    lo = Messages.off(HOOK)
    site = Messages.off(GLYPH_CALL)
    if exe[site:site + 4] != struct.pack('<I', GLYPH_CALL_ORIGINAL):
        raise SystemExit(f'{EXE}: unexpected code at {GLYPH_CALL:#x}: {exe[site:site + 4].hex()}')
    code = hook_code()
    exe[lo:lo + len(code)] = code
    exe[site:site + 4] = mips_asm.assemble('jal HOOK', GLYPH_CALL, {'HOOK': HOOK})[0]


_KATA = ('アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'
         'ガギグゲゴザジズゼゾダヂヅデドバビブベボパピプペポァィゥェォャュョッ')
_HIRA = ('あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
         'がぎぐげござじずぜぞだぢづでどばびぶべぼぱぴぷぺぽぁぃぅぇぉゃゅょっ')
_DIGITS = '0123456789'
_UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# Font 406 (8x16, 32 per row). Cells 199-232 are HUD pieces (cursor, tiny letters, arrows):
# only those with a plain meaning are named, the rest decode as {XXXX}.
SMALL = dict(enumerate(_DIGITS + _UPPER + _KATA + _HIRA + 'ー ・'))
SMALL.update({216: '’', 217: '(', 218: ')', 219: '?', 220: '、'})
# Font 407 (16x16, 16 per row); 408 continues the kanji.
LARGE = dict(enumerate(' ' + _UPPER + _DIGITS + _KATA + _HIRA))
LARGE.update(enumerate(['ー', '○', '×', 'vs', '△', '!', '?', '’', ',', '/', '_', '・', '☆', ':', '&', 'Jr',
                        *'一二三四五六七八九十百級冠統記念世界日本月第回優勝新偽'], len(LARGE)))
KANJI = dict(enumerate(
    '対戦形式試合方時間分本数場外勝負無制限選手権破壊大使黒龍真田延久冴刃明乱取氷川光秀梶原丈武蔵統一'
    '第高角度前回転固拷問体鎌屈伸片逆変横抱号脇腱羽絞腹裏腕十字膝錐揉胴締超肉弾足掛卍元祖押込両者切反'
    '則秒最終結果雪崩賭下注意途中設定更口差初期化別用替空必新作待書失敗読了入今上獲得名登録英記同持力'
    '画面違内容見速削除優防衛相択残念引成功決以他要'))
BUTTONS = {0x5F8: '□', 0x5FA: '△', 0x5FC: '○', 0x5FE: '×'}

# English: what each character is encoded as, per font. '-' is the long vowel bar, "'" the apostrophe.
_EN_EXTRA = {'-': 'ー', "'": '’'}


def _reverse(font, base, step):
    out = {}
    for i, ch in font.items():
        out.setdefault(ch, base + step * i)
    return out


ENCODE = {'small': _reverse(SMALL, 0, 1), 'large': _reverse(LARGE, 0x200, 2)}
WIDTH = {'small': 8, 'large': 16}
TOKENS = {f'{{{ch}}}': code for code, ch in BUTTONS.items()}


def decode_code(c):
    if PAD < c < BACK:
        return f'{{PAD {c - PAD}}}'
    if c > BACK:
        return f'{{BACK {c - BACK}}}'
    if c < 0x200:
        ch = SMALL.get(c)
    elif c < 0x400:
        ch = LARGE.get((c - 0x200) // 2) if not c & 1 else None
    elif c in BUTTONS:
        return f'{{{BUTTONS[c]}}}'
    else:
        ch = KANJI.get((c - 0x400) // 2) if not c & 1 else None
    return ch if ch is not None else f'{{{c:04X}}}'


def decode(codes):
    return ''.join(decode_code(c) for c in codes)


def code_width(c):
    if c > BACK:
        return -4 * (c - BACK)
    if c > PAD:
        return 8 * (c - PAD)
    return 8 if c < 0x200 else 16


def encode(text, font, where='', cells=None):
    """u16 codes (without the end code) for English `text` in `font` ('small' or 'large');
    `cells` (narrow.Cells) takes [ ] runs."""
    table, out, i = ENCODE[font], [], 0
    while i < len(text):
        if text[i] == '|':  # |N|: blank cells up to pixel N, so a piece starts where the original's did
            j = text.find('|', i + 1)
            try:
                target = int(text[i + 1:j])
            except ValueError:
                raise SystemExit(f'{where}: a column marker is |N| with N in pixels: {text!r}')
            gap = target - sum(code_width(c) for c in out)
            if gap < 0 or gap % 8:
                raise SystemExit(f'{where}: |{target}| is {"behind the text before it" if gap < 0 else "not a multiple of 8 px away"}: {text!r}')
            if gap:
                out.append(PAD + gap // 8)
            i = j + 1
            continue
        if text[i] == '[':
            j = text.find(']', i)
            if j < 0:
                raise SystemExit(f'{where}: unclosed [ in {text!r}')
            out += (cells or narrow.Cells()).codes(text[i + 1:j], where)
            i = j + 1
            continue
        if text[i] == '{':
            j = text.find('}', i)
            tok = text[i:j + 1]
            if j < 0:
                raise SystemExit(f'{where}: unclosed {{ in {text!r}')
            if tok in TOKENS:
                out.append(TOKENS[tok])
            else:
                try:
                    out.append(int(tok[1:-1], 16))
                except ValueError:
                    raise SystemExit(f'{where}: unknown token {tok} in {text!r} (use {{□}} {{△}} {{○}} {{×}} '
                                     'or a hex code like {00C8})')
            i = j + 1
            continue
        ch = _EN_EXTRA.get(text[i], text[i])
        if ch not in table:
            raise SystemExit(f'{where}: {text[i]!r} has no glyph in the {font} font: {text!r} '
                             f'(see the font tables in tools/msgtext.py)')
        out.append(table[ch])
        i += 1
    return out


class Messages:
    """The pointer table and strings of the executable."""

    def __init__(self, exe):
        self.exe = exe
        self.ptrs = [struct.unpack_from('<I', exe, self.off(TABLE) + 4 * i)[0] for i in range(COUNT)]
        self.codes = []
        for p in self.ptrs:
            if not AREAS[0][0] <= p < AREAS[0][1]:
                raise ValueError(f'slot pointer {p:#x} outside the string area - wrong executable?')
            o, cs = self.off(p), []
            while (c := struct.unpack_from('<H', exe, o)[0]) != END:
                cs.append(c)
                o += 2
            self.codes.append(cs)

    @staticmethod
    def off(ram):
        return ram - EXE_BASE

    def write(self, strings, shared=()):
        """Pack `strings` (lists of codes, one per slot) into AREAS and repoint the table; returns
        the bytes left free. Slots in `shared` reuse an identical string already placed (the
        original has duplicates of its own, kept apart so an untouched repack is byte-identical)."""
        blobs = [struct.pack(f'<{len(cs) + 1}H', *cs, END) for cs in strings]
        areas = [bytearray() for _ in AREAS]
        placed, ptrs = {}, []
        for i, b in enumerate(blobs):
            if i in shared and b in placed:
                ptrs.append(placed[b])
                continue
            for n, (lo, hi) in enumerate(AREAS):
                if len(areas[n]) + len(b) <= hi - lo:
                    ptrs.append(lo + len(areas[n]))
                    placed.setdefault(b, ptrs[-1])
                    areas[n] += b + bytes(-len(b) % 4)
                    break
            else:
                room = sum(hi - lo for lo, hi in AREAS)
                raise SystemExit(f'messages: the strings need more than the {room} bytes there are '
                                 f'(no room left for slot {i}) - shorten the English, or find more '
                                 'room (docs/TECHNICAL.md#text)')
        free = 0
        for n, ((lo, hi), a) in enumerate(zip(AREAS, areas)):
            free += hi - lo - len(a)
            if n == 0 or a:  # extra areas stay untouched until something goes there
                self.exe[self.off(lo):self.off(hi)] = a + bytes(hi - lo - len(a))
        struct.pack_into(f'<{COUNT}I', self.exe, self.off(TABLE), *ptrs)
        return free


def english_codes(row, original, where, cells):
    """(codes, width) of a row's English; if narrower than the original, the codes first blank the
    whole place in VRAM and then step back to where the text starts."""
    new = encode(row['english'], row['font'], where, cells)
    width, limit = sum(code_width(c) for c in new), int(row['width'])
    align = row.get('align') or ('center' if centred(original) else 'left')
    if align not in ALIGN:
        raise SystemExit(f'{where}: align must be left or center, not {align!r}')
    if width < limit:
        left = (limit - width) // 2 // 4 * 4 if align == 'center' else 0
        new = [PAD + limit // 8, BACK + (limit - left) // 4] + new
    return new, width


def centred(codes):
    """The original is centred in its place (blank on both ends): the English is centred too."""
    blank = (0x200, SPACE8)
    return len(codes) > 2 and codes[0] in blank and codes[-1] in blank


def font_of(codes):
    small = sum(1 for c in codes if c < 0x200)
    return 'small' if small * 2 > len(codes) else 'large'


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def dump(exe, path):
    m = Messages(exe)
    old = {r['slot']: r for r in read_csv(path)} if path.exists() else {}
    rows = []
    for i, (p, cs) in enumerate(zip(m.ptrs, m.codes)):
        prev = old.get(str(i), {})
        rows.append({'slot': str(i), 'ram': f'0x{p:08X}', 'font': prev.get('font') or font_of(cs),
                     'align': prev.get('align') or ('center' if centred(cs) else 'left'),
                     'width': str(sum(code_width(c) for c in cs)), 'japanese': decode(cs),
                     'english': prev.get('english', ''), 'notes': prev.get('notes', '')})
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, FIELDS, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def step(path, files):
    """Build step: put the English of messages.csv into the executable."""
    exe = files.get(EXE)
    m = Messages(exe)
    rows = read_csv(path)
    if len(rows) != COUNT:
        raise SystemExit(f'{paths.show(path)}: {len(rows)} rows, expected {COUNT} - run tools/msgtext.py dump')
    strings, wide, shared = [], [], set()
    cells = narrow.Cells()
    for i, (r, cs) in enumerate(zip(rows, m.codes)):
        en = r['english']
        if not en:
            strings.append(cs)
            continue
        if r['font'] not in ENCODE:
            raise SystemExit(f'{paths.show(path)} slot {r["slot"]}: font must be small or large, not {r["font"]!r}')
        new, width = english_codes(r, cs, f'{paths.show(path)} slot {r["slot"]}', cells)
        if width > int(r['width']):
            wide.append(f'{r["slot"]} ({width}/{r["width"]} px)')
        strings.append(new)
        shared.add(i)
    n = len(shared)
    if wide:
        raise SystemExit(f'{paths.show(path)}: wider than the original (each string has a fixed place in '
                         f'VRAM): slots {", ".join(wide)} - shorten them or use the small font')
    if n:
        install_hook(exe)  # checks the SE_ names before any string goes there
    free = m.write(strings, shared)
    if n:
        files.put(EXE, exe)
    used = cells.count()
    if any(used.values()):
        arch = filelink.Archive(files.get(filelink.NAME))
        cells.write(arch)
        files.put(filelink.NAME, arch.build())
    print(f'messages: {n} strings in English, {free} bytes free'
          + (f'; narrow letters in ' + ', '.join(f'{v} cells of font {k}' for k, v in used.items() if v)
             if any(used.values()) else ''))


FONT_ENTRIES = (406, 407, 408)  # FILELINK.BIN entries of the three fonts


def preview(exe, rows, out):
    """Draw the original and English of every translated row; returns how many are too wide."""
    m = Messages(exe)
    cells = narrow.Cells()
    pairs = [(m.codes[int(r['slot'])], english_codes(r, m.codes[int(r['slot'])], f'slot {r["slot"]}', cells)[0], r)
             for r in rows if r['english']]
    arch = filelink.Archive((paths.EXTRACTED / filelink.NAME.lstrip('/')).read_bytes())
    cells.write(arch)
    fonts = [tim.Tim(arch.get(i)).rgba() for i in FONT_ENTRIES]

    def glyph(c):
        font = fonts[min(c >> 9, 2)]
        if c < 0x200:
            x, y, w = (c % 32) * 8, (c // 32) * 16, 8
        else:
            i = ((c & 0x1FF) >> 1)
            x, y, w = (i % 16) * 16, (i // 16) * 16, 16
        return [row[x:x + w] for row in font[y:y + 16]]

    width = max([sum(code_width(c) for c in cs) for p in pairs for cs in p[:2]] + [64]) + 4
    bg, over = (24, 24, 48, 255), (120, 0, 0, 255)
    canvas, too_wide = [], 0
    for orig, new, r in pairs:
        limit = int(r['width'])
        wide = sum(code_width(c) for c in new) > limit
        too_wide += wide
        for cs in (orig, new):
            band = [[bg] * width for _ in range(16)]
            x = 2
            for c in cs:
                if c > BACK:
                    x += code_width(c)
                    continue
                for g in [SPACE8] * (c - PAD) if c > PAD else [c]:
                    for y, row in enumerate(glyph(g)):
                        for dx, px in enumerate(row):
                            if px[3]:
                                band[y][x + dx] = px
                            elif x + dx >= limit + 2:
                                band[y][x + dx] = over
                    x += code_width(g)
            canvas += band
        canvas += [[(60, 60, 90, 255)] * width] * 2
    out.parent.mkdir(parents=True, exist_ok=True)
    if canvas:
        tim.write_png_rgba(out, canvas)
    return len(pairs), too_wide


def simulate(exe, string):
    """DRAW_GLYPH calls as (font x, font y, VRAM x, VRAM y) when `exe`'s renderer draws the codes at
    RAM `string` (or a list of codes) at VRAM (100, 50)."""
    import mipsim
    cpu = mipsim.CPU()
    cpu.load(0x80010000, bytes(exe[0x800:]))
    if not isinstance(string, int):
        codes, string = string, 0x801F0000
        for i, c in enumerate(codes + [END]):
            cpu.w16(string + 2 * i, c)
    ret, done = 0x80000100, 0x8005100C
    cpu.r[29], cpu.r[31] = 0x801FFF00, ret
    cpu.r[4], cpu.r[5], cpu.r[6] = string, 100, 50
    cpu.stops = {ret, DRAW_GLYPH, done}
    calls, pc = [], DRAW_STRING
    while True:
        pc = cpu.run(pc)
        if pc == DRAW_GLYPH:
            calls.append(tuple(cpu.r[i] & 0xFFFFFFFF for i in (4, 5, 6, 7)))
            pc = cpu.r[31]  # return; the real DRAW_GLYPH keeps the s registers
        elif pc == done:
            pc = cpu.r[31]
        else:
            break
    if cpu.r[29] != 0x801FFF00:
        raise SystemExit('msgtext: the renderer left the stack unbalanced in the simulator')
    return calls


def drawn_span(calls, x0):
    """(start, end) in pixels from x0 of everything drawn (VRAM x is in 16-bit units = 4 px)."""
    start = min(c[2] for c in calls)
    end = max(c[2] * 4 + (8 if c[1] < 0x100 else 16) for c in calls)
    return (start - x0) * 4, end - x0 * 4


def hooktest(exe, csv_path):
    """Failures of the pad hook: on test strings, and on every English string the build step writes."""
    patched = bytearray(exe)
    install_hook(patched)
    tests = [  # (codes, expected DRAW_GLYPH calls as (font x, font y, VRAM x))
        ([0x202, 10], [(4, 256, 100), (20, 0, 104)]),                              # A (large), A (small)
        ([10, PAD + 3, 0x202], [(20, 0, 100), (10, 96, 102), (10, 96, 104), (10, 96, 106), (4, 256, 108)]),
        ([PAD + 1], [(10, 96, 100)]),
        ([0x402, PAD + 2], [(4, 512, 100), (10, 96, 104), (10, 96, 106)]),       # 戦 + 16 px of pad
        ([PAD + 2, BACK + 3, 10], [(10, 96, 100), (10, 96, 102), (20, 0, 101)]),   # blank 16 px, A 4 px in
        ([PAD + 1, BACK + 2, 0x202], [(10, 96, 100), (4, 256, 100)]),              # back to the start
    ]
    failures = []
    for codes, want in tests:
        calls = simulate(patched, codes)
        if [c[:3] for c in calls] != want or any(c[3] != 50 for c in calls):
            failures.append(f'{[hex(c) for c in codes]}: drew {calls}, expected {want} at y 50')

    class Files:
        def __init__(self):
            self.data = {EXE: bytearray(exe)}

        def get(self, name):
            if name not in self.data:
                self.data[name] = bytearray((paths.EXTRACTED / name.lstrip('/')).read_bytes())
            return self.data[name]

        def put(self, name, data):
            self.data[name] = bytearray(data)
    files = Files()
    step(csv_path, files)
    built = files.get(EXE)
    rows = [r for r in read_csv(csv_path) if r['english']]
    for r in rows:
        ptr = struct.unpack_from('<I', built, Messages.off(TABLE) + 4 * int(r['slot']))[0]
        span = drawn_span(simulate(built, ptr), 100)
        if span != (0, int(r['width'])):
            failures.append(f'slot {r["slot"]}: drawn over {span[0]}-{span[1]} px in the build, '
                            f'original 0-{r["width"]} px')
    return failures, len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['dump', 'verify', 'preview', 'hooktest', 'decode'])
    ap.add_argument('codes', nargs='*')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    if args.command == 'decode':
        print(decode([int(c, 16) for c in args.codes]))
        return
    src = paths.EXTRACTED / EXE.lstrip('/')
    if not src.exists():
        sys.exit(f'{paths.show(src)} is missing: run tools/extract.py first')
    exe = bytearray(src.read_bytes())
    if args.command == 'verify':
        m = Messages(exe)
        m.write(m.codes)
        if exe != src.read_bytes():
            sys.exit('messages: repacking the original strings changed the executable - fix tools/msgtext.py')
        print(f'messages: {COUNT} strings repacked byte for byte')
        return
    if args.command == 'hooktest':
        failures, n = hooktest(exe, paths.TEXT / CSV_NAME)
        for x in failures:
            print(x)
        if failures:
            sys.exit('messages: the pad hook failed in the simulator')
        print(f'messages: pad hook ({len(hook_code())} bytes) and {n} English strings draw as expected '
              'in the simulator')
        return
    if args.command == 'preview':
        out = paths.REVIEW / 'messages.png'
        n, wide = preview(exe, read_csv(paths.TEXT / CSV_NAME), out)
        print(f'{n} strings -> {paths.show(out)}' + (f' ({wide} wider than the original)' if wide else ''))
        return
    out = paths.TEXT / CSV_NAME
    n = dump(exe, out)
    print(f'{n} strings -> {paths.show(out)}')


if __name__ == '__main__':
    main()
