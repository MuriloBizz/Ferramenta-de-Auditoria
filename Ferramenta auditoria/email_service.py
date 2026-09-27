"""
email_service.py
Configuração do e-mail remetente e envio via SMTP (Gmail).
"""

import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

SMTP_USER = None
SMTP_PASSWORD = None


def configurado():
    return bool(SMTP_USER and SMTP_PASSWORD)


def configurar_email(email, senha_app):
    global SMTP_USER, SMTP_PASSWORD
    SMTP_USER = email
    SMTP_PASSWORD = senha_app


def enviar_email(destinatario, assunto, mensagem):
    if not configurado():
        raise ValueError("Configure o e-mail e a senha de aplicativo antes de enviar.")

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.set_content(mensagem)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)
