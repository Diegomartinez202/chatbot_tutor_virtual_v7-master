# syntax=docker/dockerfile:1.6

# Imagen base compatible con Rasa 3.1.0
FROM python:3.9-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH="/app:${PYTHONPATH}" \
    DEBIAN_FRONTEND=noninteractive

# Directorio de trabajo
WORKDIR /app

# Dependencias del sistema necesarias para compilar extensiones y healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    git \
 && rm -rf /var/lib/apt/lists/*

# Copiamos los requirements de las acciones
COPY rasa_action_server/requirements.txt /tmp/requirements.txt

# Actualiza pip y herramientas base
RUN python -m pip install --upgrade pip setuptools wheel

# Instalamos dependencias del action server y SDK de Rasa
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    pip install --no-cache-dir rasa-sdk==3.1.1

# Copiamos el código fuente del proyecto (manteniendo la estructura original)
COPY rasa/actions /app/actions
COPY rasa/utils   /app/utils

# Creamos usuario seguro para ejecutar el contenedor
RUN adduser --disabled-password --gecos "" --uid 10002 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Exponemos el puerto de servicio del action server
EXPOSE 5055

# Healthcheck para monitoreo del contenedor
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:5055/health || exit 1

# Comando de arranque del Action Server (Rasa SDK 3.x)
CMD ["python", "-m", "rasa_sdk", "--actions", "actions", "--port", "5055"]
