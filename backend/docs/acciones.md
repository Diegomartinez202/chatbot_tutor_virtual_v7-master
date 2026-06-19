1️⃣ Código listo para pegar en acciones_soporte.py

👉 Pega este bloque al final de actions/acciones_soporte.py (o donde tengas las demás acciones de soporte).

Si arriba del archivo no tienes estas imports, agrégalas también:

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction, EventType
from rasa_sdk.types import DomainDict

from backend.utils.logging import get_logger  # si ya tienes logger, no dupliques esta línea
logger = get_logger(__name__)

🔥 1. ActionPQRSLLM → action_pqrs_llm
class ActionPQRSLLM(Action):
    """Genera y/o refina una PQRS usando el LLM central.

    Esta acción:
    - Le explica al usuario que se va a estructurar su PQRS.
    - Luego delega en `action_handle_with_llm` para que genere el texto final.
    """

    def name(self) -> Text:
        return "action_pqrs_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        logger.info("ActionPQRSLLM ejecutada.")

        dispatcher.utter_message(
            text=(
                "📝 Perfecto, voy a ayudarte a redactar tu PQRS (petición, queja, "
                "reclamo o sugerencia) de forma clara y respetuosa.\n\n"
                "Por favor cuéntame, con tus palabras, qué quieres reportar, "
                "y luego ajustaré el mensaje con lenguaje formal para que puedas "
                "enviarlo por los canales oficiales. ✅"
            )
        )

        # Dejamos que el LLM central procese el siguiente turno con todo el contexto.
        return [FollowupAction("action_handle_with_llm")]

🔥 2. ActionPreguntasFrecuentesLLM → action_preguntas_frecuentes_llm

Esta acción sirve para intents como faq_general, faq_tecnico, faq_academico (cuando los tengas listados en domain+nlu).

class ActionPreguntasFrecuentesLLM(Action):
    """Responde preguntas frecuentes (FAQ) usando el LLM central.

    La idea es que el bot:
    - Reconozca que es una duda tipo FAQ.
    - Use el LLM para dar una respuesta clara, corta y contextualizada a Zajuna.
    """

    def name(self) -> Text:
        return "action_preguntas_frecuentes_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        logger.info("ActionPreguntasFrecuentesLLM ejecutada.")

        dispatcher.utter_message(
            text=(
                "❓ Veo que tienes una duda frecuente sobre la plataforma o el proceso.\n\n"
                "Voy a darte una explicación clara y resumida basada en la información "
                "académica y de soporte de Zajuna. Si después quieres más detalle, "
                "podemos profundizar o escalar a soporte humano. 🙂"
            )
        )

        # Delegar al LLM genérico que ya maneja el contexto y memoria.
        return [FollowupAction("action_handle_with_llm")]

🔥 3. ActionSoporteTecnicoLLM → action_soporte_tecnico_llm

Esta acción es para cuando el intent entra claramente como “soporte técnico” y quieres que el LLM ayude a diagnosticar/explicar antes de crear ticket, PQRS, etc.

class ActionSoporteTecnicoLLM(Action):
    """Asistente LLM especializado en soporte técnico de la plataforma Zajuna.

    Uso típico:
    - El usuario describe un problema técnico.
    - El bot hace algunas preguntas / sugerencias guiadas por el LLM.
    - Después, si hace falta, se puede crear ticket o PQRS con otras acciones.
    """

    def name(self) -> Text:
        return "action_soporte_tecnico_llm"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[EventType]:
        logger.info("ActionSoporteTecnicoLLM ejecutada.")

        dispatcher.utter_message(
            text=(
                "🛠️ Vamos a revisar tu problema técnico.\n\n"
                "Te haré algunas preguntas y te daré pasos de verificación basados en "
                "buenas prácticas de soporte (navegador, caché, conexión, permisos, etc.). "
                "Si al final el problema continúa, podemos dejarlo registrado en soporte "
                "para que un equipo humano lo revise. 🔍"
            )
        )

        # Usamos el LLM existente para guiar el diagnóstico técnico.
        return [FollowupAction("action_handle_with_llm")]

2️⃣ Qué más debes hacer (rápido)

Asegurar que las acciones estén en domain.yml en la sección actions::

actions:
  - action_pqrs_llm
  - action_preguntas_frecuentes_llm
  - action_soporte_tecnico_llm


Agregar reglas o stories que las llamen, por ejemplo (ejemplo rápido en rules):

- rule: PQRS con LLM
  steps:
    - intent: registrar_pqrs
    - action: action_pqrs_llm

- rule: FAQs con LLM
  steps:
    - intent: faq_general
    - action: action_preguntas_frecuentes_llm

- rule: Soporte técnico guiado por LLM
  steps:
    - intent: soporte_tecnico
    - action: action_soporte_tecnico_llm