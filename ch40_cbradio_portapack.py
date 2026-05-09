#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May  9 16:06:33 2026

@author: drsdr
"""

import numpy as np
import wave
import os
from scipy.signal import butter, lfilter

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "y.wav"    
OUTPUT_BASE = "cb_full_40_filtered"
MOD_INDEX = 1.2                
SAMPLE_RATE = 1000000          
PORTAPACK_CENTER = 27100000    # Shifting center to avoid DC spike

# Official 40-Channel CB Frequencies (Hz)
CB_FREQS = [
    26965000, 26975000, 26985000, 27005000, 27015000, 27025000, 27035000, 27055000, 27065000, 27075000,
    27085000, 27105000, 27115000, 27125000, 27135000, 27155000, 27165000, 27175000, 27185000, 27205000,
    27215000, 27225000, 27255000, 27235000, 27245000, 27265000, 27275000, 27285000, 27295000, 27305000,
    27315000, 27325000, 27335000, 27345000, 27355000, 27365000, 27375000, 27385000, 27395000, 27405000
]

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low, high = lowcut / nyq, highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def create_final_c16():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Load Audio
    with wave.open(INPUT_FILE, 'rb') as w:
        audio_fs = w.getframerate()
        audio_raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        if w.getnchannels() > 1:
            audio_raw = audio_raw.reshape(-1, w.getnchannels()).mean(axis=1)
        audio = audio_raw.astype(np.float32) / 32768.0

    # Apply 200Hz - 5kHz Filter
    print(f"Filtering audio: 200Hz to 5kHz...")
    b, a = butter_bandpass(200, 5000, audio_fs)
    audio_filtered = lfilter(b, a, audio)

    # Resample to 1MHz
    t = np.arange(0, len(audio)/audio_fs, 1/SAMPLE_RATE)
    audio_resampled = np.interp(t, np.arange(len(audio))/audio_fs, audio_filtered)
    
    iq = np.zeros(len(t), dtype=np.complex64)

    print(f"Modulating 40 channels with {MOD_INDEX*100}% index...")
    for freq in CB_FREQS:
        offset = freq - PORTAPACK_CENTER
        # AM: (Carrier + Offset) * (1 + Mod * Audio)
        am_mod = (1.0 + MOD_INDEX * audio_resampled) * np.exp(1j * 2 * np.pi * offset * t)
        iq += am_mod

    # Final Prep & Save
    iq /= np.max(np.abs(iq))
    iq_i = (iq.real * 32767).astype(np.int16)
    iq_q = (iq.imag * 32767).astype(np.int16)
    iq_out = np.empty(iq_i.size * 2, dtype=np.int16)
    iq_out[0::2], iq_out[1::2] = iq_i, iq_q

    iq_out.tofile(f"{OUTPUT_BASE}.C16")
    with open(f"{OUTPUT_BASE}.txt", "w") as f:
        f.write(f"sample_rate={SAMPLE_RATE}\ncenter_frequency={PORTAPACK_CENTER}\n")
    
    print(f"Files ready: {OUTPUT_BASE}.C16 and {OUTPUT_BASE}.txt")

if __name__ == '__main__':
    create_final_c16()
