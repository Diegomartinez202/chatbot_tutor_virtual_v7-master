from pathlib import Path
from starlette.testclient import TestClient
from backend.main import app
from backend.config.settings import settings

def test_static_serves_dummy(tmp_path, monkeypatch):
    # prepara un archivo en STATIC_DIR
    monkeypatch.setattr(settings, "static_dir", str(tmp_path))
    (tmp_path / "README.txt").write_text("ok")
    client = TestClient(app)
    r = client.get("/static/README.txt")
    assert r.status_code == 200
    assert r.text == "ok"
