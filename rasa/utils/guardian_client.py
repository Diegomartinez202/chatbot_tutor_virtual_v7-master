# rasa/utils/guardian_client.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests


class GuardianClient:
    """
    Cliente para la API autosave-guardian:
      - Login JWT con cache y renovación automática
      - Reintentos simples con backoff
      - Métodos: ping, autosave_create, autosave_latest, log_event
    """

    def __init__(
        self,
        base_url: str = "http://autosave-guardian:8080",
        username: str = "admin",
        password: str = "admin123",
        timeout: float = 5.0,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries

        self._token: Optional[str] = None
        self._token_exp: float = 0.0  # epoch seconds

    # ---------- internos ----------
    def _login(self) -> None:
        """Hace login y cachea token + expiración (si el API devuelve expires_in_minutes)."""
        url = f"{self.base_url}/auth/login"
        r = requests.post(
            url,
            json={"username": self.username, "password": self.password},
            timeout=self.timeout,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        data = r.json()
        self._token = data.get("access_token")
        if not self._token:
            raise RuntimeError("No se recibió access_token en /auth/login")

        ttl_min = data.get("expires_in_minutes", 60)
        # margen de seguridad de 30s para evitar token justo-expirado
        self._token_exp = time.time() + (ttl_min * 60) - 30

    def _auth_header(self) -> Dict[str, str]:
        """Asegura token válido, renueva si expirado."""
        now = time.time()
        if not self._token or now >= self._token_exp:
            self._login()
        return {"Authorization": f"Bearer {self._token}"}

    def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        json: Any = None,
        params: Dict[str, Any] | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                headers = {"Content-Type": "application/json"}
                if auth:
                    headers.update(self._auth_header())

                resp = requests.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=json,
                    params=params,
                    timeout=self.timeout,
                )

                # Si 401 y tenemos intentos, forzamos relogin y reintentamos una vez
                if resp.status_code == 401 and auth and attempt < self.max_retries:
                    self._login()
                    continue

                return resp

            except requests.RequestException as e:
                last_exc = e
                if attempt < self.max_retries:
                    time.sleep(0.4 * (attempt + 1))
                else:
                    raise

        raise last_exc or RuntimeError("Fallo desconocido en request")

    # ---------- endpoints públicos ----------
    def ping(self) -> bool:
        try:
            r = self._request("GET", "/ping", auth=False)
            if not r.ok:
                return False
            data = r.json()
            # en tu app.py devuelves {"ok": True}
            return bool(data.get("ok", False) is not False)
        except Exception:
            return False

    def autosave_create(self, sender_id: str, data: Dict[str, Any]) -> bool:
        r = self._request(
            "POST", "/autosaves", json={"sender_id": sender_id, "data": data}, auth=True
        )
        return r.ok and r.json().get("ok") is True

    def autosave_latest(self, limit: int = 5) -> Dict[str, Any]:
        r = self._request(
            "GET", "/autosaves/latest", params={"limit": limit}, auth=True
        )
        return r.json() if r.ok else {"ok": False, "items": []}

    def log_event(self, event_type: str, payload: Dict[str, Any] | None = None) -> bool:
        r = self._request(
            "POST",
            "/events/log",
            json={"event_type": event_type, "payload": payload or {}},
            auth=True,
        )
        return r.ok and r.json().get("ok") is True
