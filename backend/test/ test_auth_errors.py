
---

### 📄 Contenido `test_auth_errors.py`:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ❌ Login con credenciales inválidas
def test_login_fallido():
    res = client.post("/api/auth/login", json={
        "email": "inexistente@test.com",
        "password": "error123"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Credenciales inválidas"

# ❌ Acceso sin token
def test_me_sin_token():
    res = client.get("/api/auth/me")
    assert res.status_code == 401

# ❌ Refresh sin cookie
def test_refresh_sin_cookie():
    res = client.post("/api/auth/refresh")
    assert res.status_code == 401