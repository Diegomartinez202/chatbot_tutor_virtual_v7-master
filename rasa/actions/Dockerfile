# rasa/actions/Dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Toolchain y utilidades (para compilar ruedas si falta wheel precompilada)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      g++ \
      make \
      libffi-dev \
      libssl-dev \
      curl \
      wget \
    && rm -rf /var/lib/apt/lists/*

# Instala deps (usa --prefer-binary para evitar compilar si hay wheel)
COPY actions/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel && \
    if [ -f /tmp/requirements.txt ]; then \
      pip install --no-cache-dir --prefer-binary -r /tmp/requirements.txt ; \
    else \
      pip install --no-cache-dir --prefer-binary rasa-sdk==3.6.2 "requests>=2.32,<3" "pydantic>=1.10,<2" ; \
    fi

COPY actions /app/actions

# Usuario no root (opcional)
RUN adduser --disabled-password --gecos "" --uid 10002 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5055
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:5055/health >/dev/null 2>&1 || exit 1

CMD ["python","-m","rasa_sdk","--actions","actions","--port","5055"]