# Comandos Capturados

Este directorio almacena los comandos de voz capturados por el sistema KWS después de detectar la palabra clave "Jeepy".

## Formato de Archivos

- **Nombre**: `cmd_YYYYMMDD_HHMMSS.wav`
- **Formato**: WAV, 16kHz mono, 16-bit PCM
- **Contenido**:
  - 2.5 segundos de audio previo a la detección (pre-buffer)
  - Audio capturado hasta detectar 1.5 segundos de silencio
  - Máximo 10 segundos por seguridad

## Estructura del Audio

```
[2.5s Pre-buffer] + [Comando del Usuario] + [Detección de Silencio]
    ↓                      ↓                         ↓
  "Jeepy"           "Baja la ventana..."      [silencio 1.5s]
```

## Uso

Estos archivos están listos para ser procesados por:

1. STT (Speech-to-Text) - Whisper, Vosk, Google Cloud Speech
2. LLM (Gemini) para interpretación de comandos
3. Sistema de control vehicular
