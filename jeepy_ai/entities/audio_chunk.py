"""
Entity: AudioChunk
Objeto para transportar datos de audio y metadatos entre capas.
"""

import numpy as np


class AudioChunk:
    """Representa un fragmento de audio con metadatos."""

    def __init__(self, data: np.ndarray, timestamp: float, rms: float):
        """
        Args:
            data: Array de audio (numpy float32)
            timestamp: Timestamp de captura (seconds)
            rms: Energía RMS del chunk
        """
        self.data = data
        self.timestamp = timestamp
        self.rms = rms

    def __repr__(self):
        return f"AudioChunk(len={len(self.data)}, rms={self.rms:.4f}, ts={self.timestamp:.2f})"
