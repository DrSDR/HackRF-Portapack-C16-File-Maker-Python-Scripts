#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  9 13:54:50 2026

@author: drsdr
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, lfilter

def create_am_hackrf_filtered(wav_path, sample_rate=250000):
    # 1. Read and Prepare Audio
    fs_orig, data = wavfile.read(wav_path)
    if len(data.shape) > 1:
        data = data[:, 0]  # Mono conversion
    data = data.astype(np.float32) / (np.max(np.abs(data)) + 1e-9)

    # 2. Audio Bandpass Filter (100Hz to 6kHz)
    def bandpass_filter(signal, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return lfilter(b, a, signal)

    # Filter audio at its original sample rate
    filtered_audio = bandpass_filter(data, 100.0, 6000.0, fs_orig)

    # 3. Upsample to 250kHz
    upsampled = resample_poly(filtered_audio, sample_rate, fs_orig)
    
    # 4. AM Modulation (m=1.2 / 120% overmodulation)
    m = 1.2
    am_envelope = 1.0 + m * upsampled
    
    # 5. Frequency Offset Logic
    # Target = 1700kHz, Center = 1760kHz -> Offset = -60kHz
    center_freq_hz = 1760000
    target_freq_hz = 1700000
    offset_hz = target_freq_hz - center_freq_hz 
    
    t = np.arange(len(am_envelope)) / sample_rate
    complex_carrier = np.exp(1j * 2 * np.pi * offset_hz * t)
    
    # Combine envelope and carrier
    iq_signal = am_envelope * complex_carrier
    
    # 6. Save as 16-bit Signed IQ (int16)
    max_amp = np.max(np.abs(iq_signal))
    i_data = (iq_signal.real / max_amp * 32767).astype(np.int16)
    q_data = (iq_signal.imag / max_amp * 32767).astype(np.int16)
    
    # Interleave I and Q
    iq_interleaved = np.empty((i_data.size * 2,), dtype=np.int16)
    iq_interleaved[0::2] = i_data
    iq_interleaved[1::2] = q_data
    
    bin_filename = "am_1700_filtered_int16.C16"
    iq_interleaved.tofile(bin_filename)
    
    # 7. Create Metadata File
    txt_filename = "am_1700_filtered_int16.txt"
    with open(txt_filename, 'w') as f:
        f.write(f"sample_rate={sample_rate}\n")
        f.write(f"center_frequency={center_freq_hz}\n")
    
    print(f"Success! Files saved: {bin_filename}, {txt_filename}")
    print(f"Filter: 100Hz - 6kHz | Format: int16")

# Run
create_am_hackrf_filtered('z.wav')
