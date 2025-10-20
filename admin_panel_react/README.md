> Ruta: `chatbot_tutor_virtual_v7.3/admin_panel_react/README.md`

```md
# 🖥️ Admin Panel (React + Vite)

Panel administrativo del **Chatbot Tutor Virtual**. Build con Vite, servido en producción con Nginx (imagen inmutable).

> 📎 **Windows Quickstart** y creación de venvs: ver `../docs/WINDOWS-QUICKSTART.md`  
> 🔧 Script de venvs (enlace directo): `../scripts/make_venvs.ps1`

---

## 1) Modos de ejecución

### A) Dev (Vite + HMR)
```powershell
# con Docker (proxy ya configurado): desde la raíz
docker compose --profile build up -d admin-dev nginx-dev
# UI: http://localhost/
Variables (ya las inyecta compose):

ini
Copiar código
VITE_API_BASE=http://localhost:8000
VITE_RASA_HTTP=http://localhost:5005
VITE_RASA_WS=ws://localhost:5005
O directo (sin Docker), dentro de admin_panel_react/:

powershell
Copiar código
npm ci
npm run dev   # http://localhost:5173
B) Prod (build + Nginx)
powershell
Copiar código
# raíz del repo
docker compose --profile prod up -d --build admin nginx
# UI: http://localhost/
El compose pasa build args al Dockerfile:

ini
Copiar código
VITE_API_BASE=/api
VITE_RASA_HTTP=/rasa
VITE_RASA_WS=/ws
2) Proxy vs Dominios absolutos
✅ Con proxy (recomendado): /api, /rasa, /ws (Nginx enruta al backend/Rasa).

🔄 Sin proxy (dominios absolutos):

Usa ./.env.production.external (no borres el original).

Antes de construir:

powershell
Copiar código
cd admin_panel_react
cp .env.production.external .env.production
docker compose --profile prod build admin
docker compose --profile prod up -d admin
(alternativa CI/CD: sobreescribe con build.args en docker-compose.yml sin tocar archivos).

3) Dockerfile y Nginx
Dockerfile multi-stage admite VITE_API_BASE, VITE_RASA_HTTP, VITE_RASA_WS.

nginx.conf sirve SPA con try_files $uri /index.html; y cachea estáticos con hash.

4) Variables útiles
VITE_API_BASE → base del backend (/api o absoluto)

VITE_RASA_HTTP → HTTP de Rasa (/rasa o absoluto)

VITE_RASA_WS → WebSocket de Rasa (/ws o absoluto)

VITE_CHAT_TRANSPORT → rest (default) o ws

5) Smoke
Carga UI (200 OK) en http://localhost/ (prod) o http://localhost:5173 (dev).

Probar backend desde DevTools:

js
Copiar código
fetch('/api/chat/health').then(r=>r.json())
En dev sin proxy:

js
Copiar código
fetch('http://localhost:8000/api/chat/health').then(r=>r.json())
6) Troubleshooting
CORS (dev): backend debe permitir http://localhost:5173 (ya configurado).

404 rutas internas: nginx.conf debe tener try_files $uri /index.html;.

WS: en prod usa wss:// detrás de TLS y verifica /ws en Nginx.