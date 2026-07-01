from __future__ import annotations

import requests
import os
from typing import Any, Dict, Optional

import logging


from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rasa_sdk import Tracker
logger = logging.getLogger(__name__)

API_GET_TIMEOUT = int(
    os.getenv("API_GET_TIMEOUT", "10")
)

API_WRITE_TIMEOUT = int(
    os.getenv("API_WRITE_TIMEOUT", "15")
)

# ================================================================
# 🌐 CONFIG CENTRAL
# ================================================================
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://backend:8000"
) 

logger.info(
    "[API CONFIG] BASE_URL=%s GET_TIMEOUT=%s WRITE_TIMEOUT=%s",
    API_BASE_URL,
    API_GET_TIMEOUT,
    API_WRITE_TIMEOUT,
)
# ================================================================
# 🔁 SESSION CON RETRY (PRODUCCIÓN)
# ================================================================
_session = requests.Session()

retry_strategy = Retry(
    total=2,
    backoff_factor=0.2,
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
        logger.info("[API GET] %s", url)

        response = _session.get(
            url,
            headers=_headers(tracker),
            timeout=API_GET_TIMEOUT
        )

        response.raise_for_status()
        return safe_json(response)

    except requests.RequestException as e:
        logger.exception(
            "[API GET ERROR] %s -> %s",
            url,
            e,
        )
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
        logger.info(
            "[API POST] %s",
            url,
        )

        response = _session.post(
            url,
            json=payload,
            headers=_headers(tracker),
            timeout=API_WRITE_TIMEOUT
        )

        response.raise_for_status()
        return safe_json(response)

    except requests.RequestException as e:
        logger.exception(
            "[API POST ERROR] %s -> %s",
            url,
            e,
        )
        return default

def safe_json(response):

    try:
        return response.json()

    except Exception:

        if response.text:
            return response.text

        logger.warning(
            "[API INVALID JSON] status=%s",
            response.status_code,
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
                timeout=API_GET_TIMEOUT,
            )

        elif method == "POST":
            response = _session.post(
                url,
                json=payload or {},
                headers=_headers(tracker),
                timeout=API_WRITE_TIMEOUT,
            )

        elif method == "PUT":
            response = _session.put(
                url,
                json=payload or {},
                headers=_headers(tracker),
                timeout=API_WRITE_TIMEOUT,
            )

        elif method == "DELETE":
            response = _session.delete(
                url,
                headers=_headers(tracker),
                timeout=API_GET_TIMEOUT,
            )

        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return safe_json(response)
       

    except Exception as e:
        logger.exception("[API ERROR] %s → %s", url, str(e))
        return default