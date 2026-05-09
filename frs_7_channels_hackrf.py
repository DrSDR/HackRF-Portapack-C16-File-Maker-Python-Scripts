#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  9 14:21:56 2026

@author: drsdr
"""

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, lfilter

def create_frs_nbfm_filtered_c16(wav_path, sample_rate=250000):
    # FRS Channels 1-7 (462.5625 to 462.7125 MHz)
    frs_freqs = [
        462.5625e6, 462.5875e6, 462.6125e6, 462.6375e6,
        462.6625e6, 462.6875e6, 462.7125e6
    ]
    hackrf_center = 462.6375e6 # Center on FRS Channel 4

    # 1. Load Audio and Convert Stereo to Mono
    fs_orig, data = wavfile.read(wav_path)
    if len(data.shape) > 1:
        data = np.mean(data, axis=1) # Average L+R
    
    data = data.astype(np.float32) / (np.max(np.abs(data)) + 1e-9)

    # 2. Bandpass Filter (200Hz to 3400Hz)
    def voice_filter(signal, fs, low=200, high=3400):
        nyq = 0.5 * fs
        b, a = butter(5, [low/nyq, high/nyq], btype='band')
        return lfilter(b, a, signal)

    filtered_audio = voice_filter(data, fs_orig)

    # 3. Upsample to 250kHz
    upsampled_audio = resample_poly(filtered_audio, sample_rate, fs_orig)

    # 4. Generate NBFM Baseband (2.5 kHz deviation)
    deviation = 3200 
    audio_int = np.cumsum(upsampled_audio) / sample_rate
    nbfm_baseband = np.exp(1j * 2 * np.pi * deviation * audio_int)

    # 5. Multi-channel Mixing
    t = np.arange(len(nbfm_baseband)) / sample_rate
    composite_iq = np.zeros(len(nbfm_baseband), dtype=np.complex64)

    for freq in frs_freqs:
        offset = freq - hackrf_center
        composite_iq += nbfm_baseband * np.exp(1j * 2 * np.pi * offset * t)

    # 6. Convert to 16-bit Signed IQ (int16)
    max_val = np.max(np.abs(composite_iq))
    i_data = (composite_iq.real / max_val * 32767).astype(np.int16)
    q_data = (composite_iq.imag / max_val * 32767).astype(np.int16)

    # Interleave I and Q
    iq_interleaved = np.empty((i_data.size * 2,), dtype=np.int16)
    iq_interleaved[0::2] = i_data
    iq_interleaved[1::2] = q_data

    # 7. Save .C16 and .txt
    base_name = "frs_voice_band_c16"
    iq_interleaved.tofile(f"{base_name}.C16")

    with open(f"{base_name}.txt", "w") as f:
        f.write(f"sample_rate={sample_rate}\n")
        f.write(f"center_frequency={int(hackrf_center)}\n")

    print(f"Created {base_name}.C16 and {base_name}.txt")
    print(f"Filter: 200Hz-3.4kHz | Channels: FRS 1-7 | Center: 462.6375 MHz")

# Run
create_frs_nbfm_filtered_c16('y.wav')
