"""Twilio Verify helpers for optional SMS two-factor authentication."""

import os
import re
import streamlit as st

try:
    from twilio.rest import Client
except ImportError:
    Client = None


# AI assistance was used to help implement and debug the Twilio Verify
# integration using the official Twilio documentation.

TWILIO_PLACEHOLDERS = {
    "put_your_twilio_account_sid_here",
    "put_your_twilio_auth_token_here",
    "put_your_twilio_verify_service_sid_here",
}

PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def get_twilio_settings():
    """Read Twilio settings from Streamlit secrets or environment variables."""
    try:
        account_sid = st.secrets.get("TWILIO_ACCOUNT_SID", "")
        auth_token = st.secrets.get("TWILIO_AUTH_TOKEN", "")
        service_sid = st.secrets.get("TWILIO_VERIFY_SERVICE_SID", "")
    except Exception:
        account_sid = auth_token = service_sid = ""

    return {
        "account_sid": account_sid or os.getenv("TWILIO_ACCOUNT_SID", ""),
        "auth_token": auth_token or os.getenv("TWILIO_AUTH_TOKEN", ""),
        "service_sid": service_sid or os.getenv("TWILIO_VERIFY_SERVICE_SID", ""),
    }


def is_twilio_configured():
    """Return True when Twilio Verify settings look usable."""
    settings = get_twilio_settings()

    return (
        Client is not None
        and bool(settings["account_sid"])
        and bool(settings["auth_token"])
        and bool(settings["service_sid"])
        and settings["account_sid"] not in TWILIO_PLACEHOLDERS
        and settings["auth_token"] not in TWILIO_PLACEHOLDERS
        and settings["service_sid"] not in TWILIO_PLACEHOLDERS
    )


def normalise_or_validate_phone_number(phone_number):
    """Return a clean E.164 phone number or a safe validation error."""
    clean_phone = str(phone_number or "").strip().replace(" ", "")

    if not clean_phone:
        return False, "", "Enter a mobile number in international format."

    if not PHONE_PATTERN.fullmatch(clean_phone):
        return (
            False,
            "",
            "Use international E.164 format, for example +23057953519.",
        )

    return True, clean_phone, "Phone number format is valid."


def mask_phone_number(phone_number):
    """Hide the middle of a phone number before showing it in the UI."""
    clean_phone = str(phone_number or "").strip()

    if len(clean_phone) <= 7:
        return "Configured"

    return f"{clean_phone[:4]}*****{clean_phone[-3:]}"


def _get_verify_client():
    """Create a Twilio client only after configuration checks pass."""
    if Client is None:
        return None, None, "Twilio is not installed. Run: pip install twilio"

    if not is_twilio_configured():
        return None, None, "Twilio Verify is not configured yet."

    settings = get_twilio_settings()
    client = Client(settings["account_sid"], settings["auth_token"])
    return client, settings["service_sid"], ""


def send_two_factor_code(phone_number):
    """Start an SMS verification through Twilio Verify."""
    phone_valid, clean_phone, phone_message = normalise_or_validate_phone_number(
        phone_number
    )

    if not phone_valid:
        return False, phone_message

    client, service_sid, config_message = _get_verify_client()

    if client is None:
        return False, config_message

    try:
        verification = client.verify.v2.services(service_sid).verifications.create(
            to=clean_phone,
            channel="sms",
        )
    except Exception:
        return False, "The SMS verification code could not be sent."

    if verification.status in {"pending", "approved"}:
        return True, "A verification code has been sent by SMS."

    return False, "Twilio could not start the SMS verification."


def check_two_factor_code(phone_number, code):
    """Ask Twilio Verify whether the submitted SMS code is approved."""
    phone_valid, clean_phone, phone_message = normalise_or_validate_phone_number(
        phone_number
    )

    if not phone_valid:
        return False, phone_message

    clean_code = str(code or "").strip()

    if not clean_code:
        return False, "Enter the SMS verification code."

    client, service_sid, config_message = _get_verify_client()

    if client is None:
        return False, config_message

    try:
        verification_check = client.verify.v2.services(
            service_sid
        ).verification_checks.create(
            to=clean_phone,
            code=clean_code,
        )
    except Exception:
        return False, "The SMS verification code could not be checked."

    if verification_check.status == "approved":
        return True, "SMS verification approved."

    return False, "The SMS verification code was not approved."
