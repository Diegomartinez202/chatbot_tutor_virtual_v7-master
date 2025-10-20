# syntax=docker/dockerfile:1.6

############################
# Build (Vite)
############################
FROM node:18-alpine AS build
WORKDIR /app

# Instala dependencias con lockfile y caché de npm (más rápido en CI)
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Variables de build para Vite (puedes sobreescribir con --build-arg)
ARG VITE_API_BASE=/api
ARG VITE_RASA_HTTP=/rasa
ARG VITE_RASA_WS=/ws
ENV VITE_API_BASE=${VITE_API_BASE} \
    VITE_RASA_HTTP=${VITE_RASA_HTTP} \
    VITE_RASA_WS=${VITE_RASA_WS}

# Copia el código y construye
COPY . .
RUN npm run build

############################
# Runtime (Nginx estático)
############################
FROM nginx:1.27-alpine AS runtime

# Config SPA (fallback a index.html + cache agresiva de assets con hash)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copia artefactos generados por Vite
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Salud simple
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]