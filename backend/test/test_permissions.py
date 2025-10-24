import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ===========================================
# 🔐 TOKENS SIMULADOS (Reemplazar por reales)
# ===========================================
TOKEN_ADMIN = "Bearer TESTTOKEN_ADMIN"
TOKEN_SOPORTE = "Bearer TESTTOKEN_SOPORTE"
TOKEN_USUARIO = "Bearer TESTTOKEN_USUARIO"

# =====================================================
# 🔐 Pruebas sin autenticación (Debe responder 401)
# =====================================================
def test_protected_endpoint_requires_auth():
    res = client.get("/api/admin/intents")
    assert res.status_code == 401

def test_sin_token_logs():
    res = client.get("/api/admin/logs")
    assert res.status_code == 401

# =====================================================
# 🔐 Pruebas con rol sin permiso (Debe responder 403)
# =====================================================
def test_token_usuario_sin_permisos_logs():
    res = client.get("/api/admin/logs", headers={"Authorization": TOKEN_USUARIO})
    assert res.status_code == 403

def test_token_usuario_no_puede_ver_intents():
    res = client.get("/api/admin/intents", headers={"Authorization": TOKEN_USUARIO})
    assert res.status_code == 403

# =====================================================
# ✅ Pruebas con roles correctos (Debe responder 200/204)
# =====================================================
def test_token_soporte_puede_ver_logs():
    res = client.get("/api/admin/logs", headers={"Authorization": TOKEN_SOPORTE})
    assert res.status_code in [200, 204, 404]  # 404 si no hay logs

def test_token_admin_puede_ver_logs():
    res = client.get("/api/admin/logs", headers={"Authorization": TOKEN_ADMIN})
    assert res.status_code in [200, 204, 404]

def test_token_admin_si_puede_ver_intents():
    res = client.get("/api/admin/intents", headers={"Authorization": TOKEN_ADMIN})
    assert res.status_code in [200, 204]
