import httpx
import os

RASA_REST_URL = os.getenv("RASA_REST_URL", "http://localhost:5005/webhooks/rest/webhook")

async def send_to_rasa(sender: str, message: str, metadata: dict | None = None):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(RASA_REST_URL, json={
            "sender": sender,
            "message": message,
            "metadata": metadata or {}
        })
        r.raise_for_status()
        return r.json()
