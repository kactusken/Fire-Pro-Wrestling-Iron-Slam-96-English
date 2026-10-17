#!/usr/bin/env python3
"""Narrow letters: `[TEXT]` runs in the English are drawn into spare font cells.

  narrow.py show TEXT      print TEXT as it will be drawn (palette indices), e.g. `narrow.py show MISAWA`

The game's fonts have fixed 8 and 16 px cells. A narrow run is drawn as one strip with the letters
of translation/fonts/narrow.txt (3 px wide mostly, 1 px apart), cut into 16 px cells of font 408
(free cells 167-251) and, for a last half cell, 8 px cells of font 406 (free cells 235-255).
Identical cells are stored once. The cells use the game's own palette indices (the screens recolour
text by swapping the palette): 4 background, 2 outline, 1 upper strokes, b/c/d shading below.

Used by tools/msgtext.py: Cells.codes(text) gives the codes of a run, Cells.write(archive) puts
the cells into the font TIMs in FILELINK.BIN.
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402
import tim  # noqa: E402

FONT_FILE = 'fonts/narrow.txt'
ROW_HEIGHTS = [1, 2, 2, 2, 2, 2, 1]     # 7 design rows -> 12 rows, like the game's letters
TOP = 2                                 # first stroke row in the 16-row cell
SHADE = {8: 0xB, 9: 0xB, 10: 0xC, 11: 0xC, 12: 0xD, 13: 0xD}  # lower rows: shading, else 1
BG, OUTLINE, STROKE = 4, 2, 1
LARGE = (408, 0x400, 16, tuple(range(167, 252)))   # (font entry, code base, cell width, free cells)
SMALL = (406, 0x000, 8, tuple(range(235, 256)))


def load_font(path):
    glyphs, name, rows = {}, None, []

    def done():
        if name is not None:
            if len(rows) != len(ROW_HEIGHTS) or len({len(r) for r in rows}) != 1:
                raise SystemExit(f'{path}: glyph {name!r} needs {len(ROW_HEIGHTS)} rows of equal width')
            glyphs[' ' if name == 'SPACE' else name] = rows
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip() or (name is None and line.startswith('#')):
            continue  # blank lines; comments only in the header (glyph rows start with # too)
        if line.startswith('= '):
            done()
            name, rows = line[2:].strip(), []
        else:
            rows.append([c == '#' for c in line.strip()])
    done()
    return glyphs


def strip(text, glyphs, where=''):
    """16 rows of palette indices: the run drawn as the game draws its letters."""
    width = 1 + sum(len(glyphs[c][0]) + 1 for c in text) if all(c in glyphs for c in text) else None
    if width is None:
        bad = sorted({c for c in text if c not in glyphs})
        raise SystemExit(f'{where}: no narrow letter for {bad} in [{text}] - add it to '
                         f'translation/{FONT_FILE}')
    stroke = [[False] * width for _ in range(16)]
    x = 1
    for c in text:
        g = glyphs[c]
        y = TOP
        for row, h in zip(g, ROW_HEIGHTS):
            for _ in range(h):
                for i, on in enumerate(row):
                    stroke[y][x + i] |= on
                y += 1
        x += len(g[0]) + 1
    out = [[BG] * width for _ in range(16)]
    for y in range(16):
        for x in range(width):
            if stroke[y][x]:
                out[y][x] = SHADE.get(y, STROKE)
            elif any(stroke[yy][xx] for yy in range(max(0, y - 1), min(16, y + 2))
                     for xx in range(max(0, x - 1), min(width, x + 2))):
                out[y][x] = OUTLINE
    return out


class Cells:
    """Narrow runs -> font cells, allocated in the order they're asked for."""

    def __init__(self):
        self.glyphs = load_font(paths.TRANSLATION / FONT_FILE)
        self.used = {LARGE: {}, SMALL: {}}   # font -> {cell pixels: cell index}

    def _cell(self, font, pixels, where):
        cells = self.used[font]
        if pixels not in cells:
            free = font[3]
            if len(cells) == len(free):
                raise SystemExit(f'{where}: no free {font[2]} px font cells left for narrow letters '
                                 f'({len(free)} used) - use fewer or shorter [ ] runs')
            cells[pixels] = free[len(cells)]
        return font[1] + cells[pixels] * (2 if font[2] == 16 else 1)

    def codes(self, text, where=''):
        rows = strip(text, self.glyphs, where)
        slack = -len(rows[0]) % 8
        rows = [[BG] * (slack // 2) + r + [BG] * (slack - slack // 2) for r in rows]  # centred in its cells
        width = len(rows[0])
        out, x = [], 0
        while x < width:
            font = LARGE if width - x >= 16 else SMALL
            w = font[2]
            out.append(self._cell(font, tuple(tuple(r[x:x + w]) for r in rows), where))
            x += w
        return out

    def write(self, archive):
        """Draw the allocated cells into the font TIMs of `archive` (filelink.Archive)."""
        for font, cells in self.used.items():
            if not cells:
                continue
            entry, _, w, _ = font
            data = bytearray(archive.get(entry))
            t = tim.Tim(data)
            base, stride, per = t.size - len(t.pixels_raw), t.vram[2] * 2, 256 // w
            for pixels, cell in cells.items():
                x0, y0 = (cell % per) * w, (cell // per) * 16
                for y, row in enumerate(pixels):
                    for i in range(0, w, 2):
                        data[base + (y0 + y) * stride + (x0 + i) // 2] = row[i] | row[i + 1] << 4
            archive.put(entry, data)

    def count(self):
        return {f'{font[0]}': len(c) for font, c in self.used.items()}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['show'])
    ap.add_argument('text')
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    rows = strip(args.text, load_font(paths.TRANSLATION / FONT_FILE), 'narrow.py')
    for r in rows:
        print(''.join('.' if v == BG else '%x' % v for v in r))
    print(f'{len(rows[0])} px')


if __name__ == '__main__':
    main()
