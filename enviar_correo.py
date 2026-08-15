import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import config


def enviar_correo(asunto, cuerpo, adjunto=None, destino=None):
    destino = destino or config.CORREO_DESTINO
    if not (config.SMTP_USER and config.SMTP_PASSWORD):
        raise RuntimeError("Faltan SMTP_USER / SMTP_PASSWORD (variables de entorno).")
    if not destino:
        raise RuntimeError("No hay CORREO_DESTINO configurado.")

    msg = MIMEMultipart()
    msg["From"] = config.CORREO_ORIGEN or config.SMTP_USER
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

    if adjunto:
        nombre = Path(adjunto).name
        with open(adjunto, "rb") as f:
            img = MIMEImage(f.read())
        img.add_header("Content-Disposition", "attachment", filename=nombre)
        msg.attach(img)

    with smtplib.SMTP(config.SMTP_HOST, int(config.SMTP_PORT)) as servidor:
        servidor.starttls()
        servidor.login(config.SMTP_USER, config.SMTP_PASSWORD)
        servidor.sendmail(msg["From"], [destino], msg.as_string())
    return destino
