"""
Jeepy AI - Módulo de Integración con Gemini
Gestiona la comunicación con Google Gemini para NLU y Tool-Use
"""

from typing import Optional, Dict, Any, List
import json
from config import Config


class GeminiEngine:
    """Motor de procesamiento de lenguaje natural con Gemini"""

    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY no configurada en .env")

        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.types = types
            self.model_name = Config.GEMINI_MODEL

            print(f"✅ Gemini configurado (modelo: {self.model_name})")

        except ImportError:
            raise ImportError("google-genai no instalado. Ejecuta: uv add google-genai")

    def process_command(
        self, command_text: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Procesa un comando de voz y extrae la intención y parámetros

        Args:
            command_text: Texto transcrito del comando
            context: Contexto adicional (ubicación, estado del vehículo, etc.)

        Returns:
            Dict con:
                - action: Acción a ejecutar
                - parameters: Parámetros de la acción
                - confidence: Nivel de confianza
                - raw_response: Respuesta completa de Gemini
        """

        system_prompt = """Eres el asistente de voz "Jeepy" para un vehículo Jeep.
Tu tarea es interpretar comandos de voz del usuario y convertirlos en acciones estructuradas.

ACCIONES DISPONIBLES:
1. control_ventana: Controla ventanas del vehículo
   - Parámetros: posicion (piloto|copiloto|trasera_izquierda|trasera_derecha|todas), accion (subir|bajar), porcentaje (0-100)
   
2. control_climatizacion: Controla aire acondicionado/calefacción
   - Parámetros: accion (encender|apagar|ajustar), temperatura (°C), velocidad (1-5)
   
3. control_luces: Controla luces del vehículo
   - Parámetros: tipo (delanteras|traseras|intermitentes|todas), accion (encender|apagar)
   
4. control_cerraduras: Controla puertas
   - Parámetros: accion (bloquear|desbloquear), puertas (todas|piloto|copiloto)
   
5. reproducir_musica: Control de música/radio
   - Parámetros: accion (reproducir|pausar|siguiente|anterior), fuente (radio|bluetooth|usb)
   
6. navegacion: Funciones de navegación
   - Parámetros: accion (iniciar|cancelar|ruta_alternativa), destino (string)
   
7. llamada_telefono: Realizar llamadas
   - Parámetros: accion (llamar|colgar), contacto (string)

FORMATO DE RESPUESTA (JSON):
{
  "action": "nombre_de_accion",
  "parameters": {
    "param1": "valor1",
    "param2": "valor2"
  },
  "confidence": 0.95,
  "natural_response": "Respuesta natural para el usuario"
}

Si el comando no es claro o no coincide con ninguna acción, devuelve:
{
  "action": "aclaracion_requerida",
  "parameters": {"question": "¿Pregunta de aclaración?"},
  "confidence": 0.0,
  "natural_response": "No entendí bien, ¿podrías repetir?"
}
"""

        user_message = f"Comando del usuario: '{command_text}'"
        if context:
            user_message += f"\n\nContexto: {json.dumps(context, indent=2)}"

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_message,
                config=self.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,  # Baja temperatura para respuestas más deterministas
                    response_mime_type="application/json",
                ),
            )

            result = json.loads(response.text)
            result["raw_response"] = response.text

            print(f"\n🤖 Gemini interpretó: {result['action']}")
            print(f"   Confianza: {result.get('confidence', 0):.2f}")

            return result

        except json.JSONDecodeError as e:
            print(f"❌ Error parseando respuesta JSON de Gemini: {e}")
            print(f"   Respuesta raw: {response.text}")
            return None
        except Exception as e:
            print(f"❌ Error procesando comando con Gemini: {e}")
            return None

    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Genera una respuesta conversacional simple

        Args:
            prompt: Texto de entrada

        Returns:
            Respuesta generada
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.types.GenerateContentConfig(temperature=0.7),
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ Error generando respuesta: {e}")
            return None


class VehicleController:
    """Controlador de funciones del vehículo (simulado)"""

    def execute_action(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una acción en el vehículo

        Args:
            action: Nombre de la acción
            parameters: Parámetros de la acción

        Returns:
            Resultado de la ejecución
        """
        print(f"\n🚗 Ejecutando: {action}")
        print(f"   Parámetros: {json.dumps(parameters, indent=2)}")

        # SIMULACIÓN - Aquí iría la integración real con CAN bus / GPIO
        simulated_actions = {
            "control_ventana": self._control_ventana,
            "control_climatizacion": self._control_climatizacion,
            "control_luces": self._control_luces,
            "control_cerraduras": self._control_cerraduras,
            "reproducir_musica": self._reproducir_musica,
            "navegacion": self._navegacion,
            "llamada_telefono": self._llamada_telefono,
        }

        handler = simulated_actions.get(action)
        if handler:
            return handler(parameters)
        else:
            return {"success": False, "error": f"Acción desconocida: {action}"}

    def _control_ventana(self, params: Dict) -> Dict:
        posicion = params.get("posicion", "piloto")
        accion = params.get("accion", "bajar")
        porcentaje = params.get("porcentaje", 100)
        print(f"   ✓ Ventana {posicion}: {accion} {porcentaje}%")
        return {
            "success": True,
            "message": f"Ventana {posicion} {accion} {porcentaje}%",
        }

    def _control_climatizacion(self, params: Dict) -> Dict:
        accion = params.get("accion", "ajustar")
        temp = params.get("temperatura", 22)
        print(f"   ✓ Clima: {accion} a {temp}°C")
        return {"success": True, "message": f"Temperatura ajustada a {temp}°C"}

    def _control_luces(self, params: Dict) -> Dict:
        tipo = params.get("tipo", "delanteras")
        accion = params.get("accion", "encender")
        print(f"   ✓ Luces {tipo}: {accion}")
        return {"success": True, "message": f"Luces {tipo} {accion}"}

    def _control_cerraduras(self, params: Dict) -> Dict:
        accion = params.get("accion", "bloquear")
        puertas = params.get("puertas", "todas")
        print(f"   ✓ Cerraduras {puertas}: {accion}")
        return {"success": True, "message": f"Puertas {puertas} {accion}"}

    def _reproducir_musica(self, params: Dict) -> Dict:
        accion = params.get("accion", "reproducir")
        fuente = params.get("fuente", "bluetooth")
        print(f"   ✓ Música: {accion} desde {fuente}")
        return {"success": True, "message": f"Reproduciendo desde {fuente}"}

    def _navegacion(self, params: Dict) -> Dict:
        accion = params.get("accion", "iniciar")
        destino = params.get("destino", "")
        print(f"   ✓ Navegación: {accion} -> {destino}")
        return {"success": True, "message": f"Navegación a {destino}"}

    def _llamada_telefono(self, params: Dict) -> Dict:
        accion = params.get("accion", "llamar")
        contacto = params.get("contacto", "")
        print(f"   ✓ Teléfono: {accion} {contacto}")
        return {"success": True, "message": f"Llamando a {contacto}"}


class JeepyAssistant:
    """Asistente completo que integra STT + Gemini + Control"""

    def __init__(self):
        self.gemini = GeminiEngine()
        self.controller = VehicleController()

    def process_audio_command(self, transcribed_text: str) -> Dict[str, Any]:
        """
        Procesa un comando completo: texto -> interpretación -> ejecución

        Args:
            transcribed_text: Texto del comando ya transcrito por STT

        Returns:
            Resultado completo del procesamiento
        """
        print(f"\n{'=' * 60}")
        print(f"🎤 Comando recibido: '{transcribed_text}'")
        print(f"{'=' * 60}")

        # 1. Interpretar con Gemini
        interpretation = self.gemini.process_command(transcribed_text)

        if not interpretation:
            return {
                "success": False,
                "error": "No se pudo interpretar el comando",
                "response": "Lo siento, no entendí tu comando.",
            }

        # 2. Ejecutar acción (si no es aclaración)
        if interpretation["action"] != "aclaracion_requerida":
            execution_result = self.controller.execute_action(
                interpretation["action"], interpretation.get("parameters", {})
            )
        else:
            execution_result = {"success": False, "needs_clarification": True}

        # 3. Compilar resultado
        result = {
            "success": execution_result.get("success", False),
            "action": interpretation["action"],
            "parameters": interpretation.get("parameters", {}),
            "confidence": interpretation.get("confidence", 0),
            "response": interpretation.get("natural_response", "Listo."),
            "execution": execution_result,
        }

        print(f"\n💬 Respuesta: {result['response']}")
        print(f"{'=' * 60}\n")

        return result


if __name__ == "__main__":
    # Test del módulo
    from config import Config

    Config.print_status()

    try:
        assistant = JeepyAssistant()
        print("\n✅ Jeepy Assistant inicializado\n")

        # Ejemplos de comandos
        test_commands = [
            "Baja la ventana del piloto un 50%",
            "Enciende el aire acondicionado a 20 grados",
            "Bloquea todas las puertas",
            "Reproduce música desde bluetooth",
        ]

        for cmd in test_commands:
            result = assistant.process_audio_command(cmd)

    except Exception as e:
        print(f"\n❌ Error: {e}")
