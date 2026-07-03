# ============================================================
# 🧠 Rasa 3.6.20 + MongoDB Tracker + Registro de modelos
# ============================================================

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

# 🧠 spaCy + modelo en español para el pipeline de Rasa
COPY spacy/es_core_news_md-3.7.0-py3-none-any.whl /tmp/es_core_news_md-3.7.0-py3-none-any.whl

RUN pip install --no-cache-dir "spacy==3.7.2" && \
    pip install --no-cache-dir /tmp/es_core_news_md-3.7.0-py3-none-any.whl

# 📁 Copia el proyecto Rasa completo
COPY . /app

# 🧾 Copia entrypoint y plantillas de endpoints
COPY docker/entrypoint.sh /entrypoint.sh
COPY endpoints.tpl.yml /app/endpoints.tpl.yml
COPY endpoints.mongo.tpl.yml /app/endpoints.mongo.tpl.yml

RUN if [ -f /app/rasa/config.yml ]; then \
      echo "[Docker] Sincronizando config.yml"; \
      cp /app/rasa/config.yml /app/config.yml; \
    fi

# 🔧 Normaliza saltos de línea y permisos básicos
RUN sed -i 's/\r$//' /entrypoint.sh \
 && sed -i '1s/^\xEF\xBB\xBF//' /entrypoint.sh \
 && find /app -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; || true \
 && chown -R 1000:1000 /app /entrypoint.sh \
 && chmod +x /entrypoint.sh

ENV SQLALCHEMY_SILENCE_UBER_WARNING=1 \
    SQLALCHEMY_WARN_20=0

RUN pip install --no-cache-dir "sqlalchemy<2.0"

COPY scripts/log_model_train.py /app/scripts/log_model_train.py

RUN pip install --no-cache-dir "spacy==3.7.2" \
 && python -m spacy download es_core_news_md

RUN echo '#!/usr/bin/env bash' > /entrypoint_with_log.sh && \
    echo 'set -e' >> /entrypoint_with_log.sh && \
    echo '' >> /entrypoint_with_log.sh && \
    echo 'LATEST_MODEL=$(ls -t /app/models/*.tar.gz 2>/dev/null | head -n 1)' >> /entrypoint_with_log.sh && \
    echo 'if [ -n "$LATEST_MODEL" ]; then' >> /entrypoint_with_log.sh && \
    echo '  echo "[💾] Registrando modelo al iniciar: $LATEST_MODEL";' >> /entrypoint_with_log.sh && \
    echo '  python3 /app/scripts/log_model_train.py "$LATEST_MODEL" || true;' >> /entrypoint_with_log.sh && \
    echo 'else' >> /entrypoint_with_log.sh && \
    echo '  echo "[⚠️] No se encontró modelo en /app/models/. Entrenando uno nuevo...";' >> /entrypoint_with_log.sh && \
    echo '  rasa train;' >> /entrypoint_with_log.sh && \
    echo '  LATEST_MODEL=$(ls -t /app/models/*.tar.gz 2>/dev/null | head -n 1);' >> /entrypoint_with_log.sh && \
    echo '  if [ -n "$LATEST_MODEL" ]; then' >> /entrypoint_with_log.sh && \
    echo '    echo "[💾] Registrando modelo recién entrenado: $LATEST_MODEL";' >> /entrypoint_with_log.sh && \
    echo '    python3 /app/scripts/log_model_train.py "$LATEST_MODEL" || true;' >> /entrypoint_with_log.sh && \
    echo '  else' >> /entrypoint_with_log.sh && \
    echo '    echo "[❌] No se pudo entrenar un modelo. Revisa los logs de entrenamiento.";' >> /entrypoint_with_log.sh && \
    echo '  fi' >> /entrypoint_with_log.sh && \
    echo 'fi' >> /entrypoint_with_log.sh && \
    echo '' >> /entrypoint_with_log.sh && \
    echo 'echo "[🚀] Iniciando Rasa..."' >> /entrypoint_with_log.sh && \
    echo 'exec rasa run --enable-api --debug --cors "*" --endpoints /app/endpoints.yml --credentials /app/credentials.yml --model "$LATEST_MODEL" --port ${RASA_PORT:-5005}' >> /entrypoint_with_log.sh && \
    chmod +x /entrypoint_with_log.sh

RUN mkdir -p /app/.rasa \
 && chown -R 1000:1000 /app /entrypoint.sh /entrypoint_with_log.sh

USER 1000

ARG ENABLE_BUILD_TRAIN=false

RUN if [ "$ENABLE_BUILD_TRAIN" = "true" ]; then \
      echo "[build] Validando datos Rasa..." && \
      rasa data validate && \
      echo "[build] Entrenando modelo..." && \
      rasa train ; \
    else \
      echo "[build] ENABLE_BUILD_TRAIN=false → omitiendo train en build"; \
    fi

# RUN rasa train

ENTRYPOINT ["/entrypoint_with_log.sh"]

EXPOSE 5005

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS http://127.0.0.1:5005/status || exit 1
