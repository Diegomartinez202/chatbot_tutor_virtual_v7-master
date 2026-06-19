# Makefile (raíz del proyecto)

# ===== Variables (tómalas de tu entorno o .env) =====
# Ejemplo .env:
# HELPDESK_WEBHOOK=http://localhost:8000/api/helpdesk/tickets
# HELPDESK_TOKEN=xxxxx
# RASA_DIR=rasa
# RASA_PORT=5005
# ACTIONS_PORT=5055

RASA_DIR ?= rasa
RASA_PORT ?= 5005
ACTIONS_PORT ?= 5055

# ===== Tareas =====
.PHONY: train actions rasa-up rasa-stop helpdesk-test

train:
	@echo "🧠 Entrenando modelo Rasa..."
	cd $(RASA_DIR) && rasa data validate && rasa train

actions:
	@echo "⚙️  Levantando Action Server en :$(ACTIONS_PORT)..."
	cd $(RASA_DIR) && rasa run actions -p $(ACTIONS_PORT)

rasa-up:
	@echo "🚀 Iniciando Rasa (API) y Action Server..."
	-@pkill -f "rasa run actions" || true
	-@pkill -f "rasa run --enable-api" || true
	cd $(RASA_DIR) && (rasa run actions -p $(ACTIONS_PORT) &)
	sleep 2
	cd $(RASA_DIR) && rasa run --enable-api -p $(RASA_PORT) --cors "*"

rasa-stop:
	@echo "🛑 Deteniendo procesos Rasa..."
	-@pkill -f "rasa run actions" || true
	-@pkill -f "rasa run --enable-api" || true

helpdesk-test:
	@echo "🔎 Probando creación de ticket en Helpdesk..."
	@if [ -z "$$HELPDESK_WEBHOOK" ]; then echo "❌ Falta HELPDESK_WEBHOOK en el entorno"; exit 1; fi
	curl -sS -X POST "$$HELPDESK_WEBHOOK" \
		-H "Content-Type: application/json" \
		$$( [ -n "$$HELPDESK_TOKEN" ] && echo '-H "Authorization: Bearer '"$$HELPDESK_TOKEN"'"' ) \
		-d '{"name":"Test desde Makefile","email":"demo@example.com","subject":"Prueba rápida","message":"Esto es un ticket de prueba","conversation_id":"makefile-test"}' \
		| sed 's/.*/✅ Respuesta:/'; echo