# syntax=docker/dockerfile:1.6

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH="/app:${PYTHONPATH}" \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
 && rm -rf /var/lib/apt/lists/*

COPY rasa_action_server/requirements.txt /tmp/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir \
    rasa-sdk==3.6.2

RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY rasa/actions /app/actions
COPY rasa/utils /app/utils

COPY rasa_action_server/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN adduser --disabled-password \
    --gecos "" \
    --uid 10002 \
    appuser

RUN chown -R appuser:appuser /app

RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app/data

USER appuser

EXPOSE 5055

HEALTHCHECK --interval=30s \
           --timeout=5s \
           --retries=3 \
  CMD curl -fsS http://127.0.0.1:5055/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]