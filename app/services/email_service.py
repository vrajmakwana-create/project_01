import asyncio
from datetime import datetime
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.sender_email = settings.BREVO_SENDER_EMAIL
        self.sender_name = settings.BREVO_SENDER_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        if not self.api_key or not self.sender_email:
            logger.warning("Brevo API key or sender email not configured. Skipping email dispatch.")
            return True

        try:
            import sib_api_v3_sdk
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key["api-key"] = self.api_key

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email}],
                sender={"name": self.sender_name, "email": self.sender_email},
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

            api_instance.send_transac_email(send_smtp_email)
            return True
        except Exception as e:
            logger.error(f"Error sending email via Brevo: {e}")
            return False

    async def send_otp_email(self, to_email: str, otp: int, name: str) -> bool:
        subject = f"Verify Your Account - {settings.APP_NAME}"
        html_content = f"""
        <h2>Welcome {name}!</h2>
        <p>Your verification OTP is: <strong>{otp}</strong></p>
        <p>This code will expire in 5 minutes.</p>
        """
        return await self.send_email(to_email=to_email, subject=subject, html_content=html_content)


email_service = EmailService()
