import pyaudio
import wave
import numpy as np
import os
import time

# --- CONFIGURACIÓN DE GRABACIÓN ---
FORMAT = pyaudio.paInt16  # Formato de audio (16 bits)
CHANNELS = 1  # Mono
RATE = 16000  # Tasa de muestreo (16 kHz, estándar para ML de voz)
CHUNK = 1024  # Fragmentos de audio a leer
MAX_SILENCE_DURATION = (
    1.0  # Segundos de silencio para detener la grabación (experimental)
)
ENERGY_THRESHOLD = 500  # Nivel de energía para empezar a grabar (ajusta este valor)
SILENCE_CHUNKS = int(MAX_SILENCE_DURATION * RATE / CHUNK)

# --- RUTAS DE SALIDA ---
OUTPUT_POSITIVE_DIR = "data/jeepy_positive"
OUTPUT_NEGATIVE_DIR = "data/jeepy_negative"


def get_input_device_index():
    """Identifica el índice del dispositivo de entrada (micrófono) para PyAudio."""
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get("deviceCount")

    print("\n--- Dispositivos de Audio Disponibles ---")
    for i in range(0, numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if (device_info.get("maxInputChannels")) > 0:
            print(f"  Input Device Index {i} - {device_info.get('name')}")
            # Si tu micrófono es USB, puedes buscar el nombre exacto aquí.
            # return i # Descomentar para seleccionar el primero con entrada

    p.terminate()

    # Asume el índice 0 o el que hayas identificado para tu micrófono USB
    # Pídele al usuario que introduzca el índice manualmente para mayor seguridad
    try:
        index = int(input("\nPor favor, introduce el índice de tu micrófono USB: "))
        return index
    except ValueError:
        print("Entrada no válida. Usando el índice 0 por defecto.")
        return 0


def record_jeepy_sample(device_index, output_dir: str):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=device_index,
    )

    print("\n-----------------------------------------------------")
    print("GRABADOR LISTO. Presiona ENTER para grabar.")
    print("-----------------------------------------------------")
    input()
    print(">>> HABLA AHORA: Grabando ...")

    frames = []

    # --- BUCLE DE GRABACIÓN ---
    # Grabamos por 3 segundos para compensar el retraso del micrófono
    for i in range(0, int(RATE / CHUNK * 3)):  # Grabamos por 3 segundos
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    print(">>> GRABACIÓN FINALIZADA.")

    # --- CIERRE DE STREAM ---
    stream.stop_stream()
    stream.close()
    p.terminate()

    # --- ELIMINAR EL PRIMER SEGUNDO ---
    # Calculamos cuántos chunks representan 1 segundo
    chunks_per_second = int(RATE / CHUNK * 1)
    frames = frames[chunks_per_second:]  # Eliminamos el primer segundo

    # --- GUARDAR ARCHIVO ---
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"jeepy_{timestamp}.wav")

    wf = wave.open(filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"✅ Muestra guardada como: {filename}")


if __name__ == "__main__":
    # Crea la estructura de carpetas
    os.makedirs("data", exist_ok=True)
    os.makedirs(OUTPUT_POSITIVE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_NEGATIVE_DIR, exist_ok=True)

    mic_index = get_input_device_index()

    print("\n--- INICIO DE RECOLECCIÓN DE MUESTRAS EN EL JEEP ---")

    mode = input(
        "\nIntroduce 'P' para [Positivo/Jeepy] o 'N' para [Negativo/Ruido/Otras palabras] o 'Q' para Salir: "
    ).upper()

    while True:
        if mode == "P":
            record_jeepy_sample(mic_index, OUTPUT_POSITIVE_DIR)
        elif mode == "N":
            record_jeepy_sample(mic_index, OUTPUT_NEGATIVE_DIR)
        elif mode == "Q":
            print("Saliendo del grabador. ¡Éxito con tu entrenamiento!")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")
