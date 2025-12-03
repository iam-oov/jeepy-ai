#!/usr/bin/env python3
"""
Test del pipeline completo: STT → Gemini
"""

import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from gemini_engine import JeepyAssistant


def test_gemini_integration():
    """Prueba la integración completa con comandos reales"""
    print("\n" + "=" * 70)
    print("🧪 TEST DE INTEGRACIÓN: STT → GEMINI")
    print("=" * 70)

    # Comandos de prueba (ya transcritos)
    test_commands = [
        "Baja la ventana del piloto un 50%",
        "Enciende las luces delanteras",
        "Sube la temperatura a 22 grados",
        "Bloquea todas las puertas",
        "Reproduce música desde bluetooth",
        "¿Podrías bajar las ventanas?",
        "Pon la estación 95.3",
        "Llamar a casa",
    ]

    try:
        print(f"\n🔧 Inicializando Jeepy Assistant...")
        assistant = JeepyAssistant()
        print(f"✅ Assistant listo\n")

        for i, cmd in enumerate(test_commands, 1):
            print(f"\n{'─' * 70}")
            print(f"Test {i}/{len(test_commands)}")
            result = assistant.process_audio_command(cmd)

            if result["success"]:
                print(f"   ✅ Comando ejecutado correctamente")
            else:
                print(f"   ⚠️ Comando no ejecutado (posible aclaración requerida)")

            input("\n[Presiona ENTER para continuar...]")

        print(f"\n{'=' * 70}")
        print(f"✅ Test completado")
        print(f"{'=' * 70}\n")

    except Exception as e:
        print(f"\n❌ Error durante test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_gemini_integration()
