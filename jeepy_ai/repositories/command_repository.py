"""
Repository: CommandRepository
Gestiona almacenamiento de comandos grabados y sus resultados.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class CommandRepository:
    """Repositorio para gestionar comandos grabados y resultados."""

    def __init__(
        self,
        transcriptions_path: str = "./transcriptions/",
        results_path: str = "./interpretations/",
    ):
        self.transcriptions_path = transcriptions_path
        self.results_path = results_path

        Path(self.transcriptions_path).mkdir(parents=True, exist_ok=True)
        Path(self.results_path).mkdir(parents=True, exist_ok=True)

    def save_transcription(
        self,
        audio_file: str,
        transcription: str,
        duration: float,
        stt_engine: str = "unknown",
    ) -> str:
        """
        Guarda transcripción de comando.

        Args:
            audio_file: Path al archivo de audio
            transcription: Texto transcrito
            duration: Duración del audio
            stt_engine: Motor STT utilizado

        Returns:
            Path al archivo de transcripción
        """
        filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.transcriptions_path, filename)

        data = {
            "timestamp": datetime.now().isoformat(),
            "audio_file": audio_file,
            "transcription": transcription,
            "duration_seconds": duration,
            "stt_engine": stt_engine,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def save_gemini_result(
        self,
        transcription: str,
        interpretation: Dict[str, Any],
        execution_result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Guarda resultado de procesamiento con Gemini.

        Args:
            transcription: Texto original
            interpretation: Interpretación de Gemini
            execution_result: Resultado de ejecución de acción

        Returns:
            Path al archivo de resultado
        """
        filename = f"interpretation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.results_path, filename)

        data = {
            "timestamp": datetime.now().isoformat(),
            "transcription": transcription,
            "interpretation": interpretation,
            "execution_result": execution_result,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def get_command_history(self, limit: int = 10) -> list:
        """
        Obtiene historial de comandos procesados.

        Args:
            limit: Número máximo de comandos

        Returns:
            Lista de transcripciones ordenadas por fecha
        """
        try:
            files = sorted(Path(self.transcriptions_path).glob("*.json"), reverse=True)[
                :limit
            ]
            history = []

            for f in files:
                with open(f, "r") as file:
                    history.append(json.load(file))

            return history
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []
