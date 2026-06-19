from __future__ import annotations

import requests
import os
from typing import Any, Dict, Optional

import logging


from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rasa_sdk import Tracker
logger = logging.getLogger(__name__)


# ================================================================
# 🌐 CONFIG CENTRAL
# ================================================================
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://backend:8000"
) 

logger.info(
    "[API CONFIG] BASE_URL=%s",
    API_BASE_URL
)
# ================================================================
# 🔁 SESSION CON RETRY (PRODUCCIÓN)
# ================================================================
_session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE"]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

_session.mount("http://", adapter)
_session.mount("https://", adapter)


# ================================================================
# 🔐 HEADERS
# ================================================================
def _headers(tracker: Tracker) -> Dict[str, str]:
    token = tracker.get_slot("auth_token") or ""

    headers = {
        "Content-Type": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


# ================================================================
# 📡 GET REQUEST
# ================================================================
def get(
    tracker: Tracker,
    endpoint: str,
    default: Any = None
) -> Any:

    url = f"{API_BASE_URL}{endpoint}"

    try:
        logger.info(f"[API GET] {url}")

        response = _session.get(
            url,
            headers=_headers(tracker),
            timeout=10
        )

        response.raise_for_status()
        return safe_json(response)

    except requests.RequestException as e:
        logger.exception(f"[API GET ERROR] {url} → {e}")
        return default


# ================================================================
# 📡 POST REQUEST
# ================================================================
def post(
    tracker: Tracker,
    endpoint: str,
    payload: Dict[str, Any],
    default: Any = None
) -> Any:

    url = f"{API_BASE_URL}{endpoint}"

    try:
        logger.info(f"[API POST] {url}")

        response = _session.post(
            url,
            json=payload,
            headers=_headers(tracker),
            timeout=15
        )

        response.raise_for_status()
        return safe_json(response)

    except requests.RequestException as e:
        logger.exception(f"[API POST ERROR] {url} → {e}")
        return default

def safe_json(response):

    try:
        return response.json()

    except Exception:

        logger.warning(
            "[API INVALID JSON] status=%s",
            response.status_code
        )

        return {}

# ================================================================
# 📡 CORE BACKEND CALL (ÚNICO ENTRYPOINT)
# ================================================================
def call(
    tracker: Tracker,
    endpoint: str,
    method: str = "GET",
    default: Any = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Any:

    url = f"{API_BASE_URL}{endpoint}"

    try:
        logger.info("[API %s] %s", method, url)

        method = method.upper()

        if method == "GET":
            response = _session.get(
                url,
                headers=_headers(tracker),
                timeout=10,
            )

        elif method == "POST":
            response = _session.post(
                url,
                json=payload or {},
                headers=_headers(tracker),
                timeout=15,
            )

        elif method == "PUT":
            response = _session.put(
                url,
                json=payload or {},
                headers=_headers(tracker),
                timeout=15,
            )

        elif method == "DELETE":
            response = _session.delete(
                url,
                headers=_headers(tracker),
                timeout=10,
            )

        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        # JSON safe parse
        try:
            return response.json()
        except Exception:
            return response.text

    except Exception as e:
        logger.exception("[API ERROR] %s → %s", url, str(e))
        return default