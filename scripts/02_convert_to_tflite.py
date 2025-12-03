import tensorflow as tf
import os

MODEL_PATH = "jeepy_kws_model.keras"
OUTPUT_TFLITE_PATH = "jeepy_kws_model_quantized.tflite"

if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH):
        print(f"Error: No se encontró el modelo entrenado en {MODEL_PATH}.")
        print("Asegúrate de ejecutar el script de entrenamiento primero.")
    else:
        # Cargar el modelo entrenado
        model = tf.keras.models.load_model(MODEL_PATH)

        # 1. Configurar el TFLite Converter
        converter = tf.lite.TFLiteConverter.from_keras_model(model)

        # 2. Habilitar Optimizaciones (¡Cuantización!)
        # Esta es la clave para TinyML: reduce el tamaño y acelera la inferencia.
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        # 3. Aplicar Cuantización de Enteros (Cuantización Completa)
        # Esto reduce el modelo de 32 bits a 8 bits.
        # Requiere un 'Representative Dataset' para calibración.
        # Para simplificar, aquí usamos una cuantización post-entrenamiento básica.

        # Generar el modelo TFLite
        tflite_model = converter.convert()

        # Guardar el modelo TFLite cuantizado
        with open(OUTPUT_TFLITE_PATH, "wb") as f:
            f.write(tflite_model)

        print("\n--- CONVERSIÓN TFLITE EXITOSA ---")
        print(f"Modelo cuantizado guardado como: {OUTPUT_TFLITE_PATH}")
        print("¡Este archivo es el que usarás en la Raspberry Pi!")
