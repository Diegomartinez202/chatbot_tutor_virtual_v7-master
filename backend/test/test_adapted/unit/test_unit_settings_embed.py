# backend/test_adapted/unit/test_unit_settings_embed.py
import importlib
import os


def test_settings_lee_embed_allowed_origins(monkeypatch):
    """
    Verifica que la configuración de EMBED_ALLOWED_ORIGINS se lea desde
    variables de entorno y se refleje en settings (si tu proyecto lo hace así).

    En caso de que tu objeto settings use otro nombre de campo, ajusta el test.
    """
    monkeypatch.setenv(
        "EMBED_ALLOWED_ORIGINS",
        '["self","http://localhost:5173","https://demo.example"]',
    )

    # Reimportamos settings para forzar recarga de BaseSettings
    if "backend.config.settings" in list(importlib.sys.modules.keys()):
        importlib.reload(importlib.import_module("backend.config.settings"))
    from backend.config.settings import settings  # type: ignore

    origins = getattr(settings, "embed_allowed_origins", None)
    assert origins is not None, "settings.embed_allowed_origins no existe"
    assert "http://localhost:5173" in origins
    assert "https://demo.example" in origins
