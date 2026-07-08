"""Password recovery logic shared by the Gatekeeper Streamlit home page."""

import secrets
import time
import streamlit as st
from app_model import db, schema, users
from app_model.email_service import (
    is_local_reset_fallback_enabled,
    send_password_reset_email,
)
from app_model.security import get_password_errors
from main import generate_hash, is_valid_hash


RESET_STATE_KEY = "password_reset_request"
RESET_CODE_LIFETIME_SECONDS = 10 * 60


def request_reset_code(identifier):
    """Create and email a temporary reset code ."""
    identifier = identifier.strip()

    if not identifier:
        return False, "Please enter your username or recovery email.", None

    st.session_state.pop(RESET_STATE_KEY, None)

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user_by_username_or_email(conn, identifier)
        finally:
            conn.close()
    except Exception:
        return False, "Account recovery is temporarily unavailable.", None

    if user is None:
        return (
            False,
            "Recovery could not be started. Check the username or email and try again.",
            None,
        )

    if not user["email"]:
        return (
            False,
            "This account has no recovery email. Contact an administrator or "
            "add an email from Profile after signing in.",
            None,
        )

    reset_code = f"{secrets.randbelow(900000) + 100000:06d}"
    st.session_state[RESET_STATE_KEY] = {
        "username": user["username"],
        "code": reset_code,
        "created_at": time.time(),
    }

    email_sent, email_message = send_password_reset_email(
        user["email"],
        reset_code,
    )

    if email_sent:
        return True, "A reset code has been sent to your recovery email.", None

    if is_local_reset_fallback_enabled():
        return (
            True,
            "Email delivery is unavailable. For local testing, use the "
            "recovery code below.",
            reset_code,
        )

    st.session_state.pop(RESET_STATE_KEY, None)
    return False, email_message, None


def get_reset_username():
    """Return the username held by the active reset request."""
    reset_request = st.session_state.get(RESET_STATE_KEY)
    return reset_request["username"] if reset_request else ""


def clear_reset_request():
    """Remove any active recovery code from this browser session."""
    st.session_state.pop(RESET_STATE_KEY, None)


def reset_password(username, reset_code, new_password, confirm_password):
    """Validate a reset request and securely save a replacement password."""
    username = username.strip()
    reset_code = reset_code.strip()

    if not username or not reset_code or not new_password or not confirm_password:
        return False, "Please complete all reset fields."

    reset_request = st.session_state.get(RESET_STATE_KEY)

    if reset_request is None:
        return False, "Request a new reset code before changing the password."

    if time.time() - reset_request["created_at"] > RESET_CODE_LIFETIME_SECONDS:
        st.session_state.pop(RESET_STATE_KEY, None)
        return False, "The reset code has expired. Please request a new one."

    username_matches = secrets.compare_digest(
        username,
        reset_request["username"],
    )
    code_matches = secrets.compare_digest(reset_code, reset_request["code"])

    if not username_matches or not code_matches:
        return False, "The username or reset code is incorrect."

    if new_password != confirm_password:
        return False, "The new passwords do not match."

    if get_password_errors(new_password):
        return (
            False,
            "The new password does not meet the required rules. Check the "
            "password feedback above.",
        )

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user(conn, username)

            if user is None:
                return False, "The account could not be found."

            if is_valid_hash(new_password, user["password_hash"]):
                return (
                    False,
                    "The new password must be different from your current password.",
                )

            new_password_hash = generate_hash(new_password)

            if not users.update_password(conn, username, new_password_hash):
                return False, "The password could not be updated."
        finally:
            conn.close()
    except Exception:
        return False, "The password could not be updated. Please try again."

    st.session_state.pop(RESET_STATE_KEY, None)
    return True, "Password reset successfully. You can now log in."
