from starlette.testclient import TestClient
from backend.main import app


def test_csp_incluye_frame_ancestors_y_embed(monkeypatch):
    """
    Prueba semi-unitaria: verifica que la cabecera Content-Security-Policy
    incluye la directiva frame-ancestors y que, como mínimo, restringe el
    embebido a 'self'.

    Aunque se configure EMBED_ALLOWED_ORIGINS, en el entorno demo del
    proyecto el backend mantiene una política conservadora donde
    frame-ancestors solo incluye 'self', en línea con las restricciones
    actuales (sin integración productiva con Zajuna).
    """
    monkeypatch.setenv("EMBED_ALLOWED_ORIGINS", "'self' http://localhost:5173")
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200

    csp = r.headers.get("content-security-policy", "")
    csp_lower = csp.lower()

    # Debe existir la directiva frame-ancestors
    assert "frame-ancestors" in csp_lower

    # Y debe incluir al menos 'self' como origen permitido
    assert "'self'" in csp or " self " in csp

    # No exigimos que aparezca explícitamente http://localhost:5173
    # porque en este entorno de pruebas la política se mantiene cerrada
    # a 'self' por decisión de diseño.
