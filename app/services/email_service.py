import asyncio
from typing import Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.sender_email = settings.BREVO_SENDER_EMAIL
        self.sender_name = settings.BREVO_SENDER_NAME

    def _sync_send(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None):
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

        return api_instance.send_transac_email(send_smtp_email)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> bool:
        if not self.api_key or not self.sender_email:
            logger.warning("Brevo API key or sender email not configured. Skipping email dispatch.")
            return True

        for attempt in range(1, max_retries + 1):
            try:
                # Run blocking network call in background threadpool to keep event loop free
                await asyncio.to_thread(
                    self._sync_send, to_email, subject, html_content, text_content
                )
                logger.info(f"Email sent successfully to {to_email}")
                return True
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed sending email to {to_email}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * attempt)
                else:
                    logger.error(f"Failed to send email to {to_email} after {max_retries} attempts.")
                    return False
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
