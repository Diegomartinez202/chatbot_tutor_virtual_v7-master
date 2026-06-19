from typing import Any, Dict, Text

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict


class ValidateFeedbackForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_feedback_form"

    async def validate_feedback_tipo(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        opciones = [
            "sugerencia",
            "queja",
            "felicitacion",
            "error",
        ]

        valor = str(slot_value).lower().strip()

        if valor not in opciones:

            dispatcher.utter_message(
                text=(
                    "Selecciona un tipo válido: "
                    "sugerencia, queja, felicitacion o error."
                )
            )

            return {"feedback_tipo": None}

        return {"feedback_tipo": valor}