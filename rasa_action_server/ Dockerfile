# rasa_action_server/Dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH="/app:${PYTHONPATH}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY rasa_action_server/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Código de acciones y utilidades
COPY rasa/actions /app/actions
COPY rasa/utils   /app/utils

RUN adduser --disabled-password --gecos "" --uid 10002 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5055

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:5055/health || exit 1

# Arranque del Action Server (nota: --actions actions)
CMD ["python", "-m", "rasa_sdk", "start", "--actions", "actions", "--port", "5055"]
