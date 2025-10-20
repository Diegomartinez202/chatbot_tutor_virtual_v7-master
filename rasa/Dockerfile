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
# (Se mantienen aunque el compose monta el template correcto; esto no interfiere)
COPY docker/entrypoint.sh /entrypoint.sh
COPY endpoints.tpl.yml /app/endpoints.tpl.yml
COPY endpoints.mongo.tpl.yml /app/endpoints.mongo.tpl.yml

# 🔧 Normaliza saltos de línea y permisos
RUN sed -i 's/\r$//' /entrypoint.sh \
 && sed -i '1s/^\xEF\xBB\xBF//' /entrypoint.sh \
 && find /app -type f -name "*.sh" -exec sed -i 's/\r$//' {} \; || true \
 && chown -R 1000:1000 /app /entrypoint.sh \
 && chmod +x /entrypoint.sh

# 👤 Usuario sin privilegios (coherente con la imagen base)
USER 1000

# 🚀 Entrypoint
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 5005

# ❤️ Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD curl -fsS http://127.0.0.1:5005/status || exit 1