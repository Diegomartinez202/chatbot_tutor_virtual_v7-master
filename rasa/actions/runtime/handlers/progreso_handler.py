from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

from ...runtime.api_client import call
from .base_handler import safe_backend_response

def handler(dispatcher: CollectingDispatcher, tracker: Tracker, payload=None):

    user_id = tracker.sender_id

    data = safe_backend_response(
    call(
        tracker,
        f"/api/progreso/{user_id}",
        method="GET",
        default={}
    )
)

    porcentaje = data.get("progreso", 0)



    dispatcher.utter_message(text=f"📊 Progreso actual: {porcentaje}%")

    return data