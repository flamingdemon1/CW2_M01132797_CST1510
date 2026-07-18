"""Gatekeeper Streamlit entry page and account access flow."""

import sqlite3
import time
import streamlit as st
from app_model import db, schema, twilio_service, ui, users
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
    get_password_errors,
    is_valid_email,
    live_password_input,
)
from main import generate_hash, get_username_errors, is_valid_hash


TWO_FACTOR_RESEND_SECONDS = 30
PENDING_2FA_KEYS = [
    "pending_2fa_username",
    "pending_2fa_role",
    "pending_2fa_phone",
    "pending_2fa_started",
    "pending_2fa_last_sent",
]


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
    "role": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

ui.apply_theme()
ui.sidebar_logo()
ui.sidebar_theme_control("home")


def show_auth_view(view_name):
    """Switch the account panel """
    current_view = st.session_state.get("auth_view", "login")

    if current_view == "two_factor" and view_name != "two_factor":
        clear_pending_two_factor()

    if current_view == "recovery" and view_name != "recovery":
        clear_reset_request()

    if view_name == "recovery" and current_view != "recovery":
        clear_reset_request()
        st.session_state["recovery_step"] = 1
        st.session_state.pop("recovery_notice", None)
        st.session_state.pop("recovery_fallback_code", None)

    st.session_state["auth_view"] = view_name
    st.rerun()


def clear_pending_two_factor():
    """Clear temporary SMS verification state from the current browser session."""
    for key in PENDING_2FA_KEYS:
        st.session_state.pop(key, None)


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


def complete_streamlit_login(username, role):
    """Mark a Streamlit user as fully authenticated."""
    clear_pending_two_factor()
    st.session_state["logged_in"] = True
    st.session_state["username"] = username
    st.session_state["role"] = role or "user"


def start_two_factor_login(username, role, phone_number):
    """Send the SMS code and store only minimal pending-login state."""
    code_sent, code_message = twilio_service.send_two_factor_code(phone_number)

    if not code_sent:
        clear_pending_two_factor()
        return False, code_message

    now = time.time()
    st.session_state["pending_2fa_username"] = username
    st.session_state["pending_2fa_role"] = role or "user"
    st.session_state["pending_2fa_phone"] = phone_number
    st.session_state["pending_2fa_started"] = now
    st.session_state["pending_2fa_last_sent"] = now
    st.session_state["auth_view"] = "two_factor"
    return True, code_message


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
        return False, "Please enter both a username and a password.", "error"

    try:
        conn = db.get_connection()
        schema.create_user_table(conn)

        try:
            user = users.get_user(conn, username)
        finally:
            conn.close()
    except Exception:
        return False, "Login is temporarily unavailable. Please try again.", "error"

    if user is None or not is_valid_hash(password, user["password_hash"]):
        return False, "Incorrect username or password.", "error"

    account_role = str(user["role"] or "user").strip().lower()
    two_factor_enabled = bool(user["two_factor_enabled"])
    phone_number = str(user["phone_number"] or "").strip()

    if not two_factor_enabled:
        complete_streamlit_login(username, account_role)
        return True, "Login successful.", "complete"

    if not phone_number:
        return (
            False,
            "This account has SMS 2FA enabled but no usable phone number. "
            "Contact an administrator.",
            "error",
        )

    two_factor_started, two_factor_message = start_two_factor_login(
        username,
        account_role,
        phone_number,
    )

    if not two_factor_started:
        return False, two_factor_message, "error"

    return True, two_factor_message, "two_factor"


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

        with st.form("login_form", enter_to_submit=True):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button(
                "Log in",
                type="primary",
                icon=":material/login:",
                width="stretch",
            )

        if login_submitted:
            login_successful, login_message, login_step = login_streamlit_user(
                login_username,
                login_password,
            )

            if login_successful and login_step == "complete":
                st.switch_page("pages/1_dashboard.py")
            elif login_successful and login_step == "two_factor":
                st.success(login_message)
                st.rerun()
            else:
                st.error(login_message)

        create_column, forgot_column = st.columns(2, gap="small")

        with create_column:
            if st.button(
                "Create account",
                icon=":material/person_add:",
                width="stretch",
                key="login_create_account",
            ):
                show_auth_view("register")

        with forgot_column:
            if st.button(
                "Forgot password?",
                icon=":material/lock_reset:",
                width="stretch",
                key="login_forgot_password",
            ):
                show_auth_view("recovery")

    elif auth_view == "register":
        st.subheader("👤 Create secure account")
        st.caption("Password feedback updates when the password field changes.")

        with st.form(
            "registration_submit_form",
            enter_to_submit=False,
            border=True,
        ):
            register_username = st.text_input(
                "New username",
                key="register_username",
            )
            register_email = st.text_input(
                "Recovery email",
                key="register_email",
            )
            register_password = live_password_input(
                "New password",
                key="register_password",
                theme=ui.get_theme(),
            )
            register_confirm_password = confirm_password_input(
                "Confirm new password",
                key="register_confirm_password",
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

    elif auth_view == "two_factor":
        st.subheader("SMS two-factor verification")
        pending_username = st.session_state.get("pending_2fa_username")
        pending_phone = st.session_state.get("pending_2fa_phone")
        pending_role = st.session_state.get("pending_2fa_role", "user")

        if not pending_username or not pending_phone:
            st.warning("No pending SMS verification is available. Please log in again.")
            clear_pending_two_factor()

            if st.button("Back to login", icon=":material/login:", width="stretch"):
                show_auth_view("login")

            st.stop()

        st.caption(
            "Password verified. Enter the SMS code sent to "
            f"{twilio_service.mask_phone_number(pending_phone)} to finish login."
        )

        with st.form("two_factor_code_form", enter_to_submit=True):
            two_factor_code = st.text_input(
                "SMS verification code",
                autocomplete="one-time-code",
            )
            verify_submitted = st.form_submit_button(
                "Verify code",
                type="primary",
                icon=":material/verified_user:",
                width="stretch",
            )

        if verify_submitted:
            code_approved, code_message = twilio_service.check_two_factor_code(
                pending_phone,
                two_factor_code,
            )

            if code_approved:
                complete_streamlit_login(pending_username, pending_role)
                st.switch_page("pages/1_dashboard.py")
            else:
                st.error(code_message)

        resend_column, cancel_column = st.columns(2, gap="small")

        with resend_column:
            if st.button(
                "Resend code",
                icon=":material/sms:",
                width="stretch",
                key="two_factor_resend",
            ):
                last_sent = float(st.session_state.get("pending_2fa_last_sent", 0))
                seconds_since_send = time.time() - last_sent

                if seconds_since_send < TWO_FACTOR_RESEND_SECONDS:
                    seconds_left = int(TWO_FACTOR_RESEND_SECONDS - seconds_since_send)
                    st.warning(f"Please wait {seconds_left} seconds before resending.")
                else:
                    resent, resend_message = twilio_service.send_two_factor_code(
                        pending_phone
                    )

                    if resent:
                        st.session_state["pending_2fa_last_sent"] = time.time()
                        st.success(resend_message)
                    else:
                        st.error(resend_message)

        with cancel_column:
            if st.button(
                "Cancel login",
                icon=":material/cancel:",
                width="stretch",
                key="two_factor_cancel",
            ):
                clear_pending_two_factor()
                st.session_state["auth_view"] = "login"
                st.rerun()

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

            with st.form("request_reset_code_form", enter_to_submit=False):
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

            with st.form(
                "password_reset_submit_form",
                enter_to_submit=False,
                border=True,
            ):
                reset_code = st.text_input(
                    "Six-digit reset code",
                    max_chars=6,
                    key="recovery_reset_code",
                )
                recovery_password = live_password_input(
                    "New password",
                    key="recovery_new_password",
                    theme=ui.get_theme(),
                )
                recovery_confirm_password = confirm_password_input(
                    "Confirm new password",
                    key="recovery_confirm_password",
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
