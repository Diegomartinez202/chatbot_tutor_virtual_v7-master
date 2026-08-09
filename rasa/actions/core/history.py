from __future__ import annotations

from typing import List

from rasa_sdk import Tracker

from .nlp_utils import anonymize_text


def build_history(
    tracker: Tracker,
    max_events: int = 20,
    max_lines: int = 6,
) -> str:
    """
    Construye un historial corto de conversación para
    proporcionar contexto al LLM.

    Se eliminan comandos de Rasa (/intent) y únicamente
    se conservan los últimos turnos relevantes.
    """

    history: List[str] = []

    raw_events = tracker.events or []

    for event in raw_events[-max_events:]:

        if not isinstance(event, dict):
            continue

        event_type = event.get("event")

        if event_type == "user":

            text = anonymize_text(
                event.get("text", "")
            )

            if text and not text.startswith("/"):
                history.append(
                    f"Usuario: {text}"
                )

        elif event_type == "bot":

            text = (
                event.get("text", "")
                or ""
            ).strip()

            if text:
                history.append(
                    f"Bot: {text}"
                )

    history = history[-max_lines:]

    return "\n".join(history)