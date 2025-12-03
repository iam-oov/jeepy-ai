#!/usr/bin/env python3
"""
Jeepy AI - Setup de Configuración Inicial
Asistente interactivo para configurar API keys y dependencias
"""

import os
import sys
from pathlib import Path


def print_header():
    print("\n" + "=" * 70)
    print("🚗 JEEPY AI - Configuración Inicial")
    print("=" * 70 + "\n")


def check_env_file():
    """Verifica si existe .env, si no crea uno desde .env.example"""
    env_path = Path(".env")
    example_path = Path(".env.example")

    if not env_path.exists():
        if example_path.exists():
            print("📄 Creando archivo .env desde .env.example...")
            with open(example_path) as f:
                content = f.read()
            with open(env_path, "w") as f:
                f.write(content)
            print("✅ Archivo .env creado\n")
            return True
        else:
            print("❌ Error: .env.example no encontrado")
            return False
    else:
        print("✅ Archivo .env ya existe\n")
        return True


def get_api_key(service_name: str, env_var: str, url: str) -> str:
    """Solicita API key al usuario"""
    print(f"\n🔑 Configuración de {service_name}")
    print(f"   Obtén tu API key en: {url}")

    current_value = os.getenv(env_var, "")
    if current_value and current_value != f"your_{env_var.lower()}_here":
        print(f"   Valor actual: {current_value[:10]}...")
        use_current = input("   ¿Usar valor actual? (s/n): ").lower()
        if use_current == "s":
            return current_value

    key = input("   Ingresa tu API key (o presiona Enter para omitir): ").strip()
    return key


def update_env_file(updates: dict):
    """Actualiza el archivo .env con los nuevos valores"""
    env_path = Path(".env")

    with open(env_path) as f:
        lines = f.readlines()

    with open(env_path, "w") as f:
        for line in lines:
            updated = False
            for key, value in updates.items():
                if line.startswith(f"{key}=") and value:
                    f.write(f"{key}={value}\n")
                    updated = True
                    break
            if not updated:
                f.write(line)


def install_dependencies():
    """Guía para instalar dependencias"""
    print("\n📦 Instalación de Dependencias\n")

    print("Dependencias base (requeridas):")
    print("  uv add python-dotenv google-genai")

    print("\nMotores STT (elige uno o varios):")
    print("  1. Whisper Local (recomendado): uv add openai-whisper")
    print("  2. OpenAI Whisper API: uv add openai")
    print("  3. Google Cloud Speech: uv add google-cloud-speech")
    print("  4. Vosk (offline): uv add vosk")

    choice = input("\n¿Instalar dependencias ahora? (s/n): ").lower()
    if choice == "s":
        print("\nEjecutando instalación...")
        os.system("uv add python-dotenv google-genai openai-whisper openai")
        print("✅ Instalación completada")


def main():
    print_header()

    # 1. Verificar/crear .env
    if not check_env_file():
        sys.exit(1)

    # 2. Cargar .env actual
    from dotenv import load_dotenv

    load_dotenv()

    # 3. Configurar APIs
    updates = {}

    print("Vamos a configurar tus API keys:")

    # Gemini (obligatorio)
    gemini_key = get_api_key(
        "Google Gemini", "GEMINI_API_KEY", "https://aistudio.google.com/app/apikey"
    )
    if gemini_key:
        updates["GEMINI_API_KEY"] = gemini_key

    # OpenAI (opcional)
    openai_key = get_api_key(
        "OpenAI Whisper", "OPENAI_API_KEY", "https://platform.openai.com/api-keys"
    )
    if openai_key:
        updates["OPENAI_API_KEY"] = openai_key

    # STT Engine
    print("\n🎤 Motor de Speech-to-Text")
    print("  1. whisper_local (offline, gratis)")
    print("  2. openai (API, mejor calidad)")
    print("  3. google_cloud (API, mejor español)")
    print("  4. vosk (offline, más ligero)")

    stt_choice = input("\nSelecciona motor STT (1-4) [1]: ").strip() or "1"
    stt_engines = {
        "1": "whisper_local",
        "2": "openai",
        "3": "google_cloud",
        "4": "vosk",
    }
    updates["STT_ENGINE"] = stt_engines.get(stt_choice, "whisper_local")

    # 4. Actualizar .env
    if updates:
        print("\n💾 Guardando configuración...")
        update_env_file(updates)
        print("✅ Configuración guardada en .env")

    # 5. Instalar dependencias
    install_dependencies()

    # 6. Verificar configuración
    print("\n🔍 Verificando configuración...")
    from config import Config

    Config.print_status()

    is_valid, errors = Config.validate()

    if is_valid:
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\nPróximos pasos:")
        print("  1. Prueba el sistema: uv run python config.py")
        print("  2. Prueba STT: uv run python stt_engine.py")
        print("  3. Prueba Gemini: uv run python gemini_engine.py")
        print("  4. Ejecuta el monitor: uv run ./r-pi/kws_monitor.py")
    else:
        print("\n⚠️  Advertencias:")
        for error in errors:
            print(f"  {error}")
        print("\nPuedes continuar, pero algunas funciones pueden no estar disponibles.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuración cancelada")
        sys.exit(1)
