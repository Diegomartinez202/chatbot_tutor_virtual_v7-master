import pytest
from actions.acciones_llm import (
    parse_llm_response,
    call_ollama,
    call_llm_simple
)

def test_parse_llm_response_json_ok():
    data = parse_llm_response('{"type": "response", "value": "hola"}')
    assert data["type"] == "response"
    assert data["value"] == "hola"

def test_parse_llm_response_raw():
    data = parse_llm_response("texto cualquiera sin json")
    assert data["type"] == "raw"

def test_parse_llm_response_intent():
    data = parse_llm_response("INTENT: continuar_tema")
    assert data["type"] == "intent"

def test_call_llm_simple_timeout(monkeypatch):
    def fake_post(*args, **kwargs):
        raise Exception("timeout")

    import requests
    monkeypatch.setattr(requests, "post", fake_post)

    out = call_llm_simple("hola")
    assert out == ""

def test_call_ollama_timeout(monkeypatch):
    def fake_post(*args, **kwargs):
        raise Exception("timeout")

    import requests
    monkeypatch.setattr(requests, "post", fake_post)

    out = call_ollama("hola")
    assert out == ""
