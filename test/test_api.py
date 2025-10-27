# tests/test_api.py
import os
import requests
import pytest

PROXY_BASE = os.getenv("PROXY_BASE", "http://localhost:8080").rstrip("/")
BACKEND    = os.getenv("BACKEND", "http://localhost:8000").rstrip("/")
RASA       = os.getenv("RASA", "http://localhost:5005").rstrip("/")

@pytest.mark.timeout(15)
def test_backend_health_direct():
    r = requests.get(f"{BACKEND}/health", timeout=10)
    r.raise_for_status()
    data = r.json()
    assert "ok" in data or "status" in data

@pytest.mark.timeout(15)
def test_rasa_status_direct():
    r = requests.get(f"{RASA}/status", timeout=10)
    r.raise_for_status()
    data = r.json()
    assert "model_file" in data

@pytest.mark.timeout(15)
def test_rasa_webhook_direct():
    payload = {"sender": "pytest_smoke", "message": "hola"}
    r = requests.post(f"{RASA}/webhooks/rest/webhook", json=payload, timeout=10)
    r.raise_for_status()
    arr = r.json()
    assert isinstance(arr, list) and len(arr) >= 1

@pytest.mark.timeout(15)
def test_rasa_webhook_via_proxy():
    payload = {"sender": "pytest_smoke", "message": "hola"}
    r = requests.post(f"{PROXY_BASE}/rasa/webhooks/rest/webhook", json=payload, timeout=10)
    r.raise_for_status()
    arr = r.json()
    assert isinstance(arr, list) and len(arr) >= 1

@pytest.mark.timeout(15)
def test_backend_health_via_proxy():
    r = requests.get(f"{PROXY_BASE}/api/health", timeout=10)
    r.raise_for_status()
    data = r.json()
    assert "ok" in data or "status" in data