# backend/services/email_service.py

import smtplib
from email.mime.text import MIMEText
from backend.config.settings import settings  # ✅ Corrección: ruta del archivo settings.py

def enviar_correo(asunto, cuerpo, destinatario=None):
    try:
        destinatario = destinatario or settings.email_to

        mensaje = MIMEText(cuerpo, "plain")
        mensaje["Subject"] = asunto
        mensaje["From"] = settings.email_from
        mensaje["To"] = destinatario

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.email_from, destinatario, mensaje.as_string())

        print("✅ Correo enviado correctamente.")
        return True

    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")
        return False