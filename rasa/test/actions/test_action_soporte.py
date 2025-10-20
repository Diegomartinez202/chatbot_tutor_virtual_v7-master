from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from actions.actions import ActionEnviarSoporte

def test_action_enviar_soporte():
    action = ActionEnviarSoporte()
    dispatcher = CollectingDispatcher()
    tracker = Tracker(
        sender_id="test_user",
        slots={
            "nombre": "Daniel",
            "email": "daniel@example.com",
            "mensaje": "No funciona el curso"
        },
        events=[],
        paused=False,
        latest_message={},
        followup_action=None,
        active_loop={},
        latest_action_name=None
    )
    domain = {}
    events = action.run(dispatcher, tracker, domain)

    # ✅ Aseguramos que la acción devuelve una lista de eventos (ej. SlotSet)
    assert isinstance(events, list)