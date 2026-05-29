# 🚗 Jeepy AI

Asistente de voz para un entorno automotriz (Jeep), pensado para correr en una
**Raspberry Pi** como dispositivo de borde (Edge). Usa una arquitectura
**Edge-to-LLM**: la activación por palabra clave es local y de baja latencia, y
solo se invoca al LLM (Google Gemini) *después* de la activación, para minimizar
consumo de datos y de recursos.

> **Estado**: prototipo funcional en desarrollo. El control del vehículo está
> **simulado** (solo logging) — todavía no hay integración real con CAN bus ni GPIO.

---

## 🧭 Cómo funciona

```
🎤 Micrófono → 🎯 KWS ("Jeepy") → 🔴 Grabación → 💾 WAV → 📝 STT → 🧠 Gemini → 🚗 VehicleController
   └──────────── EDGE (local, offline) ────────────┘   └───────── CLOUD / LLM ──────────┘
```

1. **KWS (Keyword Spotting)** — `r-pi/kws_monitor.py` detecta la palabra "Jeepy"
   de forma local con un modelo TensorFlow Lite cuantizado. Usa ventana deslizante,
   features MFCC y un sistema de confirmación (2 detecciones) para reducir falsos
   positivos.
2. **Grabación** — tras la activación graba el comando hasta detectar ~1.5s de
   silencio (con pre-buffer y duración máxima de seguridad) y lo guarda como WAV
   16kHz mono en `captured_commands/`.
3. **STT (Speech-to-Text)** — `stt_engine.py` transcribe el WAV a texto. Soporta
   4 motores con fallback automático a Whisper local.
4. **NLU (Gemini)** — `gemini_engine.py` interpreta el texto y devuelve una acción
   estructurada en JSON (acción + parámetros + confianza + respuesta natural).
5. **Control del vehículo** — `VehicleController` ejecuta la acción. **Hoy es una
   simulación** (imprime lo que haría); la integración real con CAN bus / GPIO es
   trabajo futuro.

> ⚠️ **Nota técnica**: la NLU usa el **modo JSON estructurado** de Gemini
> (`response_mime_type="application/json"` + system instruction), **no** function
> calling / Tool-Use nativo. Las "acciones" son un contrato JSON que define el
> system prompt, no herramientas registradas en la API.

---

## 🎤 Motores STT soportados

| Motor          | Clave (`STT_ENGINE`) | Tipo   | Requiere                          |
| -------------- | -------------------- | ------ | --------------------------------- |
| Whisper Local  | `whisper_local`      | Local  | `openai-whisper` (default)        |
| OpenAI Whisper | `openai`             | API    | `OPENAI_API_KEY`                  |
| Google Cloud   | `google_cloud`       | API    | `GOOGLE_CLOUD_CREDENTIALS_PATH`   |
| Vosk           | `vosk`               | Local  | `VOSK_MODEL_PATH` (modelo Vosk)   |

Si el motor configurado falla al inicializar, `STTManager` hace **fallback
automático a Whisper local**.

---

## 🧠 Acciones de vehículo (simuladas)

Definidas en el system prompt de `gemini_engine.py` y ejecutadas por
`VehicleController`:

`control_ventana`, `control_climatizacion`, `control_luces`,
`control_cerraduras`, `reproducir_musica`, `navegacion`, `llamada_telefono`.

Ejemplo: _"baja la ventana del piloto un 50%"_ → `control_ventana` con
`{posicion: piloto, accion: bajar, porcentaje: 50}`.

---

## 📦 Instalación

Requisitos: **Python 3.11+**, [`uv`](https://docs.astral.sh/uv/), un micrófono y
una `GEMINI_API_KEY`.

```bash
git clone https://github.com/iam-oov/jeepy-ai.git
cd jeepy-ai

# Instalar dependencias
uv sync

# Configurar credenciales
cp .env.example .env   # luego editá .env con tus claves
```

### Variables de entorno principales

| Variable                        | Descripción                              | Default              |
| ------------------------------- | ---------------------------------------- | -------------------- |
| `GEMINI_API_KEY`                | Clave de Google Gemini (**requerida**)   | —                    |
| `GEMINI_MODEL`                  | Modelo de Gemini                         | `gemini-2.0-flash-exp` |
| `STT_ENGINE`                    | Motor STT a usar                         | `whisper_local`      |
| `STT_LANGUAGE`                  | Idioma de transcripción                  | `es-MX`              |
| `OPENAI_API_KEY`                | Solo si `STT_ENGINE=openai`              | —                    |
| `GOOGLE_CLOUD_CREDENTIALS_PATH` | Solo si `STT_ENGINE=google_cloud`        | —                    |
| `VOSK_MODEL_PATH`               | Solo si `STT_ENGINE=vosk`                | —                    |

Verificá tu configuración con:

```bash
uv run python config.py
```

---

## 🧠 El modelo KWS

El monitor espera un modelo TensorFlow Lite en `jeepy_kws_model_quantized.tflite`.
**Este archivo no está versionado** — hay que generarlo con los scripts de
`scripts/`:

```bash
# 1. Grabar muestras de la palabra clave
uv run python scripts/00_create-record-word.py

# 2. Entrenar el modelo KWS
uv run python scripts/01_train-kws-model.py

# 3. Convertir a TFLite cuantizado
uv run python scripts/02_convert_to_tflite.py
```

---

## 🚀 Uso

Con el modelo `.tflite` generado y el `.env` configurado:

```bash
uv run python r-pi/kws_monitor.py
```

1. Decí **"Jeepy"** cerca del micrófono.
2. Hablá tu comando (ej: _"enciende las luces"_).
3. El sistema graba hasta detectar ~1.5s de silencio.
4. El WAV se guarda en `captured_commands/`, se transcribe (STT) y se interpreta
   (Gemini). El resultado se imprime y, si está habilitado, se guarda en
   `transcriptions/` e `interpretations/`.

El monitor se autoconfigura según los módulos disponibles:
- **Pipeline completo**: `KWS → STT → Gemini → Acción` (si STT y Gemini cargan).
- **Pipeline parcial**: `KWS → STT` (si Gemini no está disponible).

---

## 🧪 Scripts de prueba

```bash
# Verificar configuración de STT
uv run python verify_stt.py

# Transcribir audio capturado (sin micrófono)
uv run python test_stt.py

# Probar el pipeline STT → Gemini
uv run python test_gemini.py

# Probar solo Gemini con comandos de ejemplo
uv run python gemini_engine.py
```

---

## 🗂️ Estructura del proyecto

```
jeepy-ai/
├── config.py              # Configuración centralizada (.env, validación)
├── stt_engine.py          # Motores STT + STTManager con fallback
├── gemini_engine.py       # GeminiEngine + VehicleController + JeepyAssistant
├── setup.py               # Asistente interactivo de configuración inicial
├── verify_stt.py          # Verificación de la integración STT
├── test_stt.py            # Prueba de transcripción sobre WAVs
├── test_gemini.py         # Prueba del pipeline STT → Gemini
├── r-pi/
│   └── kws_monitor.py     # Monitor KWS principal (orquesta todo el pipeline)
├── scripts/               # Grabar, entrenar y convertir el modelo KWS
├── captured_commands/     # WAVs capturados tras detectar "Jeepy"
├── planning/              # Notas de planificación y mejoras
├── ARCHITECTURE.txt       # Diagrama detallado de la arquitectura
└── pyproject.toml
```

---

## 🔮 Trabajo pendiente

- [ ] Control real del vehículo (CAN bus / GPIO) — hoy está simulado.
- [ ] TTS (Text-to-Speech) para respuestas por voz.
- [ ] Deploy y pruebas extendidas en la Raspberry Pi dentro del vehículo.
- [ ] Migrar de `tensorflow` a `tflite-runtime` en la RPi (ver nota en `kws_monitor.py`).
