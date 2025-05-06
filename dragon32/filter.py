import scipy.fftpack as FFT
from scipy import signal
import numpy as N

def gain_from_freq(fs, peak = 2400.0, low_zero = 600.0, high_zero = 3200.0):
    gains = N.zeros_like(fs)
    rise_p = (N.abs(fs) >= low_zero) * (N.abs(fs) < peak)
    gains[rise_p] = ((fs - low_zero) / (peak - low_zero))[rise_p]
    fall_p = (N.abs(fs) >= peak) * (N.abs(fs) < high_zero)
    gains[fall_p] = ((high_zero - fs) / (high_zero - peak))[fall_p]
    return gains

BLOCK_SZ = 65536

def filter_block(xs, **kwargs):
    if xs.size != BLOCK_SZ:
        raise ValueError('wrong size')
    freqs = FFT.rfftfreq(xs.size, 1.0 / 48000.0)
    Xs = FFT.rfft(xs)
    gs = gain_from_freq(freqs, **kwargs)
    Xs *= gs
    return FFT.irfft(Xs)

def filter(xs, **kwargs):
    padding_needed = BLOCK_SZ - (xs.size % BLOCK_SZ)
    pad1 = padding_needed // 2
    pad2 = padding_needed - pad1
    pad1 += BLOCK_SZ
    pad2 += BLOCK_SZ
    def Z(n): return N.zeros((n,), dtype = xs.dtype)
    ys = N.concatenate((Z(pad1), xs, Z(pad2)))
    blocks0 = [ys[i : i+BLOCK_SZ] for i in range(0, ys.size, BLOCK_SZ)]
    hbs = BLOCK_SZ / 2
    blocks1 = [ys[i : i+BLOCK_SZ] for i in range(hbs, ys.size-BLOCK_SZ, BLOCK_SZ)]
    filt_x_bs0 = [filter_block(b, **kwargs) for b in blocks0]
    filt_x_bs1 = [filter_block(b, **kwargs) for b in blocks1]
    full_filt_xs = N.zeros_like(ys)
    window = signal.bartlett(BLOCK_SZ)
    for i, b in enumerate(filt_x_bs0):
        full_filt_xs[i*BLOCK_SZ : (i+1)*BLOCK_SZ] += b * window
    for i, b in enumerate(filt_x_bs1):
        full_filt_xs[i*BLOCK_SZ + hbs : (i+1)*BLOCK_SZ + hbs] += b * window
    return full_filt_xs[pad1:-pad2]

def positive_zero_crossings(xs):
    pves = (xs > 0.0).astype(N.float32)
    d_pves = N.diff(pves)
    t1s = N.where(d_pves == +1.0)[0] + 1
    t0s = t1s - 1
    x0s = xs[t0s]
    x1s = xs[t1s]
    return t0s + (x0s / (x0s - x1s))

def periods_from_pzcs(xs):
    pzcs = positive_zero_crossings(xs)
    return N.diff(pzcs)
