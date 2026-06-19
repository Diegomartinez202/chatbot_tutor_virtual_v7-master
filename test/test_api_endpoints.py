import os
import requests

BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("DEMO_TOKEN", "demo-token")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def test_estado_estudiante():
    r = requests.get(f"{BASE_URL}/api/estado-estudiante", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    # EstadoEstudianteResponse → {"estado": "..."}
    assert "estado" in data
    assert isinstance(data["estado"], str)


def test_tutor():
    r = requests.get(f"{BASE_URL}/api/tutor", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "nombre" in data
    assert "contacto" in data


def test_certificados():
    r = requests.get(f"{BASE_URL}/api/certificados", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "certificados" in data
    assert isinstance(data["certificados"], list)


def test_horarios():
    r = requests.get(f"{BASE_URL}/api/horarios", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "horarios" in data
    assert isinstance(data["horarios"], list)


def test_progreso_cursos():
    r = requests.get(f"{BASE_URL}/api/progreso-cursos", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert "cursos" in data
    assert isinstance(data["cursos"], list)


def test_usuario_detalle():
    user_id = "user-123"
    r = requests.get(f"{BASE_URL}/api/usuarios/{user_id}", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    # response_model=UserOut → tiene "id"
    assert "id" in data
    assert data["id"] == user_id


def test_usuario_calificaciones():
    user_id = "user-123"
    r = requests.get(f"{BASE_URL}/api/usuarios/{user_id}/calificaciones", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["usuario"] == user_id
    assert isinstance(data["calificaciones"], list)


def test_usuario_estado():
    user_id = "user-123"
    r = requests.get(f"{BASE_URL}/api/usuarios/{user_id}/estado", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["usuario"] == user_id
    assert "estado" in data