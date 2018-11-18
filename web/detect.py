from tempfile import NamedTemporaryFile
from skimage import util as skutil
from scipy.io import wavfile
from bisect import bisect
import subprocess as sp
import numpy as np
import shutil
import ffmpy
import json
import sys
import os

# SETTINGS
WINSIZE = 1024
WINSTEP = 100
FREQUENCY = 900
SMOOTHWINDOW = 10
THRESHOLD = 0.4

# READ
inpfile = NamedTemporaryFile(delete=False)
shutil.copyfileobj(sys.stdin.buffer, inpfile)
inpfile.close()

# CONVERT
outfile = NamedTemporaryFile()
outfile.close()
ffmpeg = ffmpy.FFmpeg(
    inputs={inpfile.name: None},
    outputs={outfile.name: '-f wav'}
)
ffmpeg.run(
    stdout=sp.DEVNULL,
    stderr=sp.DEVNULL
)

# LOAD
rate, signal = wavfile.read(outfile.name)
if signal.ndim > 1: signal = np.mean(signal, axis=1)
signal = signal / np.max(signal)
length = len(signal)
duration = length / rate

# SLICE
windows = skutil.view_as_windows(signal, window_shape=WINSIZE, step=WINSTEP)
windows = windows * np.hanning(WINSIZE)
windows = windows.T

# ANALYZE
spectrum = np.abs(np.fft.fft(windows, axis=0))[:WINSIZE // 2]
freqs = np.fft.fftfreq(WINSIZE)[:WINSIZE // 2] * rate
index = bisect(freqs, FREQUENCY)
volume = spectrum[index, :]
volume = volume / np.max(spectrum)

# EXTRACT BEEPS
filtered = volume > THRESHOLD
rshifted = np.roll(filtered, 1)
starts = (filtered & ~rshifted).nonzero()
ends = (~filtered & rshifted).nonzero()
beeps = np.dstack([starts, ends])
beeps = np.multiply(beeps, WINSTEP / rate * 1000)
beeps = np.round(beeps).astype(int)[0].tolist()

# CLEANUP & RETURN
os.remove(inpfile.name)
os.remove(outfile.name)
print(json.dumps(beeps))
