"""
Módulo de Utilidades - Jeepy AI
Contiene clases y funciones auxiliares.
"""
import numpy as np
import wave

class SlidingWindowBuffer:
    # ... (código de SlidingWindowBuffer de kws_monitor.py) ...

class CircularAudioBuffer:
    # ... (código de CircularAudioBuffer de kws_monitor.py) ...

class ConfirmationTracker:
    # ... (código de ConfirmationTracker de kws_monitor.py) ...

class FeedbackManager:
    # ... (código de FeedbackManager de kws_monitor.py) ...

def save_wav_file(audio_data, filename, sample_rate=16000):
    """Guarda audio en formato WAV."""
    audio_int16 = (audio_data * 32767).astype(np.int16)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
