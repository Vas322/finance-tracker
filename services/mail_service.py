import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


def send_reset_email(to_email: str, reset_link: str) -> bool:
    subject = 'Восстановление пароля — Финансовый трекер'
    body = f"""Здравствуйте!

Вы запросили восстановление пароля для Финансового трекера.

Для сброса пароля перейдите по ссылке:
{reset_link}

Ссылка действительна в течение 1 часа.

Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.

--
Финансовый трекер
"""

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM
    msg['To'] = to_email
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=ctx) as server:
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.MAIL_FROM, to_email, msg.as_string())
        return True
    except Exception:
        return False
