from __future__ import annotations

from typing import Any, Dict, List, Text, Optional

import requests

from rasa.engine.graph import GraphComponent, ExecutionContext
from rasa.engine.storage.resource import Resource
from rasa.engine.storage.storage import ModelStorage
from rasa.engine.recipes.default_recipe import DefaultV1Recipe

from rasa.shared.nlu.training_data.message import Message
from rasa.shared.nlu.training_data.training_data import TrainingData


@DefaultV1Recipe.register(
    component_types=[DefaultV1Recipe.ComponentType.MESSAGE_FEATURIZER],
    is_trainable=False,
)
class TextNormalizer(GraphComponent):
    """Normaliza el texto llamando al embedding-service ANTES del NLU."""

    @staticmethod
    def get_default_config() -> Dict[Text, Any]:
        return {
            "url": "http://embedding-service:9000/api/normalize",
            "timeout": 1.5,
        }

    def __init__(self, config: Dict[Text, Any]) -> None:
        self._config = {**self.get_default_config(), **config}
        self.url: str = self._config["url"]
        self.timeout: float = float(self._config["timeout"])

    @classmethod
    def create(
        cls,
        config: Dict[Text, Any],
        model_storage: ModelStorage,
        resource: Resource,
        execution_context: ExecutionContext,
    ) -> "TextNormalizer":
        return cls(config)

    # 🔹 Rasa la exige para el entrenamiento
    def process_training_data(self, training_data: TrainingData) -> TrainingData:
        self._normalize_messages(list(training_data.training_examples))
        return training_data

    # 🔹 Rasa la usa en inferencia
    def process(self, messages: List[Message]) -> List[Message]:
        self._normalize_messages(messages)
        return messages

    def train(self, training_data: TrainingData) -> Resource:
        # No entrena nada, solo transforma mensajes
        return Resource("text_normalizer")

    # ---------- interno ----------
    def _normalize_messages(self, messages: List[Message]) -> None:
        for msg in messages:
            text: Optional[Text] = msg.get("text")
            if not text:
                continue

            try:
                resp = requests.post(
                    self.url,
                    json={"text": text},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()

                normalized = (
                    data.get("normalized")
                    or data.get("normalized_text")
                    or data.get("text")
                    or text
                )

                msg.set("text", normalized, add_to_output=True)
            except Exception:
                msg.set("text", text, add_to_output=True)
