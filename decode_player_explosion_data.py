import sys, struct

BYTES_PER_ROW = 32
BYTES_PER_HALF_ROW = 16

def xy_from_raster(raster_offset):
    y, x = divmod(raster_offset, BYTES_PER_ROW)
    if x > BYTES_PER_HALF_ROW:
        x -= BYTES_PER_ROW
        y += 1
    if x < -BYTES_PER_HALF_ROW:
        x += BYTES_PER_ROW
        y -= 1
    return x, y


costume_pxls = [0x11, 0x14, 0x41, 0x44]

for line in sys.stdin:
    hex = line.strip().split()
    int_u8s = [int(h, 16) for h in hex]
    u8s = bytes(int_u8s)
    offset_0, _loc, d_loc, pxls = struct.unpack(">hHbB", u8s)
    offset_0_x, offset_0_y = xy_from_raster(offset_0)
    d_loc_x, d_loc_y = xy_from_raster(d_loc)
    #print(f"({offset_0_x:2}, {offset_0_y:2})    ({d_loc_x:2}, {d_loc_y:2})    {pxls:02x}")
    costume = costume_pxls.index(pxls)
    print(f"    ({(offset_0_x * 14)}, {(offset_0_y * 1.75)}, {(d_loc_x * 14)}, {(d_loc_y * 1.75)}, {costume}),")
