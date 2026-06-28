"""Gatekeeper email-based password recovery page."""

import secrets
import time

import streamlit as st

from app_model import db, schema, ui, users
from app_model.email_service import (
    is_demo_mode_enabled,
    is_sendgrid_configured,
    send_password_reset_email,
)
from app_model.security import display_password_strength, get_password_errors
from main import generate_hash, is_valid_hash


RESET_STATE_KEY = "password_reset_request"
RESET_CODE_LIFETIME_SECONDS = 10 * 60
GATEKEEPER_LOGO_PATH = "assets/logos/gatekeeper_logo.png"


st.set_page_config(
    page_title="Forgot Password",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ui.apply_theme()


def request_reset_code(username):
    """Create and send a reset code for an account with a recovery email."""
    username = username.strip()

    if not username:
        return False, "Please enter your username.", None

    # A fresh request replaces any older code held in this browser session.
    st.session_state.pop(RESET_STATE_KEY, None)

    conn = db.get_connection()
    schema.create_user_table(conn)

    try:
        user = users.get_user(conn, username)
    finally:
        conn.close()

    if user is None:
        return (
            False,
            "Recovery could not be started. Check the username and try again.",
            None,
        )

    if not user["email"]:
        return (
            False,
            "This account has no recovery email. Log in and add one from the "
            "Profile page, or contact the system administrator.",
            None,
        )

    reset_code = f"{secrets.randbelow(900000) + 100000:06d}"
    st.session_state[RESET_STATE_KEY] = {
        "username": username,
        "code": reset_code,
        "created_at": time.time(),
    }

    email_sent, email_message = send_password_reset_email(
        user["email"],
        reset_code,
    )

    if email_sent:
        return True, "A reset code has been sent to your recovery email.", None

    if is_demo_mode_enabled():
        # Coursework fallback: keep the reset flow testable without live email.
        fallback_message = (
            f"{email_message} You can still continue the demo with the code below."
        )
        return True, fallback_message, reset_code

    st.session_state.pop(RESET_STATE_KEY, None)
    return False, email_message, None


def reset_password(username, reset_code, new_password, confirm_password):
    """Validate the active reset request and securely replace the password."""
    username = username.strip()
    reset_code = reset_code.strip()

    if not username or not reset_code or not new_password or not confirm_password:
        return False, "Please complete all reset fields."

    reset_request = st.session_state.get(RESET_STATE_KEY)

    if reset_request is None:
        return False, "Request a new reset code before changing the password."

    code_age = time.time() - reset_request["created_at"]

    if code_age > RESET_CODE_LIFETIME_SECONDS:
        st.session_state.pop(RESET_STATE_KEY, None)
        return False, "The reset code has expired. Please request a new one."

    username_matches = secrets.compare_digest(
        username,
        reset_request["username"],
    )
    code_matches = secrets.compare_digest(
        reset_code,
        reset_request["code"],
    )

    if not username_matches or not code_matches:
        return False, "The username or reset code is incorrect."

    if new_password != confirm_password:
        return False, "The new passwords do not match."

    if get_password_errors(new_password):
        return (
            False,
            "The new password does not meet the required rules. "
            "Please check the password feedback above.",
        )

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

    st.session_state.pop(RESET_STATE_KEY, None)
    return True, "Password reset successfully. You can now log in."


ui.page_header(
    "Forgot Password",
    "Recover access using the email linked to your Gatekeeper account",
    status="RECOVERY MODE",
    status_accent="amber",
    logo_path=GATEKEEPER_LOGO_PATH,
    logo_text="🔐",
    logo_alt="Gatekeeper password recovery logo",
)

sendgrid_ready = is_sendgrid_configured()
demo_mode_enabled = is_demo_mode_enabled()

if sendgrid_ready:
    status_title = "Email delivery ready"
    status_body = "SendGrid is configured and will be used for reset emails."
    status_accent = "green"
elif demo_mode_enabled:
    status_title = "Email delivery unavailable"
    status_body = "Demo codes will be shown when a valid account requests a reset."
    status_accent = "amber"
else:
    status_title = "Email setup required"
    status_body = "SendGrid is not configured and on-screen demo codes are disabled."
    status_accent = "red"

ui.status_card(
    status_title,
    status_body,
    accent=status_accent,
)

ui.section_heading(
    "Request reset code",
    "Enter the username for the account you need to recover.",
)
ui.section_card(
    "Email verification",
    "Gatekeeper sends a six-digit code to the recovery email stored on the account.",
    accent="blue",
)

with st.form(
    "request_reset_code_form",
    enter_to_submit=True,
    border=True,
):
    request_username = st.text_input(
        "Username",
        key="forgot_request_username",
    )
    request_submitted = st.form_submit_button(
        "Send reset code",
        type="primary",
        icon=":material/outgoing_mail:",
        use_container_width=True,
    )

if request_submitted:
    request_started, request_message, demo_code = request_reset_code(
        request_username
    )

    if request_started:
        if demo_code is None:
            st.success(request_message)
        else:
            st.warning(request_message)
            st.code(demo_code, language=None)
            st.caption("This code is shown because demo mode is enabled.")
    else:
        st.error(request_message)


ui.section_heading(
    "Set a new password",
    "Enter the code and choose a password that passes the shared security checks.",
)
ui.section_card(
    "Secure password reset",
    "Reset codes expire after ten minutes and are removed after a successful reset.",
    accent="amber",
)

with st.container(border=True):
    reset_username = st.text_input(
        "Username",
        key="forgot_reset_username",
    )
    entered_code = st.text_input(
        "Six-digit reset code",
        max_chars=6,
        key="forgot_reset_code",
    )
    new_password = st.text_input(
        "New password",
        type="password",
        key="forgot_new_password",
    )
    display_password_strength(new_password)

    # Enter submits only from the final password-confirmation step.
    with st.form(
        "password_reset_submit_form",
        enter_to_submit=True,
        border=False,
    ):
        confirm_password = st.text_input(
            "Confirm new password",
            type="password",
            key="forgot_confirm_password",
        )
        reset_submitted = st.form_submit_button(
            "Reset password",
            type="primary",
            icon=":material/lock_reset:",
            use_container_width=True,
        )

if reset_submitted:
    password_reset, reset_message = reset_password(
        reset_username,
        entered_code,
        new_password,
        confirm_password,
    )

    if password_reset:
        st.success(reset_message)
    else:
        st.error(reset_message)


st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

if st.button("Back to login", icon=":material/login:"):
    st.switch_page("home.py")
