"""Protected Gatekeeper profile and account security page."""

import streamlit as st

from app_model import db, schema, twilio_service, ui, users
from app_model.security import (
    get_password_errors,
    is_valid_email,
    live_password_input,
)
from main import generate_hash, is_valid_hash


st.set_page_config(
    page_title="Gatekeeper Profile",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="auto",
)

for key, default_value in {"logged_in": False, "username": ""}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

ui.apply_theme()
ui.sidebar_logo()
ui.sidebar_theme_control("profile")


if not st.session_state["logged_in"]:
    ui.page_header(
        "Restricted Area",
        "Authentication is required to open your Gatekeeper Profile.",
        status="ACCESS DENIED",
        status_accent="red",
    )
    st.warning("🔒 Return to Gatekeeper home and authenticate to view your profile.")
    ui.route_spacing()

    if st.button("Go to home page", icon=":material/home:"):
        st.switch_page("home.py")

    st.stop()


ui.content_profile_control()


def get_recovery_email(username):
    """Return the recovery email stored for the active account."""
    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user(conn, username)
            return user["email"] if user is not None else None
        finally:
            conn.close()
    except Exception:
        return None


def confirm_password_input(label, key):
    """Use the matching password field without strength feedback when available."""
    try:
        return live_password_input(
            label,
            key=key,
            theme=ui.get_theme(),
            show_strength=False,
        )
    except TypeError:
        # Streamlit can keep an older imported helper until the app restarts.
        return live_password_input(label, key=key, theme=ui.get_theme())


def change_recovery_email(username, new_email):
    """Validate and save a recovery email for the active account."""
    new_email = new_email.strip().lower()

    if not is_valid_email(new_email):
        return False, "Please enter a valid email address."

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            updated = users.update_email(conn, username, new_email)
        finally:
            conn.close()
    except Exception:
        return False, "The recovery email could not be updated. Please try again."

    if not updated:
        return False, "Your account could not be found. Please log in again."

    return True, "Recovery email updated successfully."


def change_password(username, current_password, new_password, confirm_password):
    """Verify the account and securely update its stored password hash."""
    if not current_password or not new_password or not confirm_password:
        return False, "Please complete all password fields."

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user(conn, username)

            if user is None:
                return False, "Your account could not be found. Please log in again."

            if not is_valid_hash(current_password, user["password_hash"]):
                return False, "The current password is incorrect."

            if new_password != confirm_password:
                return False, "The new passwords do not match."

            if is_valid_hash(new_password, user["password_hash"]):
                return (
                    False,
                    "The new password must be different from your current password.",
                )

            if get_password_errors(new_password):
                return (
                    False,
                    "The new password does not meet the required rules. Check "
                    "the password feedback above.",
                )

            updated = users.update_password(
                conn,
                username,
                generate_hash(new_password),
            )
        finally:
            conn.close()
    except Exception:
        return False, "The password could not be changed. Please try again."

    if not updated:
        return False, "The password could not be updated."

    return True, "Password changed successfully. Your session remains active."


def get_two_factor_status(username):
    """Return the active account's SMS 2FA settings."""
    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            return users.get_two_factor_status(conn, username)
        finally:
            conn.close()
    except Exception:
        return None


def save_verified_two_factor_phone(username, phone_number):
    """Save a verified phone number and enable SMS 2FA for the active user."""
    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            phone_saved = users.update_phone_number(conn, username, phone_number)
            enabled = users.set_two_factor_enabled(conn, username, True)
        finally:
            conn.close()
    except Exception:
        return False, "SMS two-factor authentication could not be enabled."

    if not phone_saved or not enabled:
        return False, "Your account could not be updated. Please log in again."

    return True, "SMS two-factor authentication is now enabled."


def disable_two_factor(username, current_password):
    """Disable SMS 2FA after confirming the current password."""
    if not current_password:
        return False, "Enter your current password before disabling SMS 2FA."

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user(conn, username)

            if user is None:
                return False, "Your account could not be found. Please log in again."

            if not is_valid_hash(current_password, user["password_hash"]):
                return False, "The current password is incorrect."

            disabled = users.set_two_factor_enabled(conn, username, False)
        finally:
            conn.close()
    except Exception:
        return False, "SMS two-factor authentication could not be disabled."

    if not disabled:
        return False, "Your account could not be updated."

    st.session_state.pop("profile_pending_2fa_phone", None)
    return True, "SMS two-factor authentication has been disabled."


ui.sidebar_user(st.session_state["username"])

if st.sidebar.button(
    "Log out",
    icon=":material/logout:",
    width="stretch",
):
    ui.logout()
    st.switch_page("home.py")


ui.page_header(
    "Profile",
    "Account details, recovery options, and session security",
    status="SECURE SESSION",
)

recovery_email = get_recovery_email(st.session_state["username"])
identity_column, status_column = st.columns(2)

with identity_column:
    ui.section_card(
        "👤 Account identity",
        f"Username: {st.session_state['username']} · Recovery email: "
        f"{recovery_email or 'Not yet provided'}",
        accent="blue",
    )

with status_column:
    ui.status_card(
        "🟢 Secure session active",
        "Your authenticated Gatekeeper session remains protected.",
        accent="green",
    )


ui.section_heading(
    "Recovery email",
    "This address receives time-limited password reset codes.",
)

with st.form("recovery_email_form", enter_to_submit=False):
    new_recovery_email = st.text_input(
        "Recovery email",
        value=recovery_email or "",
    )
    email_submitted = st.form_submit_button(
        "Update recovery email",
        icon=":material/mail:",
        width="stretch",
    )

if email_submitted:
    email_changed, email_message = change_recovery_email(
        st.session_state["username"],
        new_recovery_email,
    )

    if email_changed:
        st.success(email_message)
    else:
        st.error(email_message)


ui.section_heading(
    "SMS two-factor authentication",
    "Optional extra login protection using a Twilio Verify SMS code.",
)

two_factor_status = get_two_factor_status(st.session_state["username"])

if two_factor_status is None:
    st.error("SMS two-factor settings could not be loaded from SQLite.")
else:
    two_factor_enabled = two_factor_status["two_factor_enabled"]
    saved_phone = two_factor_status["phone_number"] or ""
    masked_phone = twilio_service.mask_phone_number(saved_phone)
    status_text = "Enabled" if two_factor_enabled else "Disabled"
    phone_text = masked_phone if saved_phone else "No verified phone number"

    ui.status_card(
        f"SMS 2FA: {status_text}",
        f"Phone status: {phone_text}",
        accent="green" if two_factor_enabled else "amber",
    )

    if not twilio_service.is_twilio_configured():
        st.warning(
            "Twilio Verify is not configured yet. SMS 2FA setup is unavailable, "
            "but the rest of your profile still works."
        )

    with st.form("profile_two_factor_send_form", enter_to_submit=False):
        phone_number = st.text_input(
            "Mobile number for SMS 2FA",
            placeholder="+23057953519",
            autocomplete="tel",
        )
        send_2fa_code = st.form_submit_button(
            "Send verification code",
            icon=":material/sms:",
            width="stretch",
            disabled=not twilio_service.is_twilio_configured(),
        )

    if send_2fa_code:
        phone_valid, clean_phone, phone_message = (
            twilio_service.normalise_or_validate_phone_number(phone_number)
        )

        if not phone_valid:
            st.error(phone_message)
        else:
            code_sent, code_message = twilio_service.send_two_factor_code(clean_phone)

            if code_sent:
                st.session_state["profile_pending_2fa_phone"] = clean_phone
                st.success(
                    "Verification code sent. Enter the code below to enable SMS 2FA."
                )
            else:
                st.error(code_message)

    pending_phone = st.session_state.get("profile_pending_2fa_phone")

    if pending_phone:
        st.caption(
            "Pending verification for "
            f"{twilio_service.mask_phone_number(pending_phone)}."
        )

        with st.form("profile_two_factor_verify_form", enter_to_submit=True):
            profile_two_factor_code = st.text_input(
                "SMS verification code",
                autocomplete="one-time-code",
            )
            verify_2fa_code = st.form_submit_button(
                "Enable SMS 2FA",
                type="primary",
                icon=":material/verified_user:",
                width="stretch",
            )

        if verify_2fa_code:
            code_approved, code_message = twilio_service.check_two_factor_code(
                pending_phone,
                profile_two_factor_code,
            )

            if code_approved:
                enabled, enable_message = save_verified_two_factor_phone(
                    st.session_state["username"],
                    pending_phone,
                )

                if enabled:
                    st.session_state.pop("profile_pending_2fa_phone", None)
                    st.success(enable_message)
                    st.rerun()
                else:
                    st.error(enable_message)
            else:
                st.error(code_message)

    if two_factor_enabled:
        with st.form("profile_two_factor_disable_form", enter_to_submit=False):
            disable_password = st.text_input(
                "Current password to disable SMS 2FA",
                type="password",
            )
            disable_2fa = st.form_submit_button(
                "Disable SMS 2FA",
                icon=":material/no_encryption:",
                width="stretch",
            )

        if disable_2fa:
            disabled, disable_message = disable_two_factor(
                st.session_state["username"],
                disable_password,
            )

            if disabled:
                st.success(disable_message)
                st.rerun()
            else:
                st.error(disable_message)


ui.section_heading(
    "Change password",
    "Confirm your current password before setting a new one.",
)
ui.section_card(
    "🔐 Password security",
    "The new password uses the same validation rules and bcrypt hashing as registration.",
    accent="amber",
)
st.write("")

with st.form(
    "profile_password_submit_form",
    enter_to_submit=False,
    border=True,
):
    current_password = st.text_input(
        "Current password",
        type="password",
        key="profile_current_password",
    )
    new_password = live_password_input(
        "New password",
        key="profile_new_password",
        theme=ui.get_theme(),
    )
    confirm_password = confirm_password_input(
        "Confirm new password",
        key="profile_confirm_password",
    )
    change_submitted = st.form_submit_button(
        "Change password",
        type="primary",
        icon=":material/lock_reset:",
        width="stretch",
    )

if change_submitted:
    password_changed, result_message = change_password(
        st.session_state["username"],
        current_password,
        new_password,
        confirm_password,
    )

    if password_changed:
        st.success(result_message)
    else:
        st.error(result_message)
