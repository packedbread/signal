from scipy.io import wavfile
from scipy.fftpack import rfft
import matplotlib.pyplot as plt
import numpy as np

def data_info(data):
    print('data_info:')
    print(f' - type: {type(data)}')
    print(f' - shape: {data.shape}')
    print(f' - dtype: {data.dtype}')
    print(f' - min: {np.min(data)}')
    print(f' - max: {np.max(data)}')


sample_rate, channels = wavfile.read('beep.wav')

window_size = 4096
stride = 1024
data_length = channels[:, 0].shape[0]
data = channels[:, 0] + channels[:, 1]

print(f'Using window size: {window_size}')
print(f'Sampling rate: {sample_rate}')
print(f'Data length: {data_length} samples, {data_length / sample_rate} s')
print(f'Frequency resolution: {sample_rate / window_size}')

fft_data = np.zeros((window_size))

for i in range(data_length // stride):
    if i * stride + window_size > data_length:
        break
    window = data[i * stride:i * stride + window_size]
    fft_data += rfft(window)

fft_data /= data_length // stride

linewidth = 0.3
f, ax = plt.subplots(2)
ax[0].plot(data, linewidth=linewidth)
ax[1].plot(np.abs(fft_data[:len(fft_data) // 2]), 'r', linewidth=linewidth)
plt.show()
