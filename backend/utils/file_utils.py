# 📁 backend/utils/file_utils.py

import os
import io
from datetime import datetime
from backend.config.settings import settings
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def save_csv_s3_and_local(csv_text: str, filename_prefix: str = "export") -> tuple[io.BytesIO, str]:
    """
    ✅ Sube un CSV a Amazon S3 y opcionalmente lo guarda en local si settings.debug == True
    """
    fecha_actual = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{filename_prefix}_{fecha_actual}.csv"

    csv_bytes = io.BytesIO(csv_text.encode("utf-8"))
    csv_bytes.seek(0)

    # ✅ NUEVO BLOQUE: si S3 está deshabilitado, forzar modo local
    if not getattr(settings, "s3_enabled", False):
        local_dir = os.path.join(settings.static_dir, "exports")
        os.makedirs(local_dir, exist_ok=True)
        local_path = os.path.join(local_dir, filename)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(csv_text)
        archivo_url = f"/static/exports/{filename}"  # URL local accesible desde FastAPI
        return csv_bytes, archivo_url

    # ✅ (resto del código original)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_s3_region,
        endpoint_url=settings.aws_s3_endpoint_url
    )
    try:
        s3_client.upload_fileobj(
            csv_bytes,
            settings.aws_s3_bucket_name,
            f"exports/{filename}",
            ExtraArgs={"ContentType": "text/csv", "ACL": "public-read"}
        )
        archivo_url = f"https://{settings.aws_s3_bucket_name}.s3.{settings.aws_s3_region}.amazonaws.com/exports/{filename}"
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"❌ Error al subir a S3: {e}")

    # 💾 Guardar local si debug
    if settings.debug:
        try:
            local_dir = os.path.join(settings.static_dir, "exports")
            os.makedirs(local_dir, exist_ok=True)
            with open(os.path.join(local_dir, filename), "w", encoding="utf-8") as f:
                f.write(csv_text)
        except Exception as e:
            print(f"⚠️ Error al guardar localmente: {e}")

    csv_bytes.seek(0)
    return csv_bytes, archivo_url


# ─────────────────────────────────────────────────────────────
# Compatibilidad: alias esperado por backend.services/log_service.py
# (No elimina lógica: solo expone el nombre histórico)
# ─────────────────────────────────────────────────────────────
def save_csv_to_s3_and_get_url(csv_text: str, filename_prefix: str = "export") -> str:
    """
    Compat: devuelve solo la URL, manteniendo la firma esperada.
    Invoca internamente a save_csv_s3_and_local.
    """
    _bytes, url = save_csv_s3_and_local(csv_text, filename_prefix=filename_prefix)
    return url
