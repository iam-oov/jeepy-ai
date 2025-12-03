#!/usr/bin/env python3
"""
Script de verificación de integración STT
Valida que todos los componentes estén correctamente configurados
"""

import os
import sys
from pathlib import Path


def check_emoji(passed: bool) -> str:
    """Retorna emoji según resultado"""
    return "✅" if passed else "❌"


def print_section(title: str):
    """Imprime sección con formato"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def check_files():
    """Verifica que archivos necesarios existan"""
    print_section("📁 VERIFICACIÓN DE ARCHIVOS")

    files_to_check = {
        "config.py": "Configuración general",
        "stt_engine.py": "Motores STT",
        "r-pi/kws_monitor.py": "Monitor KWS con STT",
        "test_stt.py": "Script de pruebas",
        "transcriptions/README.md": "Documentación transcripciones",
        ".env": "Variables de entorno (API keys)",
    }

    all_exist = True
    for file, description in files_to_check.items():
        exists = Path(file).exists()
        all_exist = all_exist and exists
        print(f"{check_emoji(exists)} {file:35} - {description}")

    return all_exist


def check_imports():
    """Verifica que módulos se puedan importar"""
    print_section("📦 VERIFICACIÓN DE IMPORTS")

    imports_ok = True

    # Config
    try:
        from config import Config

        print(f"✅ config.Config importado")
        print(f"   - STT_ENGINE: {Config.STT_ENGINE}")
        print(f"   - STT_LANGUAGE: {Config.STT_LANGUAGE}")
    except Exception as e:
        print(f"❌ Error importando config: {e}")
        imports_ok = False

    # STT Engine
    try:
        from stt_engine import STTManager

        print(f"✅ stt_engine.STTManager importado")
    except Exception as e:
        print(f"❌ Error importando stt_engine: {e}")
        imports_ok = False

    return imports_ok


def check_configuration():
    """Verifica configuración STT"""
    print_section("⚙️  VERIFICACIÓN DE CONFIGURACIÓN")

    try:
        from config import Config

        config_ok = True

        # Motor STT
        valid_engines = ["openai", "whisper_local", "google_cloud", "vosk"]
        engine_ok = Config.STT_ENGINE in valid_engines
        print(f"{check_emoji(engine_ok)} Motor STT: {Config.STT_ENGINE}")
        if not engine_ok:
            print(f"   ⚠️  Motores válidos: {', '.join(valid_engines)}")
        config_ok = config_ok and engine_ok

        # Idioma
        language_ok = bool(Config.STT_LANGUAGE)
        print(f"{check_emoji(language_ok)} Idioma: {Config.STT_LANGUAGE}")
        config_ok = config_ok and language_ok

        # API Keys según motor
        if Config.STT_ENGINE == "openai":
            key_ok = bool(Config.OPENAI_API_KEY)
            print(f"{check_emoji(key_ok)} OpenAI API Key configurada")
            if key_ok:
                print(f"   - Key: {'*' * 20}{Config.OPENAI_API_KEY[-4:]}")
            config_ok = config_ok and key_ok

        elif Config.STT_ENGINE == "google_cloud":
            key_ok = bool(Config.GOOGLE_CLOUD_CREDENTIALS_PATH)
            print(f"{check_emoji(key_ok)} Google Cloud Credentials configuradas")
            if key_ok:
                print(f"   - Path: {Config.GOOGLE_CLOUD_CREDENTIALS_PATH}")
            config_ok = config_ok and key_ok

        elif Config.STT_ENGINE == "whisper_local":
            model_ok = bool(Config.LOCAL_WHISPER_MODEL)
            print(
                f"{check_emoji(model_ok)} Modelo Whisper Local: {Config.LOCAL_WHISPER_MODEL}"
            )
            config_ok = config_ok and model_ok

        return config_ok

    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        return False


def check_stt_initialization():
    """Verifica que STTManager se puede inicializar"""
    print_section("🔧 VERIFICACIÓN DE INICIALIZACIÓN STT")

    try:
        from stt_engine import STTManager
        from config import Config

        print(f"🔄 Inicializando STTManager con motor '{Config.STT_ENGINE}'...")
        manager = STTManager()

        print(f"✅ STTManager inicializado correctamente")
        print(f"   - Motor activo: {Config.STT_ENGINE}")

        return True

    except Exception as e:
        print(f"❌ Error inicializando STTManager: {e}")
        print(f"\n💡 Posibles soluciones:")

        if "OPENAI_API_KEY" in str(e):
            print(f"   1. Configurar OpenAI API Key en .env:")
            print(f"      echo 'OPENAI_API_KEY=tu-api-key' >> .env")
            print(f"   2. O cambiar a motor local:")
            print(f"      echo 'STT_ENGINE=whisper_local' >> .env")

        elif "google" in str(e).lower():
            print(f"   1. Configurar Google Cloud Credentials:")
            print(
                f"      echo 'GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json' >> .env"
            )

        elif "whisper" in str(e).lower():
            print(f"   1. Instalar Whisper:")
            print(f"      uv add openai-whisper")

        return False


def check_directories():
    """Verifica directorios de output"""
    print_section("📂 VERIFICACIÓN DE DIRECTORIOS")

    dirs_ok = True

    dirs_to_check = {
        "captured_commands": "Comandos de audio grabados",
        "transcriptions": "Transcripciones STT",
    }

    for dir_name, description in dirs_to_check.items():
        dir_path = Path(dir_name)
        exists = dir_path.exists()

        if exists:
            file_count = len(list(dir_path.glob("*")))
            print(f"✅ {dir_name:20} - {description} ({file_count} archivos)")
        else:
            print(f"⚠️  {dir_name:20} - {description} (será creado automáticamente)")

    return dirs_ok


def check_audio_files():
    """Verifica si hay archivos de audio para probar"""
    print_section("🎵 VERIFICACIÓN DE ARCHIVOS DE AUDIO")

    audio_dir = Path("captured_commands")
    if not audio_dir.exists():
        print(f"⚠️  No existe directorio captured_commands/")
        print(f"   Ejecuta primero: uv run ./r-pi/kws_monitor.py")
        return False

    audio_files = list(audio_dir.glob("cmd_*.wav"))

    if not audio_files:
        print(f"⚠️  No hay archivos de audio capturados")
        print(f"   Ejecuta: uv run ./r-pi/kws_monitor.py")
        print(f"   Y di: 'Jeepy' + un comando")
        return False

    print(f"✅ Encontrados {len(audio_files)} archivos de audio")

    # Mostrar últimos 3
    for audio_file in sorted(audio_files)[-3:]:
        size_kb = audio_file.stat().st_size / 1024
        print(f"   - {audio_file.name} ({size_kb:.1f} KB)")

    return True


def check_test_script():
    """Verifica que test_stt.py funcione"""
    print_section("🧪 VERIFICACIÓN DE SCRIPT DE PRUEBAS")

    test_script = Path("test_stt.py")

    if not test_script.exists():
        print(f"❌ No existe test_stt.py")
        return False

    print(f"✅ test_stt.py existe")
    print(f"\n💡 Comandos disponibles:")
    print(f"   - uv run python test_stt.py          # Test simple")
    print(f"   - uv run python test_stt.py --all    # Todos los archivos")
    print(f"   - uv run python test_stt.py --file <archivo>")

    return True


def run_quick_test():
    """Ejecuta test rápido si hay archivos"""
    print_section("⚡ TEST RÁPIDO (OPCIONAL)")

    audio_dir = Path("captured_commands")
    if not audio_dir.exists():
        print(f"⏭️  Sin archivos de audio - test omitido")
        return True

    audio_files = list(audio_dir.glob("cmd_*.wav"))
    if not audio_files:
        print(f"⏭️  Sin archivos de audio - test omitido")
        return True

    # Preguntar al usuario
    print(f"📁 {len(audio_files)} archivos de audio disponibles")
    response = input(f"\n¿Ejecutar test de transcripción? (s/n): ").strip().lower()

    if response not in ["s", "si", "sí", "y", "yes"]:
        print(f"⏭️  Test omitido")
        return True

    # Ejecutar test
    print(f"\n🔄 Ejecutando test...")
    import subprocess

    result = subprocess.run(
        ["uv", "run", "python", "test_stt.py"], capture_output=False
    )

    return result.returncode == 0


def main():
    """Función principal"""
    print("\n" + "=" * 70)
    print("  🔍 VERIFICACIÓN DE INTEGRACIÓN STT - Jeepy AI")
    print("=" * 70)

    results = {
        "Archivos": check_files(),
        "Imports": check_imports(),
        "Configuración": check_configuration(),
        "Inicialización STT": check_stt_initialization(),
        "Directorios": check_directories(),
        "Archivos de Audio": check_audio_files(),
        "Script de Pruebas": check_test_script(),
    }

    # Resumen
    print_section("📊 RESUMEN")

    all_passed = True
    for check_name, passed in results.items():
        print(f"{check_emoji(passed)} {check_name}")
        all_passed = all_passed and passed

    print(f"\n{'=' * 70}")

    if all_passed:
        print(f"✅ TODAS LAS VERIFICACIONES PASARON")
        print(f"\n🎉 Sistema STT listo para usar!")
        print(f"\n💡 Siguiente paso:")
        print(f"   uv run python test_stt.py")

        # Ofrecer test rápido
        run_quick_test()

    else:
        print(f"⚠️  ALGUNAS VERIFICACIONES FALLARON")
        print(f"\n💡 Revisa los errores arriba y corrige antes de continuar")

    print(f"{'=' * 70}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
