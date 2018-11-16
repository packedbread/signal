import numpy as np
from numpy import fft
import wf
import windows

fn = './sasaaaaaaaaaaaatb.wav'
data, fr = wf.read(fn, mono=False)

gap = int(0.05 * fr)  # ширина окна
ws = windows.windows(data, gap)  # режем на окна с перекрытием в пол-окна
ws *= np.hamming(gap)  # домножение на окно хэннинга, устраняет краевые эффекты (просто так надо, все так делают)
sp = np.abs(fft.rfft(ws))  # многомерный, делает всё как надо, даже если не моно
freq = np.fft.rfftfreq(ws.shape[1], 1./fr)  # список частот в разложении Фурье
i1 = (freq * (freq <= 900)).argmax()
i2 = (freq * (freq >= 900) + 10000 * (freq < 900)).argmin()
filt = np.sum(sp[:, :, i1:i2+1], axis=0)  # или axis=1, я запутался
