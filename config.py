"""
Jeepy AI - Módulo de Configuración
Gestiona variables de entorno y configuración de APIs
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Config:
    """Configuración centralizada de Jeepy AI"""

    # Paths
    BASE_DIR = Path(__file__).parent
    CAPTURED_COMMANDS_DIR = BASE_DIR / "captured_commands"
    MODELS_DIR = BASE_DIR / "models"
    CREDENTIALS_DIR = BASE_DIR / "credentials"

    # --- GEMINI API ---
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    # --- STT Configuration ---
    STT_ENGINE: str = os.getenv(
        "STT_ENGINE", "whisper_local"
    )  # google_cloud, openai, whisper_local, vosk
    STT_LANGUAGE: str = os.getenv("STT_LANGUAGE", "es-MX")

    # Google Cloud STT
    GOOGLE_CLOUD_CREDENTIALS_PATH: Optional[str] = os.getenv(
        "GOOGLE_CLOUD_CREDENTIALS_PATH"
    )

    # OpenAI Whisper API
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-1")

    # Local Whisper
    USE_LOCAL_WHISPER: bool = os.getenv("USE_LOCAL_WHISPER", "true").lower() == "true"
    LOCAL_WHISPER_MODEL: str = os.getenv("LOCAL_WHISPER_MODEL", "base")

    # Vosk
    USE_VOSK: bool = os.getenv("USE_VOSK", "false").lower() == "true"
    VOSK_MODEL_PATH: Optional[str] = os.getenv("VOSK_MODEL_PATH")

    # --- General Settings ---
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Valida la configuración y retorna (is_valid, errors)
        """
        errors = []

        # Validar Gemini API
        if not cls.GEMINI_API_KEY:
            errors.append("❌ GEMINI_API_KEY no configurada")

        # Validar STT según motor seleccionado
        if cls.STT_ENGINE == "google_cloud":
            if not cls.GOOGLE_CLOUD_CREDENTIALS_PATH:
                errors.append(
                    "❌ GOOGLE_CLOUD_CREDENTIALS_PATH no configurada para google_cloud STT"
                )
            elif not Path(cls.GOOGLE_CLOUD_CREDENTIALS_PATH).exists():
                errors.append(
                    f"❌ Archivo de credenciales no encontrado: {cls.GOOGLE_CLOUD_CREDENTIALS_PATH}"
                )

        elif cls.STT_ENGINE == "openai":
            if not cls.OPENAI_API_KEY:
                errors.append("❌ OPENAI_API_KEY no configurada para OpenAI Whisper")

        elif cls.STT_ENGINE == "vosk":
            if not cls.VOSK_MODEL_PATH:
                errors.append("❌ VOSK_MODEL_PATH no configurada para Vosk STT")
            elif not Path(cls.VOSK_MODEL_PATH).exists():
                errors.append(f"❌ Modelo Vosk no encontrado: {cls.VOSK_MODEL_PATH}")

        # whisper_local no requiere validación de API keys

        return len(errors) == 0, errors

    @classmethod
    def print_status(cls):
        """Imprime el estado de la configuración"""
        print("\n" + "=" * 60)
        print("🚀 JEEPY AI - Estado de Configuración")
        print("=" * 60)

        # Gemini
        gemini_status = "✅" if cls.GEMINI_API_KEY else "❌"
        gemini_key = (
            f"{cls.GEMINI_API_KEY[:8]}..." if cls.GEMINI_API_KEY else "No configurada"
        )
        print(f"\n📡 Gemini API:")
        print(f"  {gemini_status} API Key: {gemini_key}")
        print(f"  📝 Modelo: {cls.GEMINI_MODEL}")

        # STT
        print(f"\n🎤 Speech-to-Text:")
        print(f"  🔧 Motor: {cls.STT_ENGINE}")
        print(f"  🌍 Idioma: {cls.STT_LANGUAGE}")

        if cls.STT_ENGINE == "whisper_local":
            print(f"  📦 Modelo Local: {cls.LOCAL_WHISPER_MODEL}")
        elif cls.STT_ENGINE == "openai":
            openai_status = "✅" if cls.OPENAI_API_KEY else "❌"
            print(
                f"  {openai_status} OpenAI API Key: {'Configurada' if cls.OPENAI_API_KEY else 'No configurada'}"
            )
        elif cls.STT_ENGINE == "google_cloud":
            gc_status = (
                "✅"
                if cls.GOOGLE_CLOUD_CREDENTIALS_PATH
                and Path(cls.GOOGLE_CLOUD_CREDENTIALS_PATH).exists()
                else "❌"
            )
            print(
                f"  {gc_status} Google Cloud Credentials: {cls.GOOGLE_CLOUD_CREDENTIALS_PATH or 'No configuradas'}"
            )
        elif cls.STT_ENGINE == "vosk":
            vosk_status = (
                "✅"
                if cls.VOSK_MODEL_PATH and Path(cls.VOSK_MODEL_PATH).exists()
                else "❌"
            )
            print(
                f"  {vosk_status} Vosk Model: {cls.VOSK_MODEL_PATH or 'No configurado'}"
            )

        # Validación
        is_valid, errors = cls.validate()
        print(
            f"\n🔍 Validación: {'✅ Configuración completa' if is_valid else '❌ Errores encontrados'}"
        )
        if errors:
            for error in errors:
                print(f"  {error}")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    Config.print_status()
    is_valid, errors = Config.validate()

    if not is_valid:
        print("\n⚠️  Pasos para configurar:")
        print("1. Copia .env.example a .env")
        print("2. Edita .env con tus API keys")
        print("3. Ejecuta: uv add python-dotenv google-genai openai")
        exit(1)
    else:
        print("✅ Sistema listo para integración!")
