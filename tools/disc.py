#!/usr/bin/env python3
"""PS1 disc image (platform pack ps1): single-track MODE2/2352 BIN files with ISO9660.

  disc.py list    <bin>
  disc.py extract <bin> <outdir> [--xa]     extract data files (XA streams only with --xa, as raw 2352 sectors)
  disc.py inject  <bin> <iso_path> <file>   overwrite a file in place (must fit in its allocated sectors)
  disc.py verify  <bin> [iso_path...]       check EDC/ECC (of the given files, or every sector - slow)

Writing regenerates EDC/ECC for every written sector and updates the directory record (size, and
LBA when a file that outgrew its slot is relocated into free sectors), so the image stays valid
for emulators and real hardware. Files are found by name on most PS1 games, but check that the
game doesn't hard-code LBAs before relocating (XA audio often is addressed by LBA: keep it put).

Interface shared by every platform's disc.py (build.py and extract.py use only this):
  SECTOR                        data bytes per sector
  Disc(path or file, writable)  .files(), .find(path), .read_file(e), .write_file(e, data, relocate),
                                .allocated_sectors(e), .is_empty(e), .extract_file(e, out), .close()
  companion_files(image)        write what an emulator needs next to the image (here: the .cue)
"""
import struct
import sys
from pathlib import Path

RAW = 2352
SECTOR = USER = 2048

# ---------------------------------------------------------------- EDC / ECC

EDC_LUT = []
for i in range(256):
    e = i
    for _ in range(8):
        e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
    EDC_LUT.append(e)

ECC_F = [0] * 256
ECC_B = [0] * 256
for i in range(256):
    j = (i << 1) ^ (0x11D if i & 0x80 else 0)
    ECC_F[i] = j
    ECC_B[i ^ j] = i


def edc(data):
    e = 0
    for b in data:
        e = (e >> 8) ^ EDC_LUT[(e ^ b) & 0xFF]
    return e


def _ecc_block(src, major_count, minor_count, major_mult, minor_inc):
    size = major_count * minor_count
    out = bytearray(major_count * 2)
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            t = src[index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = ECC_F[a]
        a = ECC_B[ECC_F[a] ^ b]
        out[major] = a
        out[major + major_count] = a ^ b
    return out


def fix_sector(sec):
    """Recompute EDC (and ECC for form 1) of a mode 2 sector in place."""
    if sec[0x12] & 0x20:  # form 2
        struct.pack_into('<I', sec, 0x92C, edc(sec[0x10:0x92C]))
        return
    struct.pack_into('<I', sec, 0x818, edc(sec[0x10:0x818]))
    addr = bytes(sec[12:16])
    sec[12:16] = b'\0\0\0\0'  # mode 2 ECC is computed with a zeroed header
    sec[0x81C:0x8C8] = _ecc_block(memoryview(sec)[0xC:], 86, 24, 2, 86)
    sec[0x8C8:0x930] = _ecc_block(memoryview(sec)[0xC:], 52, 43, 86, 88)
    sec[12:16] = addr


# ---------------------------------------------------------------- ISO9660

class Entry:
    def __init__(self, path, lba, size, is_dir, rec_sector, rec_offset):
        self.path, self.lba, self.size, self.is_dir = path, lba, size, is_dir
        self.rec_sector, self.rec_offset = rec_sector, rec_offset  # where the dir record lives

    @property
    def sectors(self):
        return (self.size + USER - 1) // USER


class Disc:
    def __init__(self, path, writable=False):
        self.own = not hasattr(path, 'read')
        self.f = open(path, 'r+b' if writable else 'rb') if self.own else path
        self.f.seek(0, 2)
        self.total_sectors = self.f.tell() // RAW
        self.entries = []
        pvd = self.read_user(16)
        assert pvd[1:6] == b'CD001', 'no ISO9660 PVD'
        root = pvd[156:190]
        self._walk(struct.unpack('<I', root[2:6])[0], struct.unpack('<I', root[10:14])[0], '/')
        self.entries.sort(key=lambda e: e.lba)

    def close(self):
        if self.own:
            self.f.close()

    def read_raw(self, lba):
        self.f.seek(lba * RAW)
        return bytearray(self.f.read(RAW))

    def write_raw(self, lba, sec):
        self.f.seek(lba * RAW)
        self.f.write(sec)

    def read_user(self, lba):
        return bytes(self.read_raw(lba)[24:24 + USER])

    def _walk(self, lba, size, path):
        for s in range((size + USER - 1) // USER):
            data = self.read_user(lba + s)
            i = 0
            while i < USER:
                ln = data[i]
                if ln == 0:
                    break
                r = data[i:i + ln]
                name = r[33:33 + r[32]]
                if name not in (b'\0', b'\1'):
                    e = Entry(path + name.decode('ascii').split(';')[0],
                              struct.unpack('<I', r[2:6])[0], struct.unpack('<I', r[10:14])[0],
                              bool(r[25] & 2), lba + s, i)
                    self.entries.append(e)
                    if e.is_dir:
                        self._walk(e.lba, e.size, e.path + '/')
                i += ln

    def files(self):
        return [e for e in self.entries if not e.is_dir]

    def find(self, path):
        path = '/' + path.lstrip('/')
        for e in self.entries:
            if e.path.upper() == path.upper():
                return e
        raise KeyError(path)

    def is_xa(self, e):
        return bool(self.read_raw(e.lba)[0x12] & 0x20) or e.path.upper().endswith('.XA')

    def allocated_sectors(self, e):
        """Sectors available before the next thing on disc."""
        later = [x.lba for x in self.entries if x.lba > e.lba]
        nxt = min(later) if later else self.total_sectors
        return nxt - e.lba

    def read_file(self, e):
        out = bytearray()
        for s in range(e.sectors):
            out += self.read_user(e.lba + s)
        return bytes(out[:e.size])

    def is_empty(self, e, samples=64):
        """True if the file looks like zero padding (checks up to `samples` spread-out sectors)."""
        step = max(1, e.sectors // samples)
        return e.size > 0 and not any(any(self.read_user(e.lba + s)) for s in range(0, e.sectors, step))

    def extract_file(self, e, out):
        with open(out, 'wb') as f:
            if self.is_xa(e):  # raw sectors: XA audio has no 2048-byte view
                for s in range(e.sectors):
                    f.write(self.read_raw(e.lba + s))
            else:
                f.write(self.read_file(e))

    def find_free(self, need, start=24):
        """First run of `need` empty sectors not used by any file or directory."""
        used = sorted((x.lba, x.lba + max(x.sectors, 1)) for x in self.entries)
        cur = start
        for a, b in used + [(self.total_sectors, self.total_sectors)]:
            while a - cur >= need:
                busy = next((l for l in range(cur, cur + need) if any(self.read_user(l))), None)
                if busy is None:
                    return cur
                cur = busy + 1
            cur = max(cur, b)
        return None

    def write_file(self, e, data, relocate=False):
        need = (len(data) + USER - 1) // USER
        avail = self.allocated_sectors(e)
        if need > avail:
            if not relocate:
                raise ValueError(f'{e.path}: {len(data)} bytes needs {need} sectors, only {avail} available')
            new = self.find_free(need)
            if new is None:
                raise ValueError(f'{e.path}: no free run of {need} sectors on disc')
            print(f'  relocating {e.path}: LBA {e.lba} -> {new} ({need} sectors)')
            old_lba = e.lba
            e.lba = new
            sec = self.read_raw(e.rec_sector)
            o = 24 + e.rec_offset
            struct.pack_into('<I', sec, o + 2, new)
            struct.pack_into('>I', sec, o + 6, new)
            fix_sector(sec)
            self.write_raw(e.rec_sector, sec)
            # new location has no meaningful subheaders yet: borrow the old file's
            for k in range(need):
                src = self.read_raw(old_lba + min(k, max(e.sectors, 1) - 1))
                dst = self.read_raw(new + k)
                dst[16:24] = src[16:24]
                self.write_raw(new + k, dst)
        old_n = max(e.sectors, 1)
        first_sub = self.read_raw(e.lba)[16:24]
        last_sub = self.read_raw(e.lba + old_n - 1)[16:24]
        mid_sub = bytes(first_sub[:2]) + bytes([first_sub[2] & ~0x81]) + bytes(first_sub[3:4])
        mid_sub = mid_sub * 2
        for s in range(need):
            lba = e.lba + s
            sec = self.read_raw(lba)
            chunk = data[s * USER:(s + 1) * USER].ljust(USER, b'\0')
            sec[16:24] = last_sub if s == need - 1 else (first_sub if s == 0 else mid_sub)
            sec[24:24 + USER] = chunk
            fix_sector(sec)
            self.write_raw(lba, sec)
        # update the directory record (size is stored both-endian at offsets 10 and 14)
        sec = self.read_raw(e.rec_sector)
        o = 24 + e.rec_offset
        struct.pack_into('<I', sec, o + 10, len(data))
        struct.pack_into('>I', sec, o + 14, len(data))
        fix_sector(sec)
        self.write_raw(e.rec_sector, sec)
        e.size = len(data)


def companion_files(image):
    """The .cue an emulator loads, next to the image."""
    image = Path(image)
    image.with_suffix('.cue').write_text(f'FILE "{image.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == 'list':
        d = Disc(argv[1])
        for e in d.files():
            print(f'{e.lba:7d} {e.size:10d} {d.allocated_sectors(e):6d}  {"XA " if d.is_xa(e) else "   "}{e.path}')
    elif cmd == 'extract':
        d = Disc(argv[1])
        out = Path(argv[2])
        xa = '--xa' in argv
        for e in d.files():
            p = out / e.path.lstrip('/')
            p.parent.mkdir(parents=True, exist_ok=True)
            if d.is_xa(e):
                if not xa:
                    continue
                with open(p, 'wb') as f:
                    for s in range(e.sectors):
                        f.write(d.read_raw(e.lba + s))
            else:
                p.write_bytes(d.read_file(e))
            print('extracted', e.path)
    elif cmd == 'inject':
        d = Disc(argv[1], writable=True)
        e = d.find(argv[2])
        data = Path(argv[3]).read_bytes()
        d.write_file(e, data)
        print(f'injected {argv[3]} -> {e.path} ({len(data)} bytes)')
    elif cmd == 'verify':
        d = Disc(argv[1])
        bad = 0
        if len(argv) > 2:
            lbas = [lba for p in argv[2:] for e in [d.find(p)] for lba in range(e.lba, e.lba + e.sectors)]
        else:
            lbas = range(d.total_sectors)
        for lba in lbas:
            sec = d.read_raw(lba)
            if sec[15] != 2:
                continue
            ref = bytearray(sec)
            fix_sector(ref)
            if ref != sec:
                bad += 1
                if bad <= 10:
                    print('bad sector', lba)
        print('bad sectors:', bad)
        return 1 if bad else 0
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
