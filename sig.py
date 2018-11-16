from scipy.io import wavfile
from scipy.fftpack import rfft, irfft
import matplotlib.pyplot as plt
import numpy as np

def data_info(data):
    print('data_info:')
    print(f' - type: {type(data)}')
    print(f' - shape: {data.shape}')
    print(f' - dtype: {data.dtype}')
    print(f' - min: {np.min(data)}')
    print(f' - max: {np.max(data)}')


sample_rate, channels = wavfile.read('beep2.wav')
print(sample_rate)
window_size = 8192
stride = 512
data_length = channels[:, 0].shape[0]
data = (channels[:, 0] + channels[:, 1]) / 2  # todo: that's going to change

b = data[int(2.585 * sample_rate):int(2.595 * sample_rate)]
print(len(b))
plt.plot(np.abs(np.fft.fftfreq(len(b))), np.fft.fft(b), linewidth=0.3)
plt.show()
exit(0)

print(f'Using window size: {window_size}')
print(f'Sampling rate: {sample_rate}')
print(f'Data length: {data_length} samples, {data_length / sample_rate} s')
print(f'Time resolution: {window_size / sample_rate}')
print(f'Frequency resolution: {sample_rate / window_size}')

fft_data = np.zeros((window_size))

searched_frequency = 900

detected = []


def get_signals(fft):
    q1, q3 = np.percentile(fft, [25, 75])
    iq = q3 - q1
    return fft[(fft > q3 + 3 * iq)]

for i in range(data_length // stride):
    if i * stride + window_size > data_length:
        break
    window = data[i * stride:i * stride + window_size]
    fft = rfft(window)
    
    timestamp = (i * stride + window_size / 2) / sample_rate
    signals = get_signals(fft)

    fft_data += fft

    if np.any(np.isclose(irfft(fft), searched_frequency, atol=5)):
        detected += [timestamp]

fft_data /= data_length // stride

linewidth = 0.3
f, ax = plt.subplots(3)
ax[0].plot(data, linewidth=linewidth)
ax[1].plot(np.abs(fft_data[:len(fft_data) // 2]), 'r', linewidth=linewidth)
ax[2].scatter(detected, [1 for _ in range(len(detected))], s=linewidth * 2)
plt.show()

print(detected)