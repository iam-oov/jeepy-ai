#!/usr/bin/env python3
"""
Script de prueba para STT (Speech-to-Text)
Transcribe archivos de audio de prueba sin necesidad de micrófono
"""

import sys
import os
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from stt_engine import STTManager


def test_stt_engine():
    """Prueba el motor STT configurado"""
    print("\n" + "=" * 70)
    print("🎤 TEST DE STT (Speech-to-Text)")
    print("=" * 70)

    # Mostrar configuración
    print(f"\n📋 Configuración:")
    print(f"   Motor STT: {Config.STT_ENGINE}")
    print(f"   Idioma: {Config.STT_LANGUAGE}")

    if Config.STT_ENGINE == "whisper_local":
        print(f"   Modelo Whisper: {Config.LOCAL_WHISPER_MODEL}")
    elif Config.STT_ENGINE == "openai":
        if Config.OPENAI_API_KEY:
            print(f"   OpenAI API Key: {'*' * 20}{Config.OPENAI_API_KEY[-4:]}")
        else:
            print(f"   ⚠️  OpenAI API Key: NO CONFIGURADA")
    elif Config.STT_ENGINE == "google_cloud":
        if Config.GOOGLE_CLOUD_CREDENTIALS_PATH:
            print(f"   Credentials: {Config.GOOGLE_CLOUD_CREDENTIALS_PATH}")
        else:
            print(f"   ⚠️  Google Cloud Credentials: NO CONFIGURADAS")

    # Buscar archivos de audio de prueba
    captured_dir = Path("captured_commands")
    if not captured_dir.exists():
        print(f"\n❌ Directorio {captured_dir} no existe")
        print(f"   Ejecuta primero el sistema KWS para generar comandos")
        return

    audio_files = sorted(captured_dir.glob("cmd_*.wav"))
    if not audio_files:
        print(f"\n❌ No hay archivos de audio en {captured_dir}")
        print(f"   Ejecuta primero el sistema KWS y di 'Jeepy' + un comando")
        return

    print(f"\n📁 Archivos de audio encontrados: {len(audio_files)}")

    # Seleccionar archivo más reciente
    latest_file = audio_files[-1]
    print(f"\n🎯 Usando archivo más reciente: {latest_file.name}")

    # Inicializar STT Manager
    print(f"\n🔧 Inicializando STT Manager...")
    try:
        stt_manager = STTManager()
        print(f"   ✅ STT Manager inicializado correctamente")
    except Exception as e:
        print(f"   ❌ Error inicializando STT: {e}")
        print(f"\n💡 Soluciones:")

        if "OPENAI_API_KEY" in str(e):
            print(f"   1. Configurar OpenAI API Key:")
            print(f"      export OPENAI_API_KEY='tu-api-key'")
            print(f"   2. O cambiar a Whisper local:")
            print(f"      export STT_ENGINE='whisper_local'")
            print(f"      uv add openai-whisper")

        return

    # Transcribir
    print(f"\n📝 Transcribiendo...")
    print(f"   (Esto puede tomar unos segundos...)")

    try:
        transcription = stt_manager.transcribe(str(latest_file))

        if transcription:
            print(f"\n✅ Transcripción exitosa:")
            print(f"\n{'=' * 70}")
            print(f'💬 "{transcription}"')
            print(f"{'=' * 70}\n")

            # Guardar transcripción
            trans_dir = Path("transcriptions")
            trans_dir.mkdir(exist_ok=True)

            timestamp = latest_file.stem.replace("cmd_", "")
            trans_file = trans_dir / f"trans_{timestamp}.txt"

            with open(trans_file, "w", encoding="utf-8") as f:
                f.write(f"# Transcripción de prueba\n")
                f.write(f"# Audio: {latest_file}\n")
                f.write(f"# Motor STT: {Config.STT_ENGINE}\n")
                f.write(f"\n{transcription}\n")

            print(f"💾 Transcripción guardada en: {trans_file}")

        else:
            print(f"\n❌ No se pudo transcribir el archivo")

    except Exception as e:
        print(f"\n❌ Error durante transcripción: {e}")
        import traceback

        traceback.print_exc()


def test_all_audio_files():
    """Transcribe todos los archivos de audio disponibles"""
    print("\n" + "=" * 70)
    print("🎤 TEST MASIVO DE STT - Todos los archivos")
    print("=" * 70)

    captured_dir = Path("captured_commands")
    if not captured_dir.exists():
        print(f"\n❌ Directorio {captured_dir} no existe")
        return

    audio_files = sorted(captured_dir.glob("cmd_*.wav"))
    if not audio_files:
        print(f"\n❌ No hay archivos de audio")
        return

    print(f"\n📁 Total de archivos: {len(audio_files)}")
    print(f"\n🔧 Inicializando STT Manager...")

    try:
        stt_manager = STTManager()
        print(f"   ✅ Inicializado: {Config.STT_ENGINE}\n")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    trans_dir = Path("transcriptions")
    trans_dir.mkdir(exist_ok=True)

    successful = 0
    failed = 0

    for i, audio_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] {audio_file.name}...", end=" ")

        try:
            transcription = stt_manager.transcribe(str(audio_file))

            if transcription:
                print(
                    f'✅ "{transcription[:50]}..."'
                    if len(transcription) > 50
                    else f'✅ "{transcription}"'
                )

                # Guardar
                timestamp = audio_file.stem.replace("cmd_", "")
                trans_file = trans_dir / f"trans_{timestamp}.txt"

                with open(trans_file, "w", encoding="utf-8") as f:
                    f.write(f"# Audio: {audio_file}\n")
                    f.write(f"# Motor: {Config.STT_ENGINE}\n")
                    f.write(f"\n{transcription}\n")

                successful += 1
            else:
                print(f"❌ Sin transcripción")
                failed += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1

    print(f"\n" + "=" * 70)
    print(f"📊 Resultados:")
    print(f"   ✅ Exitosas: {successful}")
    print(f"   ❌ Fallidas: {failed}")
    print(f"   📁 Transcripciones en: {trans_dir}")
    print(f"=" * 70 + "\n")


def main():
    """Función principal"""
    import argparse

    parser = argparse.ArgumentParser(description="Test de STT para Jeepy AI")
    parser.add_argument(
        "--all", action="store_true", help="Transcribir todos los archivos de audio"
    )
    parser.add_argument("--file", type=str, help="Transcribir un archivo específico")

    args = parser.parse_args()

    if args.file:
        # Transcribir archivo específico
        print(f"\n🎯 Transcribiendo: {args.file}")
        try:
            stt_manager = STTManager()
            transcription = stt_manager.transcribe(args.file)
            if transcription:
                print(f'\n✅ "{transcription}"\n')
            else:
                print(f"\n❌ Sin transcripción\n")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

    elif args.all:
        # Transcribir todos
        test_all_audio_files()

    else:
        # Test simple (último archivo)
        test_stt_engine()


if __name__ == "__main__":
    main()
