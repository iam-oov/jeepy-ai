"""
Repository: ConfigRepository
Gestiona acceso a configuración centralizada.
"""

from pathlib import Path
from typing import Any, Dict, Optional


class ConfigRepository:
    """Repositorio para gestionar configuración."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Path a archivo de configuración (si existe)
        """
        self.config_path = config_path
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene valor de configuración."""
        return self._cache.get(key, default)

    def set(self, key: str, value: Any):
        """Establece valor de configuración."""
        self._cache[key] = value

    def load_from_env(self):
        """Carga configuración desde variables de entorno."""
        import os

        self._cache = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            "STT_ENGINE": os.getenv("STT_ENGINE", "whisper_api"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS"
            ),
            "DEVICE_INDEX": int(os.getenv("DEVICE_INDEX", "0")),
            "SAMPLE_RATE": int(os.getenv("SAMPLE_RATE", "16000")),
            "KWS_MODEL_PATH": os.getenv(
                "KWS_MODEL_PATH", "./models/jeepy_model.tflite"
            ),
            "KWS_THRESHOLD": float(os.getenv("KWS_THRESHOLD", "0.7")),
        }

    def load_from_file(self, filepath: str) -> bool:
        """Carga configuración desde archivo JSON."""
        try:
            import json

            with open(filepath, "r") as f:
                self._cache = json.load(f)
            return True
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Retorna configuración actual como dict."""
        return self._cache.copy()
