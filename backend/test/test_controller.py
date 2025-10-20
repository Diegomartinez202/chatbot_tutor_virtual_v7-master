from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from backend.dependencies.auth import require_role
from backend.services.log_service import log_access
from backend.utils.file_utils import save_csv_s3_and_local
import time
import subprocess
import requests
import io

router = APIRouter()

# 🔹 1. Ejecutar todos los tests (test_all.sh)
@router.post("/admin/test-all", summary="🧪 Ejecutar pruebas del sistema")
def ejecutar_test_general(request: Request, payload=Depends(require_role(["admin"]))):
    start_time = time.time()

    try:
        resultado = subprocess.run(["bash", "scripts/test_all.sh"], capture_output=True, text=True)
        duracion = round(time.time() - start_time, 2)

        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=200 if resultado.returncode == 0 else 500,
            ip=request.state.ip,
            user_agent=request.state.user_agent
        )

        return {
            "success": resultado.returncode == 0,
            "message": resultado.stdout,
            "error": resultado.stderr if resultado.returncode != 0 else None,
            "duracion": f"{duracion}s"
        }

    except Exception as e:
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=500,
            ip=request.state.ip,
            user_agent=request.state.user_agent
        )
        return {"success": False, "message": "Error ejecutando test", "error": str(e)}


# 🔹 2. Test de conexión al backend
@router.get("/admin/ping", summary="🟢 Test de conexión al backend")
def ping_backend(request: Request, payload=Depends(require_role(["admin"]))):
    log_access(
        user_id=payload["_id"],
        email=payload["email"],
        rol=payload["rol"],
        endpoint=str(request.url.path),
        method=request.method,
        status=200,
        ip=request.state.ip,
        user_agent=request.state.user_agent
    )
    return {"message": "✅ Backend activo", "pong": True}


# 🔹 3. Verificar estado de Rasa
@router.get("/admin/rasa/status", summary="🤖 Verificar conexión con Rasa")
def status_rasa(request: Request, payload=Depends(require_role(["admin"]))):
    try:
        response = requests.get("http://rasa:5005/status")
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=response.status_code,
            ip=request.state.ip,
            user_agent=request.state.user_agent
        )
        return {
            "success": response.status_code == 200,
            "rasa_status": response.json()
        }

    except Exception as e:
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=500,
            ip=request.state.ip,
            user_agent=request.state.user_agent
        )
        return {
            "success": False,
            "message": "❌ No se pudo conectar con Rasa",
            "error": str(e)
        }


# 🔹 4. Exportar resultados de test como CSV
@router.get("/admin/exportaciones/tests", summary="📤 Exportar resultados de test_all.sh como CSV")
def exportar_resultados_test(request: Request, payload=Depends(require_role(["admin"]))):
    try:
        start_time = time.time()
        resultado = subprocess.run(["bash", "scripts/test_all.sh"], capture_output=True, text=True)
        duracion = round(time.time() - start_time, 2)

        csv_text = "resultado,test,duracion\n"
        csv_text += f"{'OK' if resultado.returncode == 0 else 'FALLÓ'}," \
                    f"{repr(resultado.stdout).replace(',', ' ')[:100]}," \
                    f"{duracion}s\n"

        csv_bytes, archivo_url = save_csv_s3_and_local(csv_text, filename_prefix="resultados_test")

        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=200,
            ip=request.state.ip,
            user_agent=request.state.user_agent
        )

        return StreamingResponse(
            csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=resultados_test.csv"}
        )

    except Exception as e:
        log_access(
            user_id=payload["_id"],
            email=payload["email"],
            rol=payload["rol"],
            endpoint=str(request.url.path),
            method=request.method,
            status=500,
            ip=request.state.ip,
            user_agent=request.state.user_agent
        )
        return {"success": False, "error": str(e)}
@router.get("/admin/test-s3", summary="☁️ Verificar conexión con S3")
def verificar_conexion_s3(request: Request, payload=Depends(require_role(["admin"]))):
    from backend.config.settings import settings
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_s3_region,
            endpoint_url=settings.aws_s3_endpoint_url,
        )
        # Verifica acceso al bucket
        s3.head_bucket(Bucket=settings.aws_s3_bucket_name)
        return {"success": True, "message": "✅ Conexión exitosa a S3 y bucket disponible"}

    except (BotoCoreError, ClientError) as e:
        return {"success": False, "message": "❌ Error de conexión con S3", "error": str(e)}