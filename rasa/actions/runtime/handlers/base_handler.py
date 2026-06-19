from typing import Any, Dict

from ...runtime.api_client import call
from ...core.llm_engine import run_llm


def safe_get(data: Dict[str, Any], key: str, default=None):
    if not isinstance(data, dict):
        return default
    return data.get(key, default)

def safe_backend_response(data: Any):

    if not data:
        return {}

    if not isinstance(data, dict):
        return {}

    return data

def send_lines(dispatcher, title, items):

    text = [title]

    text.extend(items)

    dispatcher.utter_message(
        text="\n".join(text)
    )