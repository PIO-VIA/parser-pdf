import aiosmtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

logger = logging.getLogger("app.services.email_service")

async def send_reset_password_email(to_email: str, reset_link: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Réinitialisation de votre mot de passe"
    message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    message["To"] = to_email

    html_content = f"""
    <html><body>
      <h2>Réinitialisation de mot de passe</h2>
      <p>Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :</p>
      <a href="{reset_link}">Réinitialiser mon mot de passe</a>
      <p>Ce lien est valable 1 heure.</p>
      <p>Si vous n'avez pas fait cette demande, ignorez cet email.</p>
    </body></html>
    """
    message.attach(MIMEText(html_content, "html"))

    # Log the email content and link for local development ease
    logger.warning(f"Reset link for {to_email}: {reset_link}")

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as e:
        logger.error(f"Failed to send reset email to {to_email} via SMTP: {str(e)}")
        # In development, we don't block the request if SMTP fails since we logged the link
        if settings.APP_ENV == "production":
            raise
