# backend/test/routes/test_admin_train.py
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def _login(email: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_user():
    email = "train_admin@example.com"
    password = "trainadmin123"
    rol = "admin"

    r_reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "rol": rol},
    )
    assert r_reg.status_code in (200, 400), r_reg.text
    return {"email": email, "password": password}


@pytest.fixture(scope="module")
def normal_user():
    email = "train_user@example.com"
    password = "trainuser123"
    rol = "usuario"

    r_reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "rol": rol},
    )
    assert r_reg.status_code in (200, 400), r_reg.text
    return {"email": email, "password": password}


@pytest.mark.parametrize(
    "who, expected_status, should_call",
    [
        ("admin", 200, True),
        ("user", 403, False),  # podría ser 401/403 según tu auth
    ],
)
def test_admin_train_permissions(monkeypatch, admin_user, normal_user, who, expected_status, should_call):
    """
    Adaptación de los tests legacy:
      - Solo admin debe poder ejecutar /api/admin/train
      - Parcheamos la función de entrenamiento para no lanzar Rasa real
    """
    # 1) Elegir credenciales
    if who == "admin":
        creds = admin_user
    else:
        creds = normal_user

    access = _login(creds["email"], creds["password"])

    # 2) Parchear servicio de entrenamiento
    # ⚠️ AJUSTA ESTE IMPORT AL MÓDULO/FUNCIÓN REALES
    import backend.services.training as training_mod

    called = {"value": False}

    def fake_train():
        called["value"] = True
        # Respuesta fake que tu endpoint puede devolver
        return {"ok": True, "returncode": 0, "msg": "fake-train"}

    monkeypatch.setattr(training_mod, "train_rasa_sync", fake_train, raising=False)

    # 3) Llamar endpoint
    r = client.post(
        "/api/admin/train",
        headers={"Authorization": f"Bearer {access}"},
    )

    assert r.status_code == expected_status, r.text

    if expected_status == 200:
        assert called["value"] is True
        data = r.json()
        assert data.get("ok") is True
    else:
        # si está prohibido, no se debe llamar el servicio
        assert called["value"] is False
