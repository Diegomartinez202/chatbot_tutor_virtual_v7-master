# syntax=docker/dockerfile:1.6

############################
# BASE (runtime base)
############################
FROM python:3.10-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive \
    APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1

# UID/GID parametrizables para alinear con el host
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001

WORKDIR /app

RUN set -eux; \
    rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend || true; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get install -y --no-install-recommends \
      bash \
      curl \
      ca-certificates \
      poppler-utils \
      adduser \
      passwd \
    ; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN set -eux; \
    if ! getent group "${APP_GID}" >/dev/null; then \
      addgroup --gid "${APP_GID}" "${APP_USER}" || addgroup --gid "${APP_GID}" "${APP_USER}"; \
    fi; \
    if ! id -u "${APP_USER}" >/dev/null 2>&1; then \
      adduser --disabled-password --gecos "" --uid "${APP_UID}" --gid "${APP_GID}" "${APP_USER}"; \
    fi; \
    mkdir -p /app/logs /app/backend/static && chown -R "${APP_UID}:${APP_GID}" /app

############################
# DEPS (requirements)
############################
FROM python:3.10-slim-bookworm AS deps

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    DEBIAN_FRONTEND=noninteractive \
    APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1

RUN set -eux; \
    rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock-frontend || true; \
    apt-get -o Acquire::Retries=5 update; \
    apt-get install -y --no-install-recommends \
      build-essential \
      libffi-dev \
      cargo \
      dos2unix \
      libc-bin \
      ca-certificates \
    ; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

ARG REQUIREMENTS_PATH=backend/requirements.txt
COPY ${REQUIREMENTS_PATH} /tmp/requirements.txt
RUN dos2unix /tmp/requirements.txt || true && \
    (iconv -f ISO-8859-1 -t UTF-8 /tmp/requirements.txt -o /tmp/requirements.txt || true)

RUN python -m pip install --upgrade "pip<25" "setuptools<70" wheel && \
    pip install --prefer-binary --prefix=/install -r /tmp/requirements.txt

############################
# PROD
############################
FROM base AS prod

COPY --from=deps /install /usr/local
COPY . /app

# Instalar Node.js temporalmente para Tailwind
USER root
RUN set -eux; \
    apt-get update && \
    apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g postcss postcss-cli tailwindcss autoprefixer && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Compilar Tailwind
RUN node /app/build-tailwind.js

# Asegurar permisos correctos
ARG APP_USER=appuser
ARG APP_UID=10001
ARG APP_GID=10001
RUN chown -R "${APP_UID}:${APP_GID}" /app

USER ${APP_USER}

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/chat/health || exit 1

ENV UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=2 \
    APP_ENV=prod \
    DEBUG=0

CMD ["bash","-lc","exec uvicorn backend.main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT} --workers ${UVICORN_WORKERS} --proxy-headers --forwarded-allow-ips='*'"]

############################
# DEV
############################
FROM prod AS dev

USER root
RUN python -m pip install --no-cache-dir watchfiles uvicorn[standard]

# Recompilar Tailwind en dev cada build
RUN node /app/build-tailwind.js

USER ${APP_USER}

ENV APP_ENV=dev \
    DEBUG=1

CMD ["bash","-lc","exec uvicorn backend.main:app --reload --host ${UVICORN_HOST} --port ${UVICORN_PORT}"]