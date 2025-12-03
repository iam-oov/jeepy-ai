import os
import numpy as np
import librosa
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout

# --- CONFIGURACIÓN DE PARÁMETROS ---
SAMPLE_RATE = 16000  # Frecuencia de muestreo (Hz), debe coincidir con la grabación
MFCC_COUNT = 40  # Número de coeficientes MFCC a extraer
MAX_PADDING_LENGTH = (
    40  # Longitud máxima de tiempo después del padding (MFCCs en X-axis)
)
# Para 1 seg a 16kHz, 40 MFCCs, este valor es típico (~40)

# --- RUTAS DE DATOS ---
POSITIVE_DIR = "data/jeepy_positive"  # Clase 1: 'jeepy'
NEGATIVE_DIR = "data/jeepy_negative"  # Clase 0: 'no-jeepy'

## 1.1 Función de Extracción de MFCCs


def extract_mfcc(file_path):
    """
    Carga un archivo de audio, aplica padding y extrae MFCCs.
    """
    try:
        # Cargar el audio
        audio, sr = librosa.load(file_path, sr=SAMPLE_RATE)

        # Extraer MFCCs
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=MFCC_COUNT)

        # Aplicar padding para estandarizar la forma (IMPORTANTE para la CNN)
        if mfccs.shape[1] < MAX_PADDING_LENGTH:
            # Rellena con ceros al final
            padding_width = MAX_PADDING_LENGTH - mfccs.shape[1]
            mfccs = np.pad(
                mfccs, pad_width=((0, 0), (0, padding_width)), mode="constant"
            )
        else:
            # Si es demasiado largo, lo recorta (no debería pasar con muestras de 1s)
            mfccs = mfccs[:, :MAX_PADDING_LENGTH]

        # Asegurar la forma correcta para la CNN (MFCC_COUNT, MAX_PADDING_LENGTH, 1)
        mfccs = mfccs[..., np.newaxis]
        return mfccs

    except Exception as e:
        print(f"Error al procesar {file_path}: {e}")
        return None


## 1.2 Carga y Etiquetado de Datos


def load_data():
    """Carga MFCCs y etiquetas de las carpetas positiva y negativa."""
    features = []
    labels = []

    # Cargar muestras positivas (Etiqueta 1)
    print("Cargando muestras positivas...")
    for filename in os.listdir(POSITIVE_DIR):
        if filename.endswith(".wav"):
            file_path = os.path.join(POSITIVE_DIR, filename)
            mfcc_features = extract_mfcc(file_path)
            if mfcc_features is not None:
                features.append(mfcc_features)
                labels.append(1)

    # Cargar muestras negativas (Etiqueta 0)
    print("Cargando muestras negativas...")
    for filename in os.listdir(NEGATIVE_DIR):
        if filename.endswith(".wav"):
            file_path = os.path.join(NEGATIVE_DIR, filename)
            mfcc_features = extract_mfcc(file_path)
            if mfcc_features is not None:
                features.append(mfcc_features)
                labels.append(0)

    # Convertir a arrays de numpy para TensorFlow
    X = np.array(features)
    y = np.array(labels)

    print(f"Total de muestras cargadas: {len(X)}")
    return X, y


## 2. Definición del Modelo CNN (TinyML)


def build_kws_model(input_shape):
    """
    Define una Red Neuronal Convolucional (CNN) ligera para KWS.
    """
    model = Sequential(
        [
            # Capa Convolucional 1: Pequeña y eficiente
            Conv2D(32, (3, 3), activation="relu", input_shape=input_shape),
            MaxPooling2D((2, 2)),
            Dropout(0.25),  # Ayuda a prevenir el overfitting
            # Capa Convolucional 2
            Conv2D(64, (3, 3), activation="relu"),
            MaxPooling2D((2, 2)),
            Dropout(0.25),
            # Aplanar para las capas densas
            Flatten(),
            # Capas Densas (Clasificación)
            Dense(128, activation="relu"),
            Dropout(0.5),
            # Capa de Salida: 1 neurona con activación sigmoide para clasificación binaria (0 o 1)
            Dense(1, activation="sigmoid"),
        ]
    )

    # Compilación: Adam es un buen optimizador; binary_crossentropy para clasificación binaria
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

    return model


## 3. Proceso Principal de Entrenamiento

if __name__ == "__main__":
    # Cargar y pre-procesar datos
    X, y = load_data()

    # Dividir datos en Entrenamiento, Validación y Prueba (80/10/10)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=(1 / 9),
        random_state=42,
        stratify=y_train_val,
    )  # 10% de 90% es ~10% total

    print(f"Tamaño del conjunto de Entrenamiento: {len(X_train)}")
    print(f"Tamaño del conjunto de Validación: {len(X_val)}")
    print(f"Tamaño del conjunto de Prueba: {len(X_test)}")

    # Crear e imprimir la arquitectura del modelo
    input_shape = X_train.shape[1:]
    model = build_kws_model(input_shape)
    model.summary()

    # Entrenamiento del modelo
    print("\n--- INICIANDO ENTRENAMIENTO ---")
    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=50,  # Puedes ajustar el número de épocas
        batch_size=32,  # Ajusta el tamaño del lote
    )

    # Evaluación final en el conjunto de prueba
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n--- EVALUACIÓN FINAL ---")
    print(f"Pérdida (Loss) en Prueba: {loss:.4f}")
    print(f"Precisión (Accuracy) en Prueba: {accuracy:.4f}")

    # --- Guardar el modelo en formato Keras para el siguiente paso ---
    model.save("jeepy_kws_model.keras")
    print("\nModelo guardado como 'jeepy_kws_model.keras'")
