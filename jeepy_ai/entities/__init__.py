"""
Entities - Modelos de dominio puros sin dependencias de negocio
"""

from .audio_chunk import AudioChunk
from .system_state import SystemState, SystemStateConstants
from .error_recovery import ErrorRecoveryManager
from .command import CommandRecord

__all__ = [
    "AudioChunk",
    "SystemState",
    "SystemStateConstants",
    "ErrorRecoveryManager",
    "CommandRecord",
]
