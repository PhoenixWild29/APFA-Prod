import hashlib
import logging

import resend

logger = logging.getLogger(__name__)

VERIFICATION_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:40px 0">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1)">
<tr><td style="background-color:#0f172a;padding:24px 32px">
<h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:600">APFA</h1>
</td></tr>
<tr><td style="padding:32px">
<h2 style="margin:0 0 16px;color:#0f172a;font-size:22px">Verify your email</h2>
<p style="margin:0 0 8px;color:#374151;font-size:15px;line-height:1.6">Hi {username},</p>
<p style="margin:0 0 24px;color:#374151;font-size:15px;line-height:1.6">Thank you for signing up for APFA. Click the button below to verify your email and activate your account.</p>
<table cellpadding="0" cellspacing="0" style="margin:0 auto 24px"><tr><td>
<a href="{verification_url}" style="display:inline-block;background-color:#1D8A84;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;padding:12px 32px;border-radius:8px">Verify My Email</a>
</td></tr></table>
<p style="margin:0 0 8px;color:#6b7280;font-size:13px;line-height:1.5">This link expires in {expiry_hours} hours.</p>
<p style="margin:0 0 24px;color:#6b7280;font-size:13px;line-height:1.5">If you didn't create an account, you can safely ignore this email.</p>
<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
<p style="margin:0;color:#9ca3af;font-size:11px">If the button doesn't work, copy and paste this URL into your browser:</p>
<p style="margin:4px 0 0;color:#9ca3af;font-size:11px;word-break:break-all">{verification_url}</p>
</td></tr>
<tr><td style="background-color:#f9fafb;padding:16px 32px;text-align:center">
<p style="margin:0;color:#9ca3af;font-size:11px">APFA &mdash; Your AI Financial Research Assistant</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

WELCOME_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:40px 0">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1)">
<tr><td style="background-color:#0f172a;padding:24px 32px">
<h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:600">APFA</h1>
</td></tr>
<tr><td style="padding:32px">
<h2 style="margin:0 0 16px;color:#0f172a;font-size:22px">Welcome to APFA!</h2>
<p style="margin:0 0 8px;color:#374151;font-size:15px;line-height:1.6">Hi {username},</p>
<p style="margin:0 0 24px;color:#374151;font-size:15px;line-height:1.6">Your account is now active. You can start using APFA to get AI-powered financial research and insights.</p>
<table cellpadding="0" cellspacing="0" style="margin:0 auto 24px"><tr><td>
<a href="{app_url}" style="display:inline-block;background-color:#1D8A84;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;padding:12px 32px;border-radius:8px">Get Started</a>
</td></tr></table>
</td></tr>
<tr><td style="background-color:#f9fafb;padding:16px 32px;text-align:center">
<p style="margin:0;color:#9ca3af;font-size:11px">APFA &mdash; Your AI Financial Research Assistant</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def hash_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class EmailService:
    def __init__(self, api_key: str, from_address: str):
        self.from_address = from_address
        self._configured = bool(api_key)
        if self._configured:
            resend.api_key = api_key

    def send_verification_email(
        self,
        to_email: str,
        username: str,
        verification_url: str,
        expiry_hours: int = 24,
    ) -> bool:
        html = VERIFICATION_EMAIL_HTML.format(
            username=username,
            verification_url=verification_url,
            expiry_hours=expiry_hours,
        )
        return self._send(to_email, "Verify your APFA account", html)

    def send_welcome_email(self, to_email: str, username: str, app_url: str) -> bool:
        html = WELCOME_EMAIL_HTML.format(username=username, app_url=app_url)
        return self._send(to_email, "Welcome to APFA!", html)

    def _send(self, to: str, subject: str, html: str) -> bool:
        if not self._configured:
            _clean = str(to).replace("\n", "").replace("\r", "")[:200]
            logger.warning(
                f"Email not configured (RESEND_API_KEY empty) -- skipping send to {_clean}"
            )
            return False
        try:
            resend.Emails.send(
                {
                    "from": self.from_address,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
            )
            _clean = str(to).replace("\n", "").replace("\r", "")[:200]
            logger.info(f"Email sent: subject={subject!r} to={_clean}")
            return True
        except Exception as e:
            _clean = str(to).replace("\n", "").replace("\r", "")[:200]
            logger.error(f"Failed to send email to {_clean}: {e}")
            return False


def _get_email_service():
    from app.config import settings

    return EmailService(
        api_key=settings.resend_api_key,
        from_address=settings.email_from,
    )


email_service: EmailService | None = None


def get_email_service() -> EmailService:
    global email_service
    if email_service is None:
        email_service = _get_email_service()
    return email_service
