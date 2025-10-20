# ==============================
# Makefile — Chatbot Tutor Virtual
# ==============================
SHELL := /bin/bash
.DEFAULT_GOAL := help

BACKEND_URL ?= http://localhost:8000
FRONTEND_PORT ?= 5173
BACKEND_PORT ?= 8000

.PHONY: help
help:
	@echo ""
	@echo "Comandos disponibles:"
	@echo "  make create-env-backend     -> Copia backend/.env.example a backend/.env si no existe"
	@echo "  make check-embed            -> Verifica CSP, redirects y health (BACKEND_URL?=$(BACKEND_URL))"
	@echo ""
	@echo "  make dev-backend            -> Levanta el backend FastAPI (puerto $(BACKEND_PORT))"
	@echo "  make dev-frontend           -> Levanta el frontend Vite (puerto $(FRONTEND_PORT))"
	@echo ""
	@echo "  make train                  -> Entrena Rasa (train_rasa.sh)"
	@echo "  make test                   -> Ejecuta pruebas con pytest"
	@echo "  make logs                   -> Pruebas de logs"
	@echo "  make users                  -> Pruebas de usuarios"
	@echo "  make upload                 -> Prueba de subida CSV"
	@echo "  make all-tests              -> Ejecuta test_all.sh"

.PHONY: create-env-backend
create-env-backend:
	@if [ ! -f backend/.env ]; then \
	  cp backend/.env.example backend/.env && \
	  echo '✅ backend/.env creado desde backend/.env.example'; \
	else \
	  echo 'ℹ️ backend/.env ya existe. Nada que copiar.'; \
	fi

.PHONY: check-embed
check-embed:
	@if [ ! -f ./check_embed.sh ]; then \
	  echo "❌ No encuentro ./check_embed.sh en la raíz del repo"; \
	  exit 1; \
	fi
	@bash ./check_embed.sh $(BACKEND_URL)

.PHONY: dev-backend
dev-backend:
	@echo "🚀 Iniciando backend en puerto $(BACKEND_PORT)..."
	uvicorn backend.main:app --host 0.0.0.0 --port $(BACKEND_PORT) --reload

.PHONY: dev-frontend
dev-frontend:
	@echo "🚀 Iniciando frontend en puerto $(FRONTEND_PORT)..."
	npm run dev --prefix frontend

.PHONY: train
train:
	@echo "🧠 Entrenando Rasa..."
	bash train_rasa.sh

.PHONY: test
test:
	@echo "🧪 Ejecutando pruebas generales..."
	pytest backend/test --disable-warnings

.PHONY: logs
logs:
	@echo "📜 Ejecutando pruebas de logs..."
	pytest backend/test/test_logs.py --disable-warnings

.PHONY: users
users:
	@echo "👥 Ejecutando pruebas de usuarios..."
	pytest backend/test/test_users.py --disable-warnings

.PHONY: upload
upload:
	@echo "⬆️ Ejecutando prueba de subida de intents por CSV..."
	pytest backend/test/test_upload_csv.py --disable-warnings

.PHONY: all-tests
all-tests:
	@echo "🧪 Ejecutando test_all.sh completo..."
	bash test_all.sh

# ====== Config ======
DC := docker compose
PROJECT := tutorbot-local

# Archivos compose (ajusta si cambias nombres)
BASE := -f docker-compose.yml
DEV  := -f docker-compose.override.yml
NGINX:= -f docker-compose.nginx.yml
REDIS:= -f docker-compose.redis.yml

# ====== Ayuda ======
.PHONY: help
help:
	@echo "Targets disponibles:"
	@echo "  build-dev        - Build de servicios (con override DEV)"
	@echo "  up-dev           - Levanta stack DEV (hot-reload) [backend/rasa/actions]"
	@echo "  build-prod       - Build de servicios (base + nginx)"
	@echo "  up-prod          - Levanta stack PROD (base + nginx)"
	@echo "  up-redis         - Suma Redis y reinicia backend con RATE_LIMIT_BACKEND=redis"
	@echo "  up-nginx         - (re)levanta sólo nginx sobre el stack base"
	@echo "  logs             - Logs en vivo de todos los servicios"
	@echo "  ps               - Estado de servicios"
	@echo "  down             - Baja todo (incl. nginx/redis si están cargados)"
	@echo "  prune            - Limpieza de recursos dangling"

# ====== DEV ======
.PHONY: build-dev up-dev
build-dev:
	$(DC) $(BASE) $(DEV) build

up-dev:
	$(DC) $(BASE) $(DEV) up -d

# ====== PROD ======
.PHONY: build-prod up-prod
build-prod:
	$(DC) $(BASE) $(NGINX) build

up-prod:
	$(DC) $(BASE) $(NGINX) up -d

# ====== Extras ======
.PHONY: up-redis up-nginx
up-redis:
	$(DC) $(BASE) $(REDIS) up -d redis backend

up-nginx:
	$(DC) $(BASE) $(NGINX) up -d nginx

# ====== Utilidades ======
.PHONY: logs ps down prune
logs:
	$(DC) $(BASE) logs -f --tail=100

ps:
	$(DC) $(BASE) ps

down:
	# Intenta bajar todo: base + dev + nginx + redis (si existen)
	-$(DC) $(BASE) $(DEV) $(NGINX) $(REDIS) down

prune:
	docker system prune -f