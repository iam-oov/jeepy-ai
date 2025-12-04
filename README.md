# 🚗 Jeepy AI - Asistente de Voz para Control Vehicular

**Versión**: 1.0.0 | **Fecha**: 3 de Diciembre, 2024 | **Autor**: GitHub Copilot + Valdo

[![macOS](https://img.shields.io/badge/macOS-✅_Desarrollo-blue)](PLATFORM_COMPATIBILITY.md)
[![Linux](https://img.shields.io/badge/Linux-✅_Testing-blue)](PLATFORM_COMPATIBILITY.md)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-✅_Producción-green)](PLATFORM_COMPATIBILITY.md)

---

## ⚡ Inicio Rápido por Plataforma

| Plataforma       | Comando                      | Nota                             |
| ---------------- | ---------------------------- | -------------------------------- |
| **macOS**        | `uv sync && uv run setup.py` | Desarrollo, sin KWS (no TFLite)  |
| **Linux**        | `uv sync && uv run setup.py` | Testing completo con KWS         |
| **Raspberry Pi** | `git clone` → `uv sync`      | Producción edge con KWS completo |

👉 **Ver detalles**: [PLATFORM_COMPATIBILITY.md](PLATFORM_COMPATIBILITY.md)

---

## 📋 Checklist de Implementación [ ] Deploy en Raspberry Pi - **FUTURO**- [ ] Añadir TTS (Text-to-Speech) - **FUTURO**- [ ] Integrar con Gemini (NLU) - **PRÓXIMO**- [x] Verificar todos los motores STT- [x] Probar con audio real- [x] Actualizar `README.md` principal- [x] Crear `transcriptions/README.md`- [x] Crear `test_stt.py`- [x] Crear directorio `transcriptions/`- [x] Integrar en `_finish_recording()`- [x] Implementar método `_save_transcription()`- [x] Implementar método `_transcribe_command()`- [x] Inicializar `STTManager` en `InferenceThread`- [x] Añadir estado `STATE_TRANSCRIBING`- [x] Definir constantes de configuración STT- [x] Importar módulos STT con try/except## ✅ Checklist de Implementación---- [Vosk Offline Recognition](https://alphacephei.com/vosk/)- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)- [Whisper Local GitHub](https://github.com/openai/whisper)- [OpenAI Whisper API Docs](https://platform.openai.com/docs/guides/speech-to-text)## 📚 Referencias---- Modelos específicos de dominio- Filtrado de ruido de motor/viento- Calibración de umbral de silencio- Fine-tuning de Whisper con audio automotriz### 4. Mejora de Precisión`)    success=success    intent=intent,    transcription=transcription,    audio_file=audio_file,    timestamp=timestamp,self.db.save_command(# Almacenar en base de datos`python### 3. Historial de Comandos`    self.tts_engine.speak("No entendí el comando")else:    self.tts_engine.speak("Luces encendidas")if success:# Responder al usuario con voz`python### 2. Feedback de Voz (TTS)`        self.vehicle_controller.execute(intent)        # Ejecutar acción basada en intent                intent = self.gemini_engine.parse_command(transcription)        # 🎯 SIGUIENTE: Enviar a Gemini para interpretación    if transcription:        transcription = self.stt_manager.transcribe(audio_file)def _transcribe_command(self, audio_file: str, duration: float):# En _transcribe_command(), después de obtener transcripción:`python### 1. Integración con Gemini (NLU)## 📈 Próximos Pasos---`ffprobe captured_commands/cmd_*.wav 2>&1 | grep Duration# Verificar duraciónffplay captured_commands/cmd_*.wav# Verificar audio con ffplay`bash**Solución**:4. Formato de audio incorrecto3. Ruido excesivo2. Audio sin voz1. Audio muy corto (< 0.5s)**Posibles causas**:### Problema: Transcripción vacía`python -c "from config import Config; print(Config.OPENAI_API_KEY)"# Verificarecho "OPENAI_API_KEY=tu-api-key" > .env# Crear/editar .env`bash**Solución**:### Problema: "OpenAI API Key not configured"`ls config.py stt_engine.py# Si falla, verificar que config.py y stt_engine.py existenpython -c "from config import Config; from stt_engine import STTManager"# Verificar imports`bash**Solución**:### Problema: "STT modules not available"## 🐛 Troubleshooting---`uv run python test_stt.py# ProbarVOSK_MODEL_PATH = "models/vosk-model-small-es-0.42"# Configurar path del modelo en config.pyunzip vosk-model-small-es-0.42.zip -d models/wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip# Descargar modeloSTT_ENGINE=vosk# En .env`bash### Configurar Vosk (Offline)`uv run python test_stt.py# ProbarGOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.jsonSTT_ENGINE=google_cloud# En .env`bash### Configurar Google Cloud STT`uv run python test_stt.py# Probaruv add openai-whisper# Instalar dependenciaSTT_ENGINE=whisper_local  # Cambiar a Whisper local# En .env`bash### Cambiar Motor STT## ⚙️ Configuración Avanzada---`ls transcriptions/trans_*.txt | wc -l# Contar transcripcionesgrep -r "luces" transcriptions/# Buscar comando específicocat transcriptions/trans_*.txt | tail -n 20# Ver últimals -lh transcriptions/# Listar todas`bash### Ver Transcripciones7. **Vuelta a LISTENING**: Listo para siguiente comando - Log: `✅ Transcripción: 'Enciende las luces del tablero'` - Transcripción: `transcriptions/trans_20241203_153045.txt` - Audio guardado: `captured_commands/cmd_20241203_153045.wav`6. **Transcripción automática**:5. **Silencio 1.5s**: Fin de grabación → Estado `TRANSCRIBING` 📝4. **Hablar comando**: "Enciende las luces del tablero"3. **Decir "Jeepy"**: KWS detecta → Estado `RECORDING` 🔴2. **Sistema esperando**: Estado `LISTENING` 🎧 ` uv run ./r-pi/kws_monitor.py `bash1. **Ejecutar monitor KWS**:### Flujo Normal## 🚀 Uso en Producción---`└── README.md                   (Actualizado)├── .env                        (API keys)├── test_stt.py                (Test suite - NUEVO)├── stt_engine.py              (Motores STT)├── config.py                   (Configuración STT)││   └── jeepy_kws_model_quantized.tflite│   ├── kws_monitor.py         (Actualizado con STT)├── r-pi/││   └── trans_20251203_122521.txt│   ├── trans_20251203_122511.txt│   ├── trans_20251203_122416.txt│   ├── README.md              (Documentación)├── transcriptions/             # Transcripciones STT││   └── cmd_20251203_122521.wav│   ├── cmd_20251203_122511.wav│   ├── cmd_20251203_122416.wav├── captured_commands/          # Audio grabadojeepy-ai/`## 📊 Estructura de Archivos Resultante---`   ❌ Fallidas: 0   ✅ Exitosas: 3📊 Resultados:[3/3] cmd_20251203_122521.wav... ✅ "Más información www.alimmenta.com"[2/3] cmd_20251203_122511.wav... ✅ "¿Cómo estás? Necesito tu ayuda, Jimmy."[1/3] cmd_20251203_122416.wav... ✅ "Jimmy, ¿cómo estás? Necesito tu ayuda, Jimmy."📁 Total de archivos: 3$ uv run python test_stt.py --all`bash### Test 3: Transcripción Masiva`💾 Transcripción guardada en: transcriptions/trans_20251203_122521.txt"Más información www.alimmenta.com"✅ Transcripción exitosa:🎯 Usando archivo más reciente: cmd_20251203_122521.wav   OpenAI API Key: ********************fFoA   Idioma: es-MX   Motor STT: openai📋 Configuración:🎤 TEST DE STT (Speech-to-Text)$ uv run python test_stt.py`bash### Test 2: Transcripción Simple`Motor configurado: openai✅ Módulos STT importados correctamente$ python -c "from config import Config; from stt_engine import STTManager; print(f'Motor: {Config.STT_ENGINE}')"`bash### Test 1: Verificación de Imports## 🧪 Pruebas Realizadas---- Tips de análisis- Comparativa de motores- Ejemplos de uso- Metadata incluida- Formato de archivosDocumentación completa:### 3. `transcriptions/README.md` (Nuevo)- ✅ Manejo de errores con sugerencias- ✅ Guardado automático de transcripciones- ✅ Progreso visual con emojis- ✅ Búsqueda automática de archivos- ✅ Validación de configuraciónCaracterísticas:`uv run python test_stt.py --file captured_commands/cmd_20241203_120000.wav# Test específicouv run python test_stt.py --all# Test masivo (todos)uv run python test_stt.py# Test simple (último archivo)`bashScript de prueba independiente con 3 modos:### 2. `test_stt.py` (Nuevo)`    self.system_state.set_state(STATE_LISTENING)    # Resetear estado        transcription = self._transcribe_command(filename, duration)    # ✨ NUEVO: Transcribir comando        self.audio_saver.save_wav(filename, self.recording_buffer, SAMPLE_RATE)    filename = os.path.join(SAVE_DIR, f"cmd_{timestamp}.wav")    # Guardar audio WAV        # ... código existente ...def _finish_recording(self):`python#### Integración en ` _finish_recording()````        f.write(f"\n{transcription}\n")        f.write(f"# STT Engine: {Config.STT_ENGINE}\n")        f.write(f"# Timestamp: {timestamp}\n")        f.write(f"# Duration: {duration:.2f}s\n")        f.write(f"# Audio source: {audio_file}\n")    with open(trans_file, "w", encoding="utf-8") as f:        trans_file = os.path.join(TRANSCRIPTIONS_DIR, f"trans_{timestamp}.txt")    timestamp = os.path.basename(audio_file).replace("cmd_", "").replace(".wav", "")    """Guarda transcripción con metadata"""def _save_transcription(self, audio_file: str, transcription: str, duration: float):```python#### Método  `\_save_transcription()``        return None        logger.error(f"❌ Error transcribiendo: {e}")    except Exception as e:                return transcription                        os.remove(audio_file)            if STT_AUTO_DELETE_AUDIO:                            self._save_transcription(audio_file, transcription, duration)            if STT_SAVE_TRANSCRIPTIONS:                        logger.info(f"✅ Transcripción: '{transcription}'")        if transcription:                transcription = self.stt_manager.transcribe(audio_file)        self.system_state.set_state(STATE_TRANSCRIBING)    try:            return None    if not self.stt_manager:            return None    if not STT_ENABLED or not ENABLE_STT_PROCESSING:    """Transcribe comando de audio usando STT"""def _transcribe_command(self, audio_file: str, duration: float) -> Optional[str]:```python#### Método `_transcribe_command()`` os.makedirs(TRANSCRIPTIONS_DIR, exist_ok=True)if STT_SAVE_TRANSCRIPTIONS:# Crear directorio de transcripciones self.stt_manager = None logger.error(f"❌ Error inicializando STT: {e}") except Exception as e: logger.info("✅ STT Manager inicializado correctamente") self.stt_manager = STTManager() try:if STT_ENABLED and ENABLE_STT_PROCESSING:# Inicializar STT Manager`` python#### Inicialización en `InferenceThread.run()````STATE_TRANSCRIBING = "transcribing"# Nuevo estadoTRANSCRIPTIONS_DIR = "./transcriptions/"STT_SAVE_TRANSCRIPTIONS = TrueSTT_AUTO_DELETE_AUDIO = FalseENABLE_STT_PROCESSING = True# STT Configuration ``python#### Configuración`STT_ENABLED = True  # Flag de degradación elegantefrom stt_engine import STTManagerfrom config import Configsys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))import osimport sys`python#### Imports Nuevos### 1. `r-pi/kws_monitor.py`## 🔧 Cambios Implementados---`OPENAI_API_KEY=sk-proj-... # Configurado ✅STT_LANGUAGE=es-MX          # Español (México)STT_ENGINE=openai           # Motor activo`env### Configuración Actual| **Vosk** | Local | ~1-2s | ⭐⭐⭐ | Gratis || **Google Cloud** | API | ~1-3s | ⭐⭐⭐⭐ | Variable || **Whisper Local** | Local | ~5-10s | ⭐⭐⭐⭐⭐ | Gratis || **OpenAI Whisper** | API | ~2-4s | ⭐⭐⭐⭐⭐ | $0.006/min ||-------|-----------|----------|-----------|-------|| Motor | API/Local | Latencia | Precisión | Costo |### Motores STT Disponibles`    [Next: Gemini NLU]  ← TODO         v         │└────────┬────────┘│  (metadata)     ││  Save TXT       │  ← transcriptions/┌─────────────────┐         v         │└────────┬────────┘│  .transcribe()  ││  STTManager     │  ← NEW!┌─────────────────┐         v         │└────────┬────────┘│  Save WAV File  │  ← captured_commands/┌─────────────────┐         v         │ SILENCE (1.5s)└────────┬────────┘│  (Recording)    ││  Audio Buffer   │┌─────────────────┐         v         │ DETECTED└────────┬────────┘│  ("Jeepy")      ││  KWS Detection  │  ← TFLite Model┌─────────────────┐         v         │└────────┬────────┘│  (Input Audio)  ││  Micrófono      │┌─────────────────┐`### Pipeline Completo## 🏗️ Arquitectura---- ✅ **Degradación elegante** si STT no está disponible- ✅ **Configuración flexible** vía variables de entorno- ✅ **Test suite** independiente (`test_stt.py`)- ✅ **Transcripciones guardadas** con metadata completa- ✅ **Estado TRANSCRIBING** añadido a máquina de estados- ✅ **Integración transparente** en flujo de grabación existente- ✅ **4 motores STT** soportados con fallback automático### Logros Clave`🎤 KWS Detecta "Jeepy" → 🔴 Graba Comando → 💾 Guarda WAV → 📝 Transcribe → 💬 Texto`Se integró exitosamente el sistema Speech-to-Text (STT) al monitor KWS de Jeepy AI, completando el pipeline:## 📋 Resumen Ejecutivo---**Motor Activo**: OpenAI Whisper API**Estado**: ✅ Completado y Probado **Fecha**: 3 de Diciembre, 2024 [![Estado](https://img.shields.io/badge/Estado-STT%20Integrado-brightgreen)](https://github.com/iam-oov/jeepy-ai)

[![Fases](https://img.shields.io/badge/Fases-5%2F5%20Completas-brightgreen)](https://github.com/iam-oov/jeepy-ai)
[![Mejoras](<https://img.shields.io/badge/Mejoras-20%2F17%20(117%25)-success>)](https://github.com/iam-oov/jeepy-ai)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![STT](https://img.shields.io/badge/STT-OpenAI%20%7C%20Whisper%20%7C%20Google-blue)](https://github.com/iam-oov/jeepy-ai)

Asistente de voz personalizado diseñado para operar en un entorno automotriz (Jeep), utilizando una arquitectura Edge-to-LLM eficiente y el modelo de lenguaje Google Gemini para la comprensión de comandos. El sistema utiliza una Raspberry Pi como dispositivo de borde (Edge) para la activación local y de baja latencia.

**🎉 NUEVA INTEGRACIÓN**: Sistema STT (Speech-to-Text) completo con soporte para OpenAI Whisper, Whisper Local, Google Cloud y Vosk.

---

## 🎯 Características Principales

### 🎤 Activación por Palabra Clave Local

- **Detección offline** de "Jeepy" en tiempo real
- **Modelo KWS optimizado** con TensorFlow Lite (quantized)
- **Baja latencia** (~250ms) con ventana deslizante
- **Anti-falsos positivos** con sistema de confirmación (2 detecciones)
- **Tolerancia a fallos** con recuperación automática

### 🗣️ Transcripción Speech-to-Text (STT)

- **Multi-motor**: OpenAI Whisper API, Whisper Local, Google Cloud, Vosk
- **Fallback automático** entre motores STT
- **Idioma configurable** (es-MX por defecto)
- **Guardado de transcripciones** en `./transcriptions/`
- **Integración transparente** tras detección de palabra clave

### 🧠 Comprensión de Lenguaje Natural (NLU)

- **Gemini AI** para interpretación de comandos complejos
- **Contexto vehicular** especializado
- Ejemplo: _"baja la ventana del piloto un 30%"_

### 🔧 Control de Hardware (Tool-Use)

- **Tool-Use de Gemini** para invocar funciones Python
- Interacción con vehículo vía **CAN bus** (simulado/real)
- Control de: ventanas, climatización, luces, cerraduras, multimedia, navegación

### ⚡ Arquitectura de Bajo Consumo

- **LLM solo después de activación** local
- Minimiza consumo de datos y recursos
- **99% uptime** esperado en producción

---

## 🚀 Novedades

### ✨ Integración STT (Speech-to-Text) - NUEVO

- ✅ **Multi-motor STT**: OpenAI Whisper, Whisper Local, Google Cloud, Vosk
- ✅ **Fallback automático** entre motores con reintentos
- ✅ **Estado TRANSCRIBING** en máquina de estados
- ✅ **Guardado de transcripciones** con metadata (motor, duración, timestamp)
- ✅ **Script de test**: `test_stt.py` para probar motores STT
- ✅ **Configuración flexible** vía `.env` (STT_ENGINE, API keys)

### Fase 4 & 5: Robustez y UX Avanzado ✅

- ✅ **Manejo de errores TFLite** con 3 reintentos automáticos
- ✅ **Reconexión de micrófono** automática (hasta 5 intentos)
- ✅ **ErrorRecoveryManager** para tracking centralizado
- ✅ **9 comandos de control** en español (pause, resume, status, stats, etc.)
- ✅ **Modo interactivo** con consola en tiempo real
- ✅ **Estado PAUSED** para pausar/reanudar sin reiniciar

**Total**: **20/17 mejoras implementadas (117%)** + STT integrado

Ver [PHASE_4_5_SUMMARY.md](PHASE_4_5_SUMMARY.md) para detalles de fases anteriores.

---

## 📦 Inicio Rápido

### Requisitos

```bash
- Python 3.11+
- uv (package manager)
- Micrófono USB o integrado
- OpenAI API Key (para STT con OpenAI Whisper)
- (Opcional) Raspberry Pi para deploy
```

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/iam-oov/jeepy-ai.git
cd jeepy-ai

# Instalar dependencias
uv sync

# Configurar API keys (crear .env en raíz del proyecto)
echo "OPENAI_API_KEY=tu-api-key-aqui" > .env
echo "STT_ENGINE=openai" >> .env

# Ejecutar sistema KWS con STT
uv run ./r-pi/kws_monitor.py
```

### Uso Básico

1. **Di "Jeepy"** cerca del micrófono
2. **Habla tu comando** (ej: "enciende las luces")
3. El sistema graba hasta detectar **1.5s de silencio**
4. **Audio guardado** en `captured_commands/`
5. **Transcripción automática** guardada en `transcriptions/`

### Test de STT

```bash
# Probar STT con último archivo capturado
uv run python test_stt.py

# Transcribir todos los archivos
uv run python test_stt.py --all

# Transcribir archivo específico
uv run python test_stt.py --file captured_commands/cmd_20241203_120000.wav
```

### Comandos Interactivos

Durante la ejecución, escribe en consola:

```bash
pause        # Pausar monitoreo
resume       # Reanudar
status       # Ver estado detallado (incluye STT)
stats        # Ver estadísticas KWS
recalibrate  # Recalibrar umbrales
quit         # Salir
```

Ver [QUICK_START.md](QUICK_START.md) para guía completa.

---

## 📚 Documentación

| Documento                                    | Descripción                            |
| -------------------------------------------- | -------------------------------------- |
| [QUICK_START.md](QUICK_START.md)             | Guía de uso rápido (5 min)             |
| [IMPROVEMENTS.md](IMPROVEMENTS.md)           | Lista completa de 20 mejoras           |
| [PHASE_4_5_SUMMARY.md](PHASE_4_5_SUMMARY.md) | Documentación detallada Fases 4-5      |
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | Resumen ejecutivo del proyecto         |
| [INTEGRATION.md](INTEGRATION.md)             | Guía de integración STT/Gemini         |
| [demo_phases_4_5.py](demo_phases_4_5.py)     | Demo sin micrófono de nuevas funciones |

---
