# tests/test_chat_alias.py
def test_health_both_paths(client):
    r1 = client.get("/chat/health")
    r2 = client.get("/api/chat/health")
    assert r1.status_code == 200 and r1.json().get("ok") is True
    assert r2.status_code == 200 and r2.json().get("ok") is True

def test_chat_post_both_paths(client):
    payload = {"message": "hola", "sender_id": "pytest-1"}
    a = client.post("/chat", json=payload)
    b = client.post("/api/chat", json=payload)
    assert a.status_code == 200
    assert b.status_code == 200
    assert isinstance(a.json(), list)
    assert isinstance(b.json(), list)

def test_openapi_hides_api_alias(client):
    spec = client.get("/openapi.json").json()
    paths = set(spec.get("paths", {}).keys())
    assert "/chat" in paths and "/chat/health" in paths
    assert "/api/chat" not in paths and "/api/chat/health" not in paths
