# jeepy-ai

Asistente de Voz "Jeepy" (Edge-to-LLM)
🚘 Jeepy AI: Asistente de Voz para Control Vehicular (Edge-to-LLM)
Un asistente de voz personalizado diseñado para operar en un entorno automotriz (Jeep), utilizando una arquitectura de doble etapa eficiente y el modelo de lenguaje avanzado Google Gemini para la comprensión de comandos. El sistema utiliza una Raspberry Pi como dispositivo de borde (Edge) para la activación local y de baja latencia.

✨ Características Principales
Activación por Palabra Clave Local: Detección de la palabra clave "Jeepy" en tiempo real y offline mediante un modelo de Keyword Spotting (KWS) optimizado con TinyML (TensorFlow Lite).

Comprensión de Lenguaje Natural (NLU): Utiliza Gemini para interpretar comandos complejos y contextuales (ej. "baja la ventana del piloto un 30%").

Control de Hardware (Tool-Use): Implementación de la función Tool-Use de Gemini para invocar comandos de Python que interactúan con las funciones del vehículo (vía simulación de CAN bus o GPIO).

Arquitectura de Bajo Consumo: El LLM solo se invoca después de la activación local, minimizando el consumo de datos y recursos.
