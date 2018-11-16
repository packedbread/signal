import numpy as np
from math import ceil
import warnings

def nans(*args, **kwargs):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return np.zeros(*args, **kwargs) / np.zeros(*args, **kwargs)

def windows(arr, length, step=None):
    if step is None:
        step = length // 2
    
    t = arr.dtype
    nwl = ceil(length / step) * step
    rep = nwl // step
    nsl = ceil(arr.shape[0] / nwl) * nwl
    padded = np.append(arr, np.zeros((nsl - arr.shape[0], *arr.shape[1:])), axis=0)
    ps = padded.shape
    snale = padded.repeat(rep, axis=0)
    snale.resize((ps[0], rep, *ps[1:]))
    snale = snale.swapaxes(0, 1).copy()
    snale.resize((rep * ps[0], *ps[1:]))
    snale = np.append(snale, np.zeros((step * rep, *ps[1:])), axis=0)
    snale.resize((rep, ps[0] + step, *ps[1:]))
    w = snale[:,:ps[0]].copy()
    w.resize((rep, ps[0] // nwl, nwl, *ps[1:]))
    w = w[:,:,:length].swapaxes(0, 1).copy()
    w.resize(rep * ps[0] // nwl, length, *ps[1:])
    extra = ceil((nsl - arr.shape[0] - (nwl - length)) / step) + rep - 1
    return w if extra == 0 else w[:-extra]

def lookthrough_mean(pieces, step):
    ps = pieces.shape
    pieces2 = np.append(pieces, nans((ps[0], step - ps[1] % step, *ps[2:])), axis=1)
    ps = pieces2.shape
    rep = ceil(ps[1] / step)
    matr = np.append(pieces2, nans((rep - ps[0] % rep, *ps[1:])), axis=0)
    matr.resize((ceil(ps[0] / rep), rep, ps[1], *ps[2:]))
    matr = matr.swapaxes(0, 1).copy()
    matr.resize((rep, ps[1] * ceil(ps[0] / rep), *ps[2:]))
    matr = np.append(matr, nans((rep, rep * step, *ps[2:])), axis=1)
    matr.resize((rep * (ps[1] * ceil(ps[0] / rep) + step * rep), *ps[2:]))
    matr = matr[:-step * rep].copy()
    matr.resize((rep, ps[1] * ceil(ps[0] / rep) + step * (rep - 1), *ps[2:]))
    
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return np.nanmean(matr, axis=0)[:step * (pieces.shape[0] - 1) + pieces.shape[1]].copy()

def lookthrough_sum(pieces, step):
    ps = pieces.shape
    pieces2 = np.append(pieces, nans((ps[0], step - ps[1] % step, *ps[2:])), axis=1)
    ps = pieces2.shape
    rep = ceil(ps[1] / step)
    matr = np.append(pieces2, nans((rep - ps[0] % rep, *ps[1:])), axis=0)
    matr.resize((ceil(ps[0] / rep), rep, ps[1], *ps[2:]))
    matr = matr.swapaxes(0, 1).copy()
    matr.resize((rep, ps[1] * ceil(ps[0] / rep), *ps[2:]))
    matr = np.append(matr, nans((rep, rep * step, *ps[2:])), axis=1)
    matr.resize((rep * (ps[1] * ceil(ps[0] / rep) + step * rep), *ps[2:]))
    matr = matr[:-step * rep].copy()
    matr.resize((rep, ps[1] * ceil(ps[0] / rep) + step * (rep - 1), *ps[2:]))
    
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return np.nansum(matr, axis=0)[:step * (pieces.shape[0] - 1) + pieces.shape[1]].copy()

def triangle_window(length):
    side = np.arange(length)
    tw = np.min([side, length - 1 - side], axis=0)
    return tw / tw.max()

def trap_window(length, scale=1/3):
    side = np.arange(length)
    plain = np.ones(length) * length * scale
    tw = np.min([side, length - 1 - side, plain], axis=0)
    return tw / tw.max()

def repeater(signal, n, scale=1/3):
    sh = signal.shape
    sig = signal.copy()
    sig *= trap_window(sig.shape[0], scale=scale)
    sig.resize((1, *sh))
    sig = sig.repeat(n, axis=0)
    return lookthrough_sum(sig, int(sh[0] * scale))

__all__ = ['windows', 'lookthrough_mean', 'lookthrough_sum',
           'triangle_window', 'trap_window', 'repeater']
