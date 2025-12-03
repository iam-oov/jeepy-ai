"""
Jeepy AI - Módulo de Speech-to-Text
Soporta múltiples motores: Whisper local, OpenAI Whisper API, Google Cloud, Vosk
"""

import os
from pathlib import Path
from typing import Optional
import wave
import numpy as np

from config import Config


class STTEngine:
    """Clase base para motores STT"""

    def transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe un archivo de audio a texto"""
        raise NotImplementedError


class WhisperLocalSTT(STTEngine):
    """Motor STT usando Whisper local (OpenAI)"""

    def __init__(self):
        try:
            import whisper

            self.model = whisper.load_model(Config.LOCAL_WHISPER_MODEL)
            print(f"✅ Whisper local cargado (modelo: {Config.LOCAL_WHISPER_MODEL})")
        except ImportError:
            raise ImportError("Whisper no instalado. Ejecuta: uv add openai-whisper")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe usando Whisper local"""
        try:
            result = self.model.transcribe(
                audio_file,
                language=Config.STT_LANGUAGE.split("-")[0],  # 'es' de 'es-MX'
                fp16=False,  # Compatibilidad CPU
            )
            return result["text"].strip()
        except Exception as e:
            print(f"❌ Error en transcripción Whisper local: {e}")
            return None


class OpenAIWhisperSTT(STTEngine):
    """Motor STT usando OpenAI Whisper API"""

    def __init__(self):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no configurada")

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
            print("✅ OpenAI Whisper API configurada")
        except ImportError:
            raise ImportError("OpenAI SDK no instalado. Ejecuta: uv add openai")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe usando OpenAI Whisper API"""
        try:
            with open(audio_file, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model=Config.WHISPER_MODEL,
                    file=audio,
                    language=Config.STT_LANGUAGE.split("-")[0],
                )
            return transcript.text.strip()
        except Exception as e:
            print(f"❌ Error en transcripción OpenAI: {e}")
            return None


class GoogleCloudSTT(STTEngine):
    """Motor STT usando Google Cloud Speech-to-Text"""

    def __init__(self):
        if not Config.GOOGLE_CLOUD_CREDENTIALS_PATH:
            raise ValueError("GOOGLE_CLOUD_CREDENTIALS_PATH no configurada")

        try:
            from google.cloud import speech

            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                Config.GOOGLE_CLOUD_CREDENTIALS_PATH
            )
            self.client = speech.SpeechClient()
            print("✅ Google Cloud Speech-to-Text configurado")
        except ImportError:
            raise ImportError(
                "Google Cloud Speech no instalado. Ejecuta: uv add google-cloud-speech"
            )

    def transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe usando Google Cloud"""
        try:
            from google.cloud import speech

            with open(audio_file, "rb") as audio:
                content = audio.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=Config.STT_LANGUAGE,
            )

            response = self.client.recognize(config=config, audio=audio)

            if response.results:
                return response.results[0].alternatives[0].transcript.strip()
            return None

        except Exception as e:
            print(f"❌ Error en transcripción Google Cloud: {e}")
            return None


class VoskSTT(STTEngine):
    """Motor STT usando Vosk (offline)"""

    def __init__(self):
        if not Config.VOSK_MODEL_PATH or not Path(Config.VOSK_MODEL_PATH).exists():
            raise ValueError(f"Modelo Vosk no encontrado: {Config.VOSK_MODEL_PATH}")

        try:
            from vosk import Model, KaldiRecognizer
            import json

            self.Model = Model
            self.KaldiRecognizer = KaldiRecognizer
            self.json = json
            self.model = Model(Config.VOSK_MODEL_PATH)
            print(f"✅ Vosk configurado (modelo: {Config.VOSK_MODEL_PATH})")
        except ImportError:
            raise ImportError("Vosk no instalado. Ejecuta: uv add vosk")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """Transcribe usando Vosk"""
        try:
            # Leer WAV
            wf = wave.open(audio_file, "rb")
            if (
                wf.getnchannels() != 1
                or wf.getsampwidth() != 2
                or wf.getframerate() != 16000
            ):
                print("❌ Audio debe ser mono, 16-bit, 16kHz")
                return None

            rec = self.KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)

            text = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = self.json.loads(rec.Result())
                    text += result.get("text", "") + " "

            final_result = self.json.loads(rec.FinalResult())
            text += final_result.get("text", "")

            return text.strip()

        except Exception as e:
            print(f"❌ Error en transcripción Vosk: {e}")
            return None


class STTManager:
    """Gestor de Speech-to-Text con fallback automático"""

    def __init__(self):
        self.engine = self._initialize_engine()

    def _initialize_engine(self) -> STTEngine:
        """Inicializa el motor STT según configuración"""
        engine_name = Config.STT_ENGINE

        try:
            if engine_name == "whisper_local":
                return WhisperLocalSTT()
            elif engine_name == "openai":
                return OpenAIWhisperSTT()
            elif engine_name == "google_cloud":
                return GoogleCloudSTT()
            elif engine_name == "vosk":
                return VoskSTT()
            else:
                raise ValueError(f"Motor STT desconocido: {engine_name}")
        except Exception as e:
            print(f"⚠️  Error inicializando {engine_name}: {e}")
            print("🔄 Intentando fallback a Whisper local...")
            try:
                return WhisperLocalSTT()
            except:
                raise RuntimeError("No se pudo inicializar ningún motor STT")

    def transcribe(self, audio_file: str) -> Optional[str]:
        """
        Transcribe un archivo de audio a texto

        Args:
            audio_file: Ruta al archivo WAV (16kHz mono)

        Returns:
            Texto transcrito o None si falla
        """
        if not Path(audio_file).exists():
            print(f"❌ Archivo no encontrado: {audio_file}")
            return None

        print(f"🎤 Transcribiendo: {audio_file}")
        text = self.engine.transcribe(audio_file)

        if text:
            print(f"✅ Transcripción: '{text}'")
        else:
            print("❌ Transcripción falló")

        return text


if __name__ == "__main__":
    # Test del módulo
    from config import Config

    Config.print_status()

    try:
        stt = STTManager()
        print("\n✅ STT Manager inicializado correctamente")

        # Ejemplo de uso
        # text = stt.transcribe("captured_commands/cmd_20251203_143022.wav")
        # print(f"Resultado: {text}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
