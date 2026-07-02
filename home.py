"""Gatekeeper Streamlit entry page and account access flow."""

import sqlite3

import streamlit as st

from app_model import db, schema, ui, users
from app_model.email_service import (
    is_local_reset_fallback_enabled,
    is_sendgrid_configured,
)
from app_model.recovery import (
    clear_reset_request,
    get_reset_username,
    request_reset_code,
    reset_password,
)
from app_model.security import (
    display_password_strength,
    get_password_errors,
    is_valid_email,
)
from main import generate_hash, get_username_errors, is_valid_hash


st.set_page_config(
    page_title="Gatekeeper Home",
    page_icon="assets/logos/gatekeeper_logo.png",
    layout="wide",
    initial_sidebar_state="auto",
)

for key, default_value in {
    "logged_in": False,
    "username": "",
    "auth_view": "login",
    "recovery_step": 1,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

ui.apply_theme()
ui.sidebar_logo()


def show_auth_view(view_name):
    """Switch the account panel without relying on Streamlit tabs."""
    current_view = st.session_state.get("auth_view", "login")

    if current_view == "recovery" and view_name != "recovery":
        clear_reset_request()

    if view_name == "recovery" and current_view != "recovery":
        clear_reset_request()
        st.session_state["recovery_step"] = 1
        st.session_state.pop("recovery_notice", None)
        st.session_state.pop("recovery_fallback_code", None)

    st.session_state["auth_view"] = view_name
    st.rerun()


def register_streamlit_user(username, password, email=""):
    """Register a new user in the SQLite users table."""
    username = username.strip()
    email = email.strip().lower()

    if username == "" or email == "" or password == "":
        return False, "Please enter a username, recovery email, and password."

    username_errors = get_username_errors(username)

    if username_errors:
        return False, " ".join(username_errors)

    if not is_valid_email(email):
        return False, "Please enter a valid recovery email address."

    if get_password_errors(password):
        return (
            False,
            "Password does not meet the required rules. Check the password "
            "feedback above.",
        )

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            if users.get_user(conn, username) is not None:
                return False, "This username already exists. Choose another one."

            users.add_user(conn, username, generate_hash(password), email)
        finally:
            conn.close()
    except sqlite3.IntegrityError:
        return False, "This username already exists. Choose another one."
    except Exception:
        return False, "The account could not be created. Please try again."

    return True, "Registration successful. You can now log in."


def login_streamlit_user(username, password):
    """Log in a user by checking the stored SQLite password hash."""
    username = username.strip()

    if username == "" or password == "":
        return False, "Please enter both a username and a password."

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user(conn, username)
        finally:
            conn.close()
    except Exception:
        return False, "Login is temporarily unavailable. Please try again."

    if user is None or not is_valid_hash(password, user["password_hash"]):
        return False, "Incorrect username or password."

    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    return True, "Login successful."


ui.content_profile_control()

header_status = (
    "SECURE SESSION" if st.session_state["logged_in"] else "ACCESS CONTROL READY"
)
ui.page_header(
    "Gatekeeper",
    "Cyber Incident Intelligence System",
    status=header_status,
)

if st.session_state["logged_in"]:
    ui.status_card(
        "Identity verified",
        f"Welcome, {st.session_state['username']}. Your secure session is active.",
        accent="green",
    )
    ui.section_heading("Command routes", "Choose a protected workspace.")

    dashboard_column, ai_column, profile_column, logout_column = st.columns(4)

    with dashboard_column:
        ui.command_card(
            "📊 Security Dashboard",
            "Review incident totals, trends, categories, statuses, and severity filters.",
            accent="cyan",
        )
        st.write("")
        if st.button(
            "Open dashboard",
            icon=":material/dashboard:",
            width="stretch",
        ):
            st.switch_page("pages/1_dashboard.py")

    with ai_column:
        ui.command_card(
            "🤖 SmartBoyAI",
            "Ask database-aware questions about cyber incidents and IT tickets.",
            accent="green",
        )
        st.write("")
        if st.button(
            "Open SmartBoyAI",
            icon=":material/smart_toy:",
            width="stretch",
        ):
            st.switch_page("pages/2_SmartBoyAI.py")

    with profile_column:
        ui.command_card(
            "👤 Profile & Security",
            "Review account details, recovery email, and password security.",
            accent="blue",
        )
        st.write("")
        if st.button(
            "Open profile",
            icon=":material/account_circle:",
            width="stretch",
        ):
            st.switch_page("pages/3_Profile.py")

    with logout_column:
        ui.command_card(
            "🔒 Session Control",
            "End this authenticated session and return to secure access.",
            accent="red",
        )
        st.write("")
        if st.button(
            "Log out",
            icon=":material/logout:",
            width="stretch",
        ):
            ui.logout()
            st.rerun()

    st.stop()


overview_column, access_column = st.columns([0.85, 1.15], gap="large")

with overview_column:
    ui.section_card(
        "🛡️ Protected intelligence workspace",
        "Gatekeeper brings incident monitoring, operational data, and assisted "
        "analysis into one authenticated command centre.",
        accent="cyan",
    )
    st.write("")
    ui.status_card(
        "Credential boundary active",
        "Passwords are validated and stored as secure hashes, never as plain text.",
        accent="green",
    )

with access_column:
    auth_view = st.session_state["auth_view"]

    if auth_view == "login":
        st.subheader("🔐 Secure login")
        st.caption("Authenticate to enter the Gatekeeper command centre.")

        login_notice = st.session_state.pop("login_notice", None)
        if login_notice:
            st.success(login_notice)

        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button(
                "Log in",
                type="primary",
                icon=":material/login:",
                width="stretch",
            )

        if login_submitted:
            login_successful, login_message = login_streamlit_user(
                login_username,
                login_password,
            )

            if login_successful:
                st.switch_page("pages/1_dashboard.py")
            else:
                st.error(login_message)

        st.caption("New to Gatekeeper or having trouble signing in?")
        create_column, forgot_column = st.columns(2, gap="small")

        with create_column:
            if st.button(
                "Create account",
                icon=":material/person_add:",
                width="stretch",
            ):
                show_auth_view("register")

        with forgot_column:
            if st.button(
                "Forgot password?",
                icon=":material/lock_reset:",
                width="stretch",
            ):
                show_auth_view("recovery")

    elif auth_view == "register":
        st.subheader("👤 Create secure account")
        st.caption("Password feedback updates when the password field changes.")

        with st.container(border=True):
            register_username = st.text_input(
                "New username",
                key="register_username",
            )
            register_email = st.text_input(
                "Recovery email",
                key="register_email",
            )
            register_password = st.text_input(
                "New password",
                type="password",
                key="register_password",
            )
            display_password_strength(register_password)

            with st.form(
                "registration_submit_form",
                enter_to_submit=True,
                border=False,
            ):
                register_confirm_password = st.text_input(
                    "Confirm new password",
                    type="password",
                )
                register_submitted = st.form_submit_button(
                    "Register",
                    type="primary",
                    icon=":material/person_add:",
                    width="stretch",
                )

        if register_submitted:
            if register_password != register_confirm_password:
                st.error("The passwords do not match.")
            else:
                registered, register_message = register_streamlit_user(
                    register_username,
                    register_password,
                    register_email,
                )

                if registered:
                    st.session_state["login_notice"] = register_message
                    st.session_state["auth_view"] = "login"
                    st.rerun()
                else:
                    st.error(register_message)

        if st.button(
            "Already have an account? Log in",
            icon=":material/login:",
            width="stretch",
        ):
            show_auth_view("login")

    else:
        st.subheader("📧 Recover account")
        recovery_step = st.session_state.get("recovery_step", 1)

        if recovery_step == 1:
            st.caption("Step 1 of 2 · Request a code that expires after ten minutes.")

            if is_sendgrid_configured():
                st.info("A six-digit code will be sent to your recovery email.")
            elif is_local_reset_fallback_enabled():
                st.warning(
                    "Email delivery is unavailable. Local reset fallback is enabled."
                )
            else:
                st.warning(
                    "Email delivery is unavailable. Contact an administrator if "
                    "you cannot receive a reset code."
                )

            with st.form("request_reset_code_form"):
                recovery_identifier = st.text_input(
                    "Username or recovery email",
                    key="recovery_identifier",
                )
                request_submitted = st.form_submit_button(
                    "Send code",
                    type="primary",
                    icon=":material/outgoing_mail:",
                    width="stretch",
                )

            if request_submitted:
                request_started, request_message, fallback_code = request_reset_code(
                    recovery_identifier
                )

                if request_started:
                    st.session_state["recovery_notice"] = request_message
                    st.session_state["recovery_fallback_code"] = fallback_code
                    st.session_state["recovery_step"] = 2
                    st.rerun()
                else:
                    st.error(request_message)

        else:
            st.caption("Step 2 of 2 · Verify the code and choose a new password.")
            recovery_notice = st.session_state.get("recovery_notice", "")
            fallback_code = st.session_state.get("recovery_fallback_code")

            if fallback_code:
                st.warning(recovery_notice)
                st.code(fallback_code, language=None)
            else:
                st.success(recovery_notice)

            reset_username = get_reset_username()

            with st.container(border=True):
                reset_code = st.text_input(
                    "Six-digit reset code",
                    max_chars=6,
                    key="recovery_reset_code",
                )
                recovery_password = st.text_input(
                    "New password",
                    type="password",
                    key="recovery_new_password",
                )
                display_password_strength(recovery_password)

                with st.form("password_reset_submit_form", border=False):
                    recovery_confirm_password = st.text_input(
                        "Confirm new password",
                        type="password",
                    )
                    reset_submitted = st.form_submit_button(
                        "Reset password",
                        type="primary",
                        icon=":material/lock_reset:",
                        width="stretch",
                    )

            if reset_submitted:
                password_reset, reset_message = reset_password(
                    reset_username,
                    reset_code,
                    recovery_password,
                    recovery_confirm_password,
                )

                if password_reset:
                    st.session_state["login_notice"] = reset_message
                    st.session_state["auth_view"] = "login"
                    st.session_state["recovery_step"] = 1
                    st.rerun()
                else:
                    st.error(reset_message)

            if st.button(
                "Request a new code",
                icon=":material/refresh:",
                width="stretch",
            ):
                clear_reset_request()
                st.session_state["recovery_step"] = 1
                st.session_state.pop("recovery_notice", None)
                st.session_state.pop("recovery_fallback_code", None)
                st.rerun()

        if st.button(
            "Back to login",
            icon=":material/arrow_back:",
            width="stretch",
        ):
            show_auth_view("login")
