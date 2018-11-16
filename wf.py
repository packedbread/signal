import wave as w
import numpy as np
import os


def converter(fn1, fn2):
    command = 'ffmpeg -i "%s" "%s"' % (fn1, fn2)
    os.system(command)

def mono_to_stereo(signal):
    sig = signal.copy()
    n = sig.shape[0]
    sig = sig[:,np.newaxis].repeat(2, axis=0).copy()
    sig.resize((n, 2))
    sig = sig.swapaxes(0, 1).copy()
    sig.resize((2, n))
    return sig

def normalize(data, sep=False):
    signal = np.array(data, dtype=float)
    signal = (signal.T - signal.mean(axis=-1)).T
    if sep:
        signal = (signal.T / signal.max(axis=-1)).T
    else:
        signal *= 32668 / np.abs(signal).max()
    signal += 32768
    return np.array(signal, dtype=data.dtype)

def read(fn, mono=False):
    if fn[fn.rfind('.'):] != '.wav':
        tfn = fn[:fn.rfind('.')] + '(temp).wav'
        converter(fn, tfn)
    else:
        tfn = fn

    f = w.open(tfn)
    nch = f.getnchannels()
    sw = f.getsampwidth()
    fr = f.getframerate()
    n = f.getnframes()

    frames = np.array(list(f.readframes(n)), dtype=int)
    frames.resize((n, nch, sw))
    frames *= 256 ** np.arange(sw)
    stereo = (frames.sum(axis=2) + (256 ** sw // 2)) % (256 ** sw) - (256 ** sw // 2)

    f.close()
    if tfn != fn:
        os.remove(tfn)

    if mono:
        return stereo.T.mean(axis=0), fr
    return stereo.T, fr

def write(fn, data, fr, sw=2, convert=False, norm=True):
    if norm:
        data = normalize(data)

    if len(data.shape) == 1:
        data = mono_to_stereo(data)
    
    if data.dtype != np.int64:
        data = np.array(data, dtype=int, copy=True)
    
    nch, n = data.shape
    data.resize((nch, n, 1))
    data = data.repeat(sw, axis=2)
    data = (data - 256 ** sw // 2) % (256 ** sw)
    data //= 256 ** np.arange(sw)
    data %= 256
    frames = data.swapaxes(0, 1)
    frames = frames.copy()
    frames.resize(n * nch * sw)

    if convert:
        tfn = fn[:fn.rfind('.')] + '(temp).wav'
    else:
        tfn = fn[:fn.rfind('.')] + '.wav'
    
    f = w.open(tfn, 'w')
    f.setnchannels(nch)
    f.setsampwidth(sw)
    f.setframerate(fr)
    f.writeframes(bytes(list(np.array(frames, dtype=int))))
    f.close()

    if convert or not fn.endswith('.wav'):
        converter(tfn, fn)
        os.remove(tfn)
