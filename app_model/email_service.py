"""SendGrid email helpers for Gatekeeper password recovery."""

import os

import streamlit as st


# These are the example values shown in setup instructions. Treating them as
# unconfigured prevents the app from trying to use the examples as real keys.
SENDGRID_PLACEHOLDERS = {
    "put_your_sendgrid_api_key_here",
    "put_your_verified_sender_email_here",
    "your_sendgrid_api_key_here",
    "your_verified_sender_email_here",
}


def is_local_reset_fallback_enabled():
    """Return whether local testing may show an undelivered reset code."""
    try:
        setting = st.secrets.get("ALLOW_LOCAL_RESET_FALLBACK", None)

        # Keep older local settings working while the new name is adopted.
        if setting is None:
            setting = st.secrets.get("PASSWORD_RESET_DEMO_MODE", None)
    except Exception:
        setting = None

    if setting is None:
        setting = os.getenv("ALLOW_LOCAL_RESET_FALLBACK")

    if setting is None:
        setting = os.getenv("PASSWORD_RESET_DEMO_MODE", "false")

    if isinstance(setting, bool):
        return setting

    return str(setting).strip().lower() in {"1", "true", "yes", "on"}


def is_demo_mode_enabled():
    """Backward-compatible alias for older coursework code."""
    return is_local_reset_fallback_enabled()


def get_sendgrid_settings():
    """Read SendGrid settings from Streamlit secrets or environment variables."""
    try:
        api_key = str(st.secrets.get("SENDGRID_API_KEY", "")).strip()
        from_email = str(st.secrets.get("SENDGRID_FROM_EMAIL", "")).strip()
    except Exception:
        api_key = ""
        from_email = ""

    if not api_key:
        api_key = os.getenv("SENDGRID_API_KEY", "").strip()

    if not from_email:
        from_email = os.getenv("SENDGRID_FROM_EMAIL", "").strip()

    return {
        "api_key": api_key,
        "from_email": from_email,
    }


def is_sendgrid_configured():
    """Return True when both SendGrid settings contain real values."""
    settings = get_sendgrid_settings()
    api_key = settings["api_key"]
    from_email = settings["from_email"]

    return (
        bool(api_key)
        and bool(from_email)
        and api_key not in SENDGRID_PLACEHOLDERS
        and from_email not in SENDGRID_PLACEHOLDERS
    )


def send_password_reset_email(to_email, reset_code):
    """Send a reset code and return a success flag with a safe message."""
    if not is_sendgrid_configured():
        return False, "SendGrid is not configured."

    try:
        import sendgrid
        from sendgrid.helpers.mail import Content, Email, Mail, To
    except ImportError:
        return False, "The SendGrid Python package is not installed."

    settings = get_sendgrid_settings()

    try:
        sendgrid_client = sendgrid.SendGridAPIClient(
            api_key=settings["api_key"]
        )
        from_email = Email(settings["from_email"])
        to_email = To(to_email)
        subject = "Gatekeeper Password Reset Code"
        content = Content(
            "text/plain",
            "Your Gatekeeper password reset code is: "
            f"{reset_code}\n\nThis code expires in 10 minutes. "
            "If you did not request it, you can ignore this email.",
        )
        mail = Mail(from_email, to_email, subject, content)
        response = sendgrid_client.client.mail.send.post(
            request_body=mail.get()
        )

        if 200 <= int(response.status_code) < 300:
            return True, "Reset email sent successfully."

        return False, "SendGrid did not accept the reset email."

    except Exception as error:
        status_code = getattr(error, "status_code", None)
        if status_code is None:
            status_code = getattr(error, "code", None)

        if status_code is not None:
            return False, f"SendGrid rejected the email (status {status_code})."

        return False, "The reset email could not be sent."
