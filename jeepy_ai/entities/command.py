"""
Entity: CommandRecord
Representa un comando de audio grabado con sus metadatos.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CommandRecord:
    """Representa un comando grabado con metadatos."""

    audio_file: str
    duration: float
    timestamp: datetime
    transcription: Optional[str] = None
    gemini_result: Optional[dict] = None
    error: Optional[str] = None

    def __repr__(self):
        return (
            f"CommandRecord("
            f"file={self.audio_file}, "
            f"duration={self.duration:.2f}s, "
            f"transcribed={self.transcription is not None}, "
            f"has_result={self.gemini_result is not None})"
        )
