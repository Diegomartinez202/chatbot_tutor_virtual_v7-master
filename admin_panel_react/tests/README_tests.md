# Pruebas E2E / Visuales (Playwright)

## Requisitos
- Node 18+  
- `admin_panel_react/package.json` con `"type": "module"`
- `tsconfig.playwright.json` con:
  - `"module": "ESNext"`
  - `"moduleResolution": "NodeNext"`
  - `"types": ["@playwright/test", "node"]`

> **Importante (NodeNext):** todos los **imports relativos** entre archivos TS deben terminar en **`.js`** (ej: `../utils/gotoSpa.js`), aunque el archivo fuente sea `.ts`.

## Instalación
```bash
npm i
npx playwright install --with-deps
Correr screenshots (server auto con webServer)
bash
Copiar
Editar
npm run screenshots
# Reporte HTML:
npx playwright show-report
Correr galería completa
bash
Copiar
Editar
npm run gallery
Salida de artefactos
Imágenes: docs/visuals/*.png

Zips generados (si está el script zip:visuals):

tests/__artifacts__/visuals_YYYYMMDD_HHMMSS.zip

tests/__artifacts__/report_YYYYMMDD_HHMMSS.zip

Variables útiles
CHAT_PATH=/chat (por defecto)

PLAYWRIGHT_BASE_URL=https://tu-sitio.com (para correr contra entorno externo)

PLAYWRIGHT_LOGIN_PATH=/login, PLAYWRIGHT_LOGIN_USER, PLAYWRIGHT_LOGIN_PASS (login opcional en specs)

SCREENSHOTS_ROUTES="/ruta1,/ruta2,..."

SCREENSHOTS_TIMEOUT_MS=180000 (para alargar timeout de la suite)

Errores comunes
404 al entrar directo a rutas SPA: usa el helper gotoSpa() en los specs.

(TS) Relative import paths need explicit file extensions: agrega .js al import relativo (NodeNext).

No carga data: asegúrate de que los mocks (tests/e2e/mocks/*.ts) están ruteando las llamadas que hace tu UI (page.route("**/api/...")).

Scripts disponibles
npm run screenshots → corre tests/visual/screenshots.spec.ts + zipea.

npm run gallery → corre tests/visual/gallery.spec.ts + zipea.

npm run screenshots:harness → rutas de harness (ver package.json).