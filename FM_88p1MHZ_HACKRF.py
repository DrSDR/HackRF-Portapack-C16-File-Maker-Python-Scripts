import numpy as np
import scipy.io.wavfile as wav
from scipy.signal import butter, lfilter
import os

def apply_pre_emphasis(audio, fs, tau=75e-6):
    """Applies a 75us pre-emphasis filter to boost highs for FM."""
    alpha = np.exp(-1.0 / (fs * tau))
    return lfilter([1, -alpha], [1], audio)

def butter_bandpass(lowcut, highcut, fs, order=5):
    """Creates a bandpass filter between 200Hz and 8kHz."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def generate_wbfm_c16(wav_input, output_base, sample_rate_out=500000, deviation=75000):
    if not os.path.exists(wav_input):
        print(f"Error: File '{wav_input}' not found.")
        return

    # 1. Load Audio
    print(f"Loading {wav_input}...")
    fs, data = wav.read(wav_input)
    
    # 2. Convert Stereo to Mono
    if len(data.shape) > 1:
        print("Mixing stereo channels to mono...")
        data = data.mean(axis=1)
    
    # Normalize to float32 [-1.0, 1.0]
    audio = data.astype(np.float32) / (np.max(np.abs(data)) + 1e-9)

    # 3. Apply 75us Pre-emphasis
    print("Applying 75us pre-emphasis...")
    audio = apply_pre_emphasis(audio, fs)

    # 4. Apply 200Hz - 8kHz Bandpass Filter
    print("Filtering audio (200Hz - 8kHz)...")
    b, a = butter_bandpass(200, 8000, fs, order=5)
    audio_filtered = lfilter(b, a, audio)
    
    # Re-normalize to ensure max volume without over-modulating
    audio_filtered /= (np.max(np.abs(audio_filtered)) + 1e-9)

    # 5. Resample to 500kHz IQ Rate
    print("Resampling to 500kHz IQ rate...")
    num_samples_out = int(len(audio_filtered) * sample_rate_out / fs)
    audio_resampled = np.interp(
        np.linspace(0, len(audio_filtered), num_samples_out), 
        np.arange(len(audio_filtered)), 
        audio_filtered
    )

    # 6. Frequency Modulation (FM)
    print("Generating FM Quadrature (I/Q) samples...")
    sensitivity = 2 * np.pi * deviation / sample_rate_out
    phase = np.cumsum(audio_resampled * sensitivity)
    
    # Convert to 16-bit signed integers (C16 format)
    i_int = (np.cos(phase) * 32767).astype(np.int16)
    q_int = (np.sin(phase) * 32767).astype(np.int16)
    
    # Interleave I and Q: [I, Q, I, Q...]
    iq_interleaved = np.empty((2 * num_samples_out,), dtype=np.int16)
    iq_interleaved[0::2] = i_int
    iq_interleaved[1::2] = q_int

    # 7. Write .C16 and .txt files
    c16_file = f"{output_base}.C16"
    txt_file = f"{output_base}.txt"

    with open(c16_file, 'wb') as f:
        f.write(iq_interleaved.tobytes())

    with open(txt_file, 'w') as f:
        # Center Frequency set to 88.1 MHz (88100000 Hz)
        f.write(f"sample_rate={sample_rate_out}\n")
        f.write(f"center_frequency=88100000\n")

    print(f"\nSuccess!")
    print(f"Transfer '{c16_file}' and '{txt_file}' to your Portapack /captured/ folder.")

if __name__ == "__main__":
    # --- UPDATE THESE TWO LINES ---
    INPUT_WAV = "npr.wav"        # Put your filename here
    OUTPUT_NAME = "MoonshineRadio" # The name for the Portapack files
    # ------------------------------

    generate_wbfm_c16(INPUT_WAV, OUTPUT_NAME)
