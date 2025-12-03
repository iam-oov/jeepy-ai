import pyaudio
import numpy as np
import librosa
import time
import tensorflow as tf  # Usaremos tf.lite.Interpreter en lugar de tflite-runtime para simplicidad en el desarrollo

# --- CONFIGURACIÓN DEL MODELO Y AUDIO ---
TFLITE_MODEL_PATH = "jeepy_kws_model_quantized.tflite"
SAMPLE_RATE = 16000  # Debe coincidir con el entrenamiento (16 kHz)
MFCC_COUNT = 40  # Debe coincidir con el entrenamiento (40 coeficientes)
MAX_PADDING_LENGTH = 40  # Debe coincidir con el entrenamiento (~40 para 1 segundo)
CHUNK = int(SAMPLE_RATE * 1.0)  # Un fragmento de 1.0 segundo para la inferencia
FORMAT = (
    pyaudio.paFloat32
)  # Usamos Float32 para evitar conversiones complejas si el modelo TFLite lo requiere
CHANNELS = 1

# --- CONFIGURACIÓN DE ACTIVACIÓN ---
ACTIVATION_THRESHOLD = (
    0.92  # Umbral de confianza (ajustar aquí, usar >0.95 por la precisión baja)
)


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

    p.terminate()

    # Pídele al usuario que introduzca el índice manualmente
    try:
        index = int(input("\nPor favor, introduce el índice de tu micrófono: "))
        return index
    except ValueError:
        print("Entrada no válida. Usando el índice 0 por defecto.")
        return 0


def extract_mfcc(audio_chunk):
    """
    Función para extraer MFCCs, idéntica a la usada en el entrenamiento.
    """
    try:
        # Extraer MFCCs
        # Nota: librosa espera muestras de punto flotante (dtype=float32)
        mfccs = librosa.feature.mfcc(y=audio_chunk, sr=SAMPLE_RATE, n_mfcc=MFCC_COUNT)

        # Aplicar Padding
        if mfccs.shape[1] < MAX_PADDING_LENGTH:
            padding_width = MAX_PADDING_LENGTH - mfccs.shape[1]
            mfccs = np.pad(
                mfccs, pad_width=((0, 0), (0, padding_width)), mode="constant"
            )
        else:
            mfccs = mfccs[:, :MAX_PADDING_LENGTH]

        # Asegurar la forma (MFCC_COUNT, MAX_PADDING_LENGTH, 1) y el tipo (float32)
        mfccs = mfccs[np.newaxis, ..., np.newaxis].astype(np.float32)
        return mfccs

    except Exception as e:
        print(f"Error en la extracción de MFCCs: {e}")
        return None


def initialize_tflite_interpreter():
    """
    Carga el modelo TFLite cuantizado y prepara el intérprete.
    """
    try:
        # Cargar el modelo TFLite (En RPi, usar tflite_runtime.interpreter)
        interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
        interpreter.allocate_tensors()

        # Obtener los detalles de las capas de entrada y salida
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print("✅ Intérprete TFLite cargado con éxito.")
        return interpreter, input_details, output_details
    except Exception as e:
        print(
            f"❌ Error al cargar el modelo TFLite. Asegúrate de que el archivo existe y las dependencias están instaladas. Error: {e}"
        )
        return None, None, None


def kws_monitor(device_index):
    """
    Bucle principal de monitoreo de audio en vivo.
    """
    interpreter, input_details, output_details = initialize_tflite_interpreter()
    if interpreter is None:
        return

    # Inicializar PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=device_index,
    )

    print("\n--- MONITOREO KWS ACTIVO (Diga 'Jeepy') ---")
    print(f"Umbral de activación: {ACTIVATION_THRESHOLD}")

    while True:
        try:
            # 1. Leer un fragmento de audio (1.0 segundo)
            audio_data = stream.read(CHUNK, exception_on_overflow=False)

            # Convertir bytes a array de numpy (float32)
            audio_chunk = np.frombuffer(audio_data, dtype=np.float32)

            # 2. Pre-procesamiento: Extraer MFCCs
            mfccs_input = extract_mfcc(audio_chunk)

            if mfccs_input is None:
                continue

            # 3. Inferencia TFLite
            interpreter.set_tensor(input_details[0]["index"], mfccs_input)
            interpreter.invoke()

            # Obtener el resultado (la predicción de la capa de salida)
            output_data = interpreter.get_tensor(output_details[0]["index"])

            # La salida es una probabilidad (usando sigmoide)
            probability_jeepy = output_data[0][0]

            # 4. Evaluación del Umbral
            if probability_jeepy >= ACTIVATION_THRESHOLD:
                # --- ACCIÓN DE ACTIVACIÓN (Etapa 2) ---
                print("\n\n#####################################################")
                print(f"¡PALABRA CLAVE DETECTADA! Confianza: {probability_jeepy:.4f}")
                print(">>> Iniciando Grabación del Comando y Llamada a Gemini...")
                # Aquí iría la lógica para:
                # 1. Detener el bucle KWS.
                # 2. Grabar 5 segundos de audio para el comando.
                # 3. Llamar al STT (Vosk o Cloud).
                # 4. Llamar a Gemini.
                # 5. Volver al bucle KWS.
                print("#####################################################\n")

                # Para fines de prueba, detenemos la simulación o introducimos un retardo
                time.sleep(3)

            # Mostrar el estado actual (opcional, para depuración)
            print(f"Monitoreo... Probabilidad: {probability_jeepy:.4f}", end="\r")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error inesperado en el bucle de monitoreo: {e}")
            break

    # Cierre de PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Monitoreo detenido.")


if __name__ == "__main__":
    # Usamos la importación de tf.lite.Interpreter. Si estás en RPi y tienes problemas,
    # reemplaza 'tensorflow as tf' por 'import tflite_runtime.interpreter as tflite'
    # y ajusta el código según la documentación de tflite-runtime.

    # Seleccionar dispositivo de audio
    mic_index = get_input_device_index()

    kws_monitor(mic_index)
