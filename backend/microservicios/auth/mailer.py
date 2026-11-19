"""Envio de correos (solo recuperacion de contrasena por ahora).

MAIL_MODE=log  (por defecto): no envia nada; escribe el enlace en los logs del
               servicio. Sirve para desarrollo y para la demo sin SMTP.
MAIL_MODE=smtp: envia por SMTP con SMTP_HOST, SMTP_PORT, SMTP_USER,
               SMTP_PASSWORD, SMTP_FROM y SMTP_STARTTLS (true/false).
"""
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Protocol

logger = logging.getLogger("auth.mailer")


class Mailer(Protocol):
    def send_password_reset(self, to_email: str, link: str) -> None: ...


class LogMailer:
    def send_password_reset(self, to_email: str, link: str) -> None:
        logger.warning("[MAIL_MODE=log] Enlace de recuperacion para %s: %s", to_email, link)


class SmtpMailer:
    def send_password_reset(self, to_email: str, link: str) -> None:
        host = os.environ["SMTP_HOST"]
        port = int(os.getenv("SMTP_PORT", "587"))
        sender = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "no-reply@localhost"))
        msg = EmailMessage()
        msg["Subject"] = "Restablece tu contrasena"
        msg["From"] = sender
        msg["To"] = to_email
        msg.set_content(
            "Recibimos una solicitud para restablecer tu contrasena.\n\n"
            f"Abre este enlace (vale 1 hora):\n{link}\n\n"
            "Si no fuiste tu, ignora este mensaje."
        )
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            if os.getenv("SMTP_STARTTLS", "true").lower() == "true":
                smtp.starttls()
            user = os.getenv("SMTP_USER")
            if user:
                smtp.login(user, os.getenv("SMTP_PASSWORD", ""))
            smtp.send_message(msg)


def get_mailer() -> Mailer:
    return SmtpMailer() if os.getenv("MAIL_MODE", "log").lower() == "smtp" else LogMailer()
