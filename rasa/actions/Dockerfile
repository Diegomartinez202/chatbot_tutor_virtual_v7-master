# rasa/actions/Dockerfile
# syntax=docker/dockerfile:1.6

# ✅ 1) Usamos la imagen oficial del SDK de Rasa (evita compilar dependencias)
FROM rasa/rasa-sdk:3.6.2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ✅ 2) Copiamos tus acciones y el entrypoint
COPY actions /app/actions
COPY actions/entrypoint.sh /entrypoint.sh
COPY utils /app/utils 
# ✅ 3) requirements opcional
USER root
RUN if [ -f /app/actions/requirements.txt ]; then \
      python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
      pip install --no-cache-dir -r /app/actions/requirements.txt ; \
    fi

# Normaliza CRLF y permisos
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
USER 1001

EXPOSE 5055

# ✅ Healthcheck correcto (sin heredoc)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD ["python","-c","import urllib.request,sys,socket; socket.setdefaulttimeout(3); urllib.request.urlopen('http://127.0.0.1:5055/health'); print('ok')"]

# ✅ 4) Entrypoint con tus echos + arranque del SDK
ENTRYPOINT ["/entrypoint.sh"]
