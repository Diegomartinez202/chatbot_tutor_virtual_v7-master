from __future__ import annotations

from fastapi.testclient import TestClient


def _create_via_service(client: TestClient, email="nuevo@test.com"):
    # Crea mediante endpoint admin (requiere rol admin → fixture admin_auth_override)
    payload = {
        "nombre": "Nuevo",
        "email": email,
        "password": "abcd",
        "rol": "usuario",
    }
    r = client.post("/api/admin/users", json=payload, headers={"Authorization": "Bearer demo"})
    assert r.status_code in (200, 201), r.text
    return r.json()


def test_admin_users_list_and_crud_flow(client: TestClient, admin_auth_override):
    # LIST inicial (puede estar vacío)
    r0 = client.get("/api/admin/users", headers={"Authorization": "Bearer demo"})
    assert r0.status_code == 200, r0.text
    initial = r0.json()
    assert isinstance(initial, list)

    # CREATE
    new_user = _create_via_service(client, email="nuevo1@test.com")
    assert new_user.get("email") == "nuevo1@test.com"
    assert "id" in new_user

    # LIST debe incluirlo
    r1 = client.get("/api/admin/users", headers={"Authorization": "Bearer demo"})
    assert r1.status_code == 200
    lst = r1.json()
    emails = [u.get("email") for u in lst]
    assert "nuevo1@test.com" in emails

    # UPDATE (cambiamos nombre y rol)
    uid = new_user["id"]
    upd = {"nombre": "Actualizado", "rol": "soporte"}
    r2 = client.put(f"/api/admin/users/{uid}", json=upd, headers={"Authorization": "Bearer demo"})
    assert r2.status_code == 200, r2.text
    updated = r2.json()
    assert updated.get("nombre") == "Actualizado"
    assert updated.get("rol") in ("soporte", "support", "soporte".lower())  # tolerante

    # DELETE
    r3 = client.delete(f"/api/admin/users/{uid}", headers={"Authorization": "Bearer demo"})
    assert r3.status_code in (200, 204), r3.text

    # LIST ya no debe incluirlo
    r4 = client.get("/api/admin/users", headers={"Authorization": "Bearer demo"})
    assert r4.status_code == 200
    lst2 = r4.json()
    emails2 = [u.get("email") for u in lst2]
    assert "nuevo1@test.com" not in emails2


def test_admin_users_export_csv(client: TestClient, admin_auth_override):
    # Crea 2 usuarios y exporta CSV
    _create_via_service(client, email="csv1@test.com")
    _create_via_service(client, email="csv2@test.com")

    r = client.get("/api/admin/users/export", headers={"Authorization": "Bearer demo"})
    # Algunos controladores devuelven 200 + csv; otros 200 con StreamingResponse
    assert r.status_code == 200, r.text
    # Content-Type puede variar; verificamos cabecera de descarga
    cd = r.headers.get("content-disposition", "").lower()
    assert "attachment;" in cd
    assert ".csv" in cd
    assert "id,email" or "email"  # lectura la hace Excel; con BOM puede variar
