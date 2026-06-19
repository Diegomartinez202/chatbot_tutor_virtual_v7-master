import os
from backend.utils.file_utils import save_csv_s3_and_local
from backend.config.settings import settings

def test_save_csv_local_only(monkeypatch, tmp_path):
    # Forzamos modo local-only
    monkeypatch.setattr(settings, "s3_enabled", False, raising=False)
    monkeypatch.setattr(settings, "debug", True, raising=False)

    # Redirigimos la carpeta de estáticos a un tmp aislado
    static_dir = tmp_path / "static"
    monkeypatch.setattr(settings, "static_dir", str(static_dir), raising=False)

    # Datos de prueba
    csv_text = "col1,col2\nA,B\n"
    buf, url = save_csv_s3_and_local(csv_text, filename_prefix="pytest_export")

    # Debe devolver URL local y el archivo debe existir físicamente
    assert url.startswith("/static/exports/")
    basename = os.path.basename(url)
    expected_file = static_dir / "exports" / basename

    assert expected_file.exists(), f"No se creó el archivo: {expected_file}"
    assert expected_file.read_text(encoding="utf-8") == csv_text

    # El buffer debe apuntar al mismo contenido
    buf.seek(0)
    assert buf.read().decode("utf-8") == csv_text