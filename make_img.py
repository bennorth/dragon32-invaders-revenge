from PIL import Image
import sys

palette = [
    (0, 0, 0, 0),
    (255, 255, 131, 255),
    (27, 22, 107, 255),
    (109, 14, 36, 255)
]

PIXELS_PER_BYTE = 4

def int_from_hex(hex):
    if hex.startswith("$"):
        hex = hex[1:]
    return int(hex, 16)

def pixels_from_byte(b):
    mask_0 = 0xc0
    pixel_idxs = [
        (b & (mask_0 >> (2 * i))) >> (2 * (3 - i))
        for i in range(4)
    ]
    return pixel_idxs

def layout_iter(bytes, chunk_len, layout):
    if layout == "horizontal":
        yield from iter(bytes)
    elif layout == "vertical":
        n_bytes = len(bytes)
        if n_bytes % chunk_len != 0:
            raise ValueError(f"bad layout: {n_bytes=} {chunk_len=}")
        n_chunks = n_bytes // chunk_len
        for offset in range(chunk_len):
            for chunk_idx in range(n_chunks):
                yield bytes[chunk_idx * chunk_len + offset]
    else:
        raise ValueError(f'unknown layout "{layout}"')


def img_from_bytes(bytes, im_wd_bytes, layout, scale, *, green_0=False):
    n_bytes = len(bytes)
    if n_bytes % im_wd_bytes != 0:
        raise ValueError(f"got {n_bytes} bytes but need multiple of {im_wd_bytes}")

    #print(bytes, (im_wd_bytes * PIXELS_PER_BYTE, n_bytes // im_wd_bytes))

    img_height = n_bytes // im_wd_bytes

    if layout == "vertical":
        img_height, im_wd_bytes = im_wd_bytes, img_height

    if green_0:
        eff_palette = list(palette)
        eff_palette[0] = (29, 174, 21, 255)
    else:
        eff_palette = palette

    im = Image.new("RGBA", (2 * scale * im_wd_bytes * PIXELS_PER_BYTE, scale * img_height))
    i_bytes = layout_iter(bytes, img_height, layout)
    for row_idx in range(img_height):
        for colbatch_idx in range(im_wd_bytes):
            b = next(i_bytes)
            pxs = pixels_from_byte(b)
            for pxl_idx, pxl in enumerate(pxs):
                for xdup in range(2 * scale):
                    for ydup in range(scale):
                        im.putpixel(
                            (2 * scale * (colbatch_idx * PIXELS_PER_BYTE + pxl_idx) + xdup,
                             scale * row_idx + ydup),
                            eff_palette[pxl]
                        )
    return im


if __name__ == "__main__":
    layout = "horizontal"
    scale = int(sys.argv[1])

    bytes = []
    im_wd_bytes = None
    for line in open(sys.argv[2], "rt"):
        if line.startswith("# vertical"):
            layout = "vertical"
            continue
        if line.startswith("#"):
            continue
        row_bytes = list(map(int_from_hex, line.strip().split()))
        if im_wd_bytes is None:
            im_wd_bytes = len(row_bytes)
        if len(row_bytes) != im_wd_bytes:
            raise ValueError("inconsistent row lengths")
        bytes.extend(row_bytes)

    im = img_from_bytes(bytes, im_wd_bytes, layout, scale)
    im.save(sys.argv[3])
