"""Generate plugin/images/icon.png (64x64 teal disc) with the stdlib only."""
import struct, zlib

N = 64
rows = []
for y in range(N):
    row = bytearray([0])
    for x in range(N):
        inside = (x - 31.5) ** 2 + (y - 31.5) ** 2 <= 30 ** 2
        row += bytes((0x1F, 0x9D, 0x8F, 255)) if inside else bytes((0, 0, 0, 0))
    rows.append(bytes(row))

def chunk(t, d):
    c = struct.pack('>I', len(d)) + t + d
    return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)

png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 6, 0, 0, 0)) \
    + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b'')
import os
os.makedirs('plugin/images', exist_ok=True)
open('plugin/images/icon.png', 'wb').write(png)
