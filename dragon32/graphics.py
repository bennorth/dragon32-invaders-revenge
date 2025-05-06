import numpy as N
import matplotlib
import Image

def pxls_from_byte(b):
    return N.array([(b & 0xc0) >> 6,
                    (b & 0x30) >> 4,
                    (b & 0x0c) >> 2,
                    (b & 0x03)],
                   dtype = N.uint8)

cmap = matplotlib.colors.ListedColormap([(0.0, 1.0, 0.0),
                                         (1.0, 1.0, 0.0),
                                         (0.0, 0.0, 1.0),
                                         (1.0, 0.0, 0.0)])

def pxls_from_data(xs):
    return N.concatenate(map(pxls_from_byte, xs))

def Image_from_data_mode_3(xs):
    xs2 = N.array([xs, xs]).T.ravel()

    im = Image.fromstring('P', (256, 192), xs2, 'raw', 'P', 0, 1)
    im.putpalette([  0, 255,   0,
                     255, 255,   0,
                     0,   0, 255,
                     255,   0,   0])
    return im
