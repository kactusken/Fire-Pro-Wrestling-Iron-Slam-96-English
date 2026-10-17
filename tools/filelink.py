#!/usr/bin/env python3
"""FILELINK.BIN, the game's archive: read, rebuild, unpack.

  filelink.py list               every entry: index, offset, size, group, type
  filelink.py verify             rebuild the archive from its entries and compare byte for byte

Format (docs/TECHNICAL.md#filelinkbin): u32 count, 12 zero bytes, count x {u32 offset, u32 size,
u32 0, u32 group}, then the entries packed back to back. Offsets count from the end of the table.
`group` counts down the members still to come in a load group (n, ..., 1) and is 0x10000 on the
last one. The game finds the archive by name and reads this table, so entries may change size.

Used by extract.py (extracted/FILELINK/NNN.<type>) and by the build (Archive.put).
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

NAME = '/FILELINK.BIN'
TYPES = {b'\x10\0\0\0': 'tim', b'pBAV': 'vab', b'pQES': 'seq'}


class Archive:
    def __init__(self, data):
        count = struct.unpack_from('<I', data, 0)[0]
        if count == 0 or count > 4096 or data[4:16] != bytes(12):
            raise ValueError('not FILELINK.BIN: bad header')
        base = 0x10 + 16 * count
        self.entries, self.groups = [], []
        end = base
        for i in range(count):
            off, size, zero, group = struct.unpack_from('<4I', data, 0x10 + 16 * i)
            if zero or base + off != end:
                raise ValueError(f'FILELINK.BIN entry {i}: unexpected layout (offset {off:#x}, field 3 {zero:#x})')
            self.entries.append(bytes(data[base + off:base + off + size]))
            self.groups.append(group)
            end = base + off + size
        if end != len(data):
            raise ValueError(f'FILELINK.BIN: {len(data) - end} bytes after the last entry')

    def get(self, i):
        return self.entries[i]

    def put(self, i, data):
        self.entries[i] = bytes(data)

    def build(self):
        count = len(self.entries)
        table, off = bytearray(), 0
        for e, g in zip(self.entries, self.groups):
            table += struct.pack('<4I', off, len(e), 0, g)
            off += len(e)
        return struct.pack('<I', count) + bytes(12) + bytes(table) + b''.join(self.entries)


def kind(entry):
    return TYPES.get(entry[:4], 'bin')


def unpack(data, out):
    """Write every entry to out/NNN.<type>; returns the count."""
    a = Archive(data)
    out.mkdir(parents=True, exist_ok=True)
    for i, e in enumerate(a.entries):
        p = out / f'{i:03d}.{kind(e)}'
        if not (p.exists() and p.stat().st_size == len(e)):
            p.write_bytes(e)
    return len(a.entries)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0], epilog=paths.FOLDER_HELP,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['list', 'verify'])
    args = ap.parse_args(paths.configure(sys.argv[1:] if argv is None else argv))
    src = paths.EXTRACTED / NAME.lstrip('/')
    if not src.exists():
        sys.exit(f'{paths.show(src)} is missing: run tools/extract.py first')
    data = src.read_bytes()
    a = Archive(data)
    if args.command == 'list':
        off = 0
        for i, (e, g) in enumerate(zip(a.entries, a.groups)):
            print(f'{i:3d}  {off:#09x}  {len(e):7d}  {"end" if g == 0x10000 else g:>3}  {kind(e)}')
            off += len(e)
    else:
        if a.build() != data:
            sys.exit('FILELINK.BIN: the rebuilt archive differs from the original - fix tools/filelink.py')
        print(f'FILELINK.BIN: {len(a.entries)} entries, rebuilt byte for byte')


if __name__ == '__main__':
    main()
