# syntax=docker/dockerfile:1.6

############################
# Build (Vite)
############################
FROM node:18-alpine AS build
WORKDIR /app

# Instala dependencias con lock y caché
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Variables de build para Vite (sobrescribibles con --build-arg)
ARG VITE_API_BASE=/api
ARG VITE_RASA_HTTP=/rasa
ARG VITE_RASA_WS=/ws
ENV VITE_API_BASE=${VITE_API_BASE} \
    VITE_RASA_HTTP=${VITE_RASA_HTTP} \
    VITE_RASA_WS=${VITE_RASA_WS}

# Copia el código
COPY . .

# --- sanity check: falla temprano si no existe tu App ---
# Acepta: src/App.jsx, src/App.tsx o src/app.jsx (tu caso)
RUN [ -f "src/App.jsx" -o -f "src/App.tsx" -o -f "src/app.jsx" ] || (echo "❌ No existe src/App.jsx, src/App.tsx ni src/app.jsx" && exit 1)

# Compila
RUN npm run build

############################
# Runtime (Nginx estático)
############################
FROM nginx:1.27-alpine AS runtime

# SPA config (fallback a index.html)
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Artefactos de Vite
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

# Healthcheck sencillo
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]