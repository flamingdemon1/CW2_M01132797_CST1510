"""Protected Gatekeeper profile and account security page."""

import streamlit as st

from app_model import db, schema, ui, users
from app_model.security import (
    display_password_strength,
    get_password_errors,
    is_valid_email,
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

with st.form("recovery_email_form"):
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
    "Change password",
    "Confirm your current password before setting a new one.",
)
ui.section_card(
    "🔐 Password security",
    "The new password uses the same validation rules and bcrypt hashing as registration.",
    accent="amber",
)
st.write("")

with st.container(border=True):
    current_password = st.text_input(
        "Current password",
        type="password",
        key="profile_current_password",
    )
    new_password = st.text_input(
        "New password",
        type="password",
        key="profile_new_password",
    )
    display_password_strength(new_password)

    with st.form(
        "profile_password_submit_form",
        enter_to_submit=True,
        border=False,
    ):
        confirm_password = st.text_input(
            "Confirm new password",
            type="password",
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
