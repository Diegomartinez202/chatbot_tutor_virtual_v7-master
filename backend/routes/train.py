# backend/routes/train.py
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import os, httpx

from backend.services.train_service import entrenar_y_loggear
from backend.dependencies.auth import require_role
from backend.services.log_service import log_access
from backend.config.settings import settings  # 👈 compat con .env

# ✅ Rate limiting por endpoint (no-op si SlowAPI está deshabilitado)
from backend.rate_limit import limit
# ✅ Request-ID para trazabilidad extremo a extremo (lo propagamos a GitHub)
from backend.middleware.request_id import get_request_id

router = APIRouter()

class TrainPayload(BaseModel):
    mode: Optional[Literal["local", "ci"]] = None
    branch: Optional[str] = None  # default "main"


async def _trigger_ci(branch: str = "main", request_id: Optional[str] = None):
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    workflow = os.getenv("GITHUB_WORKFLOW_FILE", "deploy-railway.yml")
    token = os.getenv("GITHUB_TOKEN_WORKFLOW")
    if not all([owner, repo, workflow, token]):
        raise HTTPException(status_code=500, detail="Faltan envs de GitHub (OWNER/REPO/WORKFLOW/TOKEN) para CI.")

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    # Propagamos trazabilidad si existe
    if request_id:
        headers["X-Request-ID"] = request_id

    payload = {"ref": branch or "main"}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=headers, json=payload)
    if r.status_code not in (201, 204):
        raise HTTPException(status_code=500, detail=f"GitHub API error: {r.status_code} {r.text}")
    return {"success": True, "mode": "ci", "message": f"Workflow {workflow} disparado en rama {payload['ref']}"}


@router.post("/admin/train", tags=["Entrenamiento"])
@limit("3/hour")  # Entrenamiento es costoso: limitar invocaciones por hora
async def entrenar_bot(
    request: Request,
    body: Optional[TrainPayload] = None,
    payload=Depends(require_role(["admin"]))
):
    mode_env = os.getenv("TRAIN_MODE", "local").lower()  # fallback global
    mode = (body.mode if body else None) or mode_env
    branch = (body.branch if body else None) or "main"
    rid = get_request_id()  # trazabilidad

    try:
        if mode == "ci":
            resultado = await _trigger_ci(branch, request_id=rid)
            ok = True
            msg = resultado["message"]
            log_path = None
        else:
            # Modo LOCAL (comportamiento actual)
            resultado = entrenar_y_loggear()
            ok = resultado.get("success", False)
            msg = "✅ Bot entrenado correctamente" if ok else "❌ Error al entrenar el bot"
            log_path = resultado.get("log_path")

        # Logging de acceso
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=200 if ok else 500,
            ip=getattr(request.state, "ip", None),
            user_agent=getattr(request.state, "user_agent", None),
            extra={"request_id": rid, "mode": mode, "branch": branch},
        )

        return {
            "success": ok,
            "mode": mode,
            "message": msg,
            "log_file": log_path,
            "request_id": rid,
        }
    except HTTPException:
        raise
    except Exception as e:
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=500,
            ip=getattr(request.state, "ip", None),
            user_agent=getattr(request.state, "user_agent", None),
            extra={"request_id": rid, "mode": mode, "branch": branch, "error": str(e)},
        )
        return {
            "success": False,
            "mode": mode,
            "message": "❌ Error al entrenar/desplegar",
            "error": str(e),
            "request_id": rid,
        }
