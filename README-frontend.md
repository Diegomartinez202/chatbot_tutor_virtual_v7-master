# Frontend (Admin Panel React + Vite)

## Prerrequisitos
- Node.js LTS (con npm). Verifica: `node -v` y `npm -v`.
- Backend FastAPI en http://127.0.0.1:8000 (o ajusta tu .env).

## Ejecutar
```bash
cd admin_panel_react
npm install
npm run dev
App: http://localhost:5173

.env (Vite)
Crea admin_panel_react/.env:

ini
Copiar código
VITE_API_BASE=http://127.0.0.1:8000
# VITE_ZAJUNA_SSO_URL=https://tu-sso.local/oauth/authorize
CORS en FastAPI
Permite:

http://localhost:5173

http://127.0.0.1:5173
