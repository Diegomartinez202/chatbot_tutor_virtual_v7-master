# =====================================================
# 🧩 backend/services/email_service.py
# =====================================================
import smtplib
from email.mime.text import MIMEText
from typing import Optional
from backend.config.settings import settings
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def enviar_correo(asunto: str, cuerpo: str, destinatario: Optional[str] = None) -> bool:
    """
    Envía un correo de texto plano usando configuración SMTP del sistema.
    Mantiene la lógica original, agregando validaciones, trazabilidad y seguridad.

    Parámetros:
        asunto (str): Asunto del correo.
        cuerpo (str): Contenido del mensaje.
        destinatario (str, opcional): Dirección de destino. Si no se proporciona,
                                      usa settings.email_to.
    Retorna:
        bool: True si el correo fue enviado correctamente, False en caso de error.
    """
    try:
        destinatario_final = destinatario or getattr(settings, "email_to", None)
        if not destinatario_final:
            raise ValueError("No se especificó destinatario (email_to no configurado).")

        remitente = getattr(settings, "email_from", None)
        if not remitente:
            raise ValueError("No se especificó remitente (email_from no configurado).")

        smtp_server = getattr(settings, "smtp_server", None)
        smtp_port = getattr(settings, "smtp_port", 587)
        smtp_user = getattr(settings, "smtp_user", None)
        smtp_pass = getattr(settings, "smtp_pass", None)

        if not all([smtp_server, smtp_user, smtp_pass]):
            raise RuntimeError("Faltan credenciales SMTP en settings.py.")

        # Construcción del mensaje MIME
        mensaje = MIMEText(cuerpo or "", "plain", "utf-8")
        mensaje["Subject"] = asunto or "(sin asunto)"
        mensaje["From"] = remitente
        mensaje["To"] = destinatario_final

        # Conexión y envío
        logger.debug(f"[email_service] Conectando a SMTP {smtp_server}:{smtp_port}")
        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, [destinatario_final], mensaje.as_string())

        logger.info(f"✅ Correo enviado correctamente a {destinatario_final}")
        return True

    except Exception as e:
        logger.error(f"❌ Error al enviar el correo: {e}", exc_info=True)
        return False