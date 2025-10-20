# README-solution — Solución VS2022 + Tareas

Este documento resume **cómo está organizada la solución (.sln)**, **cómo lanzar con F5**, **dónde ver el Task Runner** y **dónde están los Solution Items**.

---

## 1) Estructura de la solución

- **ChatbotTutorVirtual.sln**
  - **backend** (Python, `backend\backend.pyproj`)
    - *Startup file:* `main.py`
    - *Working dir:* `..\`
    - *Args:* `-m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000`
    - *Interpreter:* `.venv\Scripts\python.exe`
  - **frontend/** (Solution Folder)
    - *Solution Items:*
      - `README-frontend.md`
      - `run_frontend.bat`
      - `run_all.bat`
    - *(Opcional)* Proyecto **admin_panel_react** (Node) si se agregó “From Existing Node.js code”.

> Nota: los GUIDs de proyectos los gestiona VS automáticamente.

---

## 2) Lanzar con F5 (backend)

1. Abrir `ChatbotTutorVirtual.sln` en VS2022.  
2. En **Solution Explorer** → clic derecho **backend** → **Set as Startup Project**.  
3. Presionar **F5**.  
4. Abrir Swagger: `http://127.0.0.1:8000/docs`.

**Logs / salida**: *View → Output* (seleccionar “Python” o “Debug”).  
**Confiar en el venv**: Si VS pregunta por binarios Python, elegir **“Confiar siempre”**.

---

## 3) Task Runner (npm run dev)

> Requiere workload **Node.js development**.

1. *View → Other Windows → Task Runner Explorer*.  
2. Seleccionar proyecto **admin_panel_react**.  
3. Script **dev** → **Run** (probar).  
4. Script **dev** → **Bindings** → marcar:
   - **Project Open** (se ejecuta al abrir la solución)
   - **After Build** (se ejecuta al compilar/ejecutar backend)

Frontend: `http://localhost:5173`

---

## 4) Solution Items (accesos directos)

En la carpeta de solución **frontend**:
- **`run_frontend.bat`** → `npm install` + `npm run dev`.  
- **`run_all.bat`** → abre 2 ventanas: backend (.venv) + frontend (Vite).  
- **`README-frontend.md`** → guía breve del panel (prerrequisitos, .env, CORS).

---

## 5) Docker (perfiles)

Archivo: `docker-compose.yml` (raíz) con perfiles:
- **build** (usa tus Dockerfiles):  
  `docker compose --profile build up -d --build`
- **vanilla** (imágenes oficiales):  
  `docker compose --profile vanilla up -d --build`

Apagar: `docker compose down`  
Logs: `docker compose --profile build logs -f backend`

---

## 6) Problemas frecuentes (rápida referencia)

- **No module named uvicorn**  
  Activar venv e instalar deps:  
  `.\.venv\Scripts\activate`  
  `python -m pip install -r backend\requirements.txt --no-cache-dir`
- **ModuleNotFoundError: backend**  
  Verificar *Working dir* del proyecto = `..\`
- **Puerto 8000 ocupado**  
  Cambiar a `--port 8010` en argumentos o liberar puerto.
- **CORS desde Vite**  
  Permitir `http://localhost:5173` y `http://127.0.0.1:5173` en FastAPI.

---

## 7) Rutas útiles (local)

- Backend (FastAPI): `http://127.0.0.1:8000/docs`  
- Frontend (Vite): `http://localhost:5173`  
- Rasa (status): `http://127.0.0.1:5005/status`

---