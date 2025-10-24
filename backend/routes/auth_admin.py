# backend/routes/auth_admin.py
"""
Shim de compatibilidad:
Este módulo preserva el import histórico `backend.routes.auth_admin`
pero delega toda la lógica al router unificado de admin_auth.py.

- Expone `router` con el prefijo legacy `/api/admin`
- Opcionalmente exporta `ensure_admin_indexes` si tu startup lo llama
"""

from __future__ import annotations

from backend.routes.admin_auth import (
    router_compat as router,  # /api/admin (legacy)
    ensure_admin_indexes,
)

__all__ = ["router", "ensure_admin_indexes"]
