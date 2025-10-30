#\rasa\Dockerfile
FROM rasa/rasa:3.6.20-full

USER root

# 📦 Paquetes mínimos + curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext-base curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 🧩 Dependencias para tracker_store (Mongo) y event_broker (Redis)
RUN pip install --no-cache-dir "redis>=4.5" "pymongo[srv]==3.13.0"
RUN pip install --no-cache-dir pika

# 📁 Copia el proyecto Rasa completo
COPY . /app

# 🧾 Copia entrypoint y plantillas de endpoints
COPY docker/entrypoint.sh /entrypoint.sh
COPY endpoints.tpl.yml /app/endpoints.tpl.yml
COPY endpoints.mongo.tpl.yml /app/endpoints.mongo.tpl.yml

# 🔧 Normaliza saltos de línea y permisos
RUN sed -i 's/\r$//' /entrypoint.sh \
 && sed -i '1s/^\xEF\xBB\xBF//' /entrypoint.sh \
 && find /app -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; || true \
 && chown -R 1000:1000 /app /entrypoint.sh \
 && chmod +x /entrypoint.sh

# ✅ Silencia warnings SQLAlchemy 2.0 + pin <2.0
ENV SQLALCHEMY_SILENCE_UBER_WARNING=1 \
    SQLALCHEMY_WARN_20=0

# Instalación del pin (mantengo tu secuencia)
USER root
RUN pip install --no-cache-dir "sqlalchemy<2.0"
USER 1001

# 👤 Usuario sin privilegios (coherente con la imagen base)
USER 1000

# 🚀 Entrypoint
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 5005

# ❤️ Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS http://127.0.0.1:5005/status || exit 1

# Instala pymongo para registrar entrenamientos

COPY scripts/log_model_train.py /app/scripts/log_model_train.py
RUN pip install pymongo
RUN echo '#!/usr/bin/env bash' > /entrypoint_with_log.sh && \
    echo 'set -e' >> /entrypoint_with_log.sh && \
    echo 'LATEST_MODEL=$(ls -t /app/models/*.tar.gz 2>/dev/null | head -n 1)' >> /entrypoint_with_log.sh && \
    echo 'if [ -n "$LATEST_MODEL" ]; then' >> /entrypoint_with_log.sh && \
    echo '  echo "[💾] Registrando modelo al iniciar: $LATEST_MODEL";' >> /entrypoint_with_log.sh && \
    echo '  python3 /app/scripts/log_model_train.py "$LATEST_MODEL" || true;' >> /entrypoint_with_log.sh && \
    echo 'fi' >> /entrypoint_with_log.sh && \
    echo 'exec rasa run --enable-api --cors \"*\" --port ${RASA_PORT:-5005}' >> /entrypoint_with_log.sh && \
    chmod +x /entrypoint_with_log.sh

ENTRYPOINT ["/entrypoint_with_log.sh"]

