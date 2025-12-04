"""
Repository: AudioRepository
Gestiona almacenamiento y recuperación de archivos de audio.
"""

import os
import numpy as np
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional


class AudioRepository:
    """Repositorio para gestionar archivos de audio."""

    def __init__(self, base_path: str = "./captured_commands/"):
        self.base_path = base_path
        Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def save_wav(
        self,
        audio_data: np.ndarray,
        filename: Optional[str] = None,
        sample_rate: int = 16000,
    ) -> str:
        """
        Guarda audio en formato WAV.

        Args:
            audio_data: Array de audio (float32)
            filename: Nombre del archivo (si es None, genera automático)
            sample_rate: Sample rate en Hz

        Returns:
            Path al archivo guardado
        """
        if filename is None:
            filename = f"cmd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

        filepath = os.path.join(self.base_path, filename)
        audio_int16 = (audio_data * 32767).astype(np.int16)

        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_int16.tobytes())

        return filepath

    def load_wav(self, filepath: str, sample_rate: int = 16000) -> np.ndarray:
        """
        Carga audio desde archivo WAV.

        Args:
            filepath: Path al archivo
            sample_rate: Sample rate esperado

        Returns:
            Array de audio (float32)
        """
        with wave.open(filepath, "rb") as wf:
            n_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()

            audio_bytes = wf.readframes(n_frames)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32767.0

            return audio_float32

    def delete_audio(self, filepath: str) -> bool:
        """Elimina archivo de audio."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error al eliminar {filepath}: {e}")
            return False

    def get_duration(self, filepath: str) -> float:
        """Obtiene duración del audio en segundos."""
        try:
            with wave.open(filepath, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / rate
        except Exception:
            return 0.0
