import sqlite3
import streamlit as st
from app_model import db, schema, ui, users
from app_model.security import (
    display_password_strength,
    get_password_errors,
    get_password_strength,
    is_valid_email,
)
from main import generate_hash, is_valid_hash


st.set_page_config(
    page_title="Gatekeeper Home",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
ui.apply_theme()


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""


def register_streamlit_user(username, password, email=""):
    """Register a new user in the SQLite users table."""
    username = username.strip()
    email = email.strip().lower()

    if username == "" or email == "" or password == "":
        st.error("Please enter a username, recovery email, and password.")
        return

    if not is_valid_email(email):
        st.error("Please enter a valid recovery email address.")
        return

    password_errors = get_password_errors(password)

    if password_errors:
        st.error(
            "Password does not meet the required rules. Please check the "
            "password feedback above."
        )
        return

    conn = db.get_connection()
    schema.create_user_table(conn)

    try:
        existing_user = users.get_user(conn, username)

        if existing_user is not None:
            st.error("This username already exists. Please choose another one.")
            return

        password_hash = generate_hash(password)
        users.add_user(conn, username, password_hash, email)
        st.success("Registration successful. You can now log in.")

    except sqlite3.IntegrityError:
        st.error("This username already exists. Please choose another one.")

    finally:
        conn.close()


def login_streamlit_user(username, password):
    """Log in a user by checking the SQLite password hash."""
    username = username.strip()

    if username == "" or password == "":
        st.error("Please enter both a username and a password.")
        return

    conn = db.get_connection()
    schema.create_user_table(conn)

    try:
        user = users.get_user(conn, username)

        if user is None:
            st.error("Incorrect username or password.")
            return

        stored_hash = user["password_hash"]

        if is_valid_hash(password, stored_hash):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.switch_page("pages/1_dashboard.py")
            return

        st.error("Incorrect username or password.")

    finally:
        conn.close()


def logout_streamlit_user():
    """Clear the Streamlit login session."""
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""


header_status = "SECURE SESSION" if st.session_state["logged_in"] else "ACCESS CONTROL READY"

ui.page_header(
    "Gatekeeper",
    "Cyber Incident Intelligence System",
    status=header_status,
    logo_path="assets/logos/gatekeeper_logo.png",
    logo_text="🛡️",
    logo_alt="Gatekeeper logo",
)

if st.session_state["logged_in"]:
    ui.status_card(
        "Identity verified",
        f"Secure session active for {st.session_state['username']}.",
        accent="green",
    )

    ui.section_heading(
        "Command routes",
        "Choose a protected Gatekeeper workspace.",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ui.section_card(
            "Security Dashboard",
            "Review incident totals, categories, statuses, and severity filters.",
            accent="cyan",
        )
        if st.button(
            "Open dashboard",
            icon=":material/dashboard:",
            use_container_width=True,
        ):
            st.switch_page("pages/1_dashboard.py")

    with col2:
        ui.section_card(
            "SmartBoyAI Assistant",
            "Ask database-aware questions about cyber incidents and IT tickets.",
            accent="green",
        )
        if st.button(
            "Open SmartBoyAI",
            icon=":material/smart_toy:",
            use_container_width=True,
        ):
            st.switch_page("pages/2_SmartBoyAI.py")

    with col3:
        ui.section_card(
            "Profile & Security",
            "Review account details and securely update your password.",
            accent="blue",
        )
        if st.button(
            "Open profile",
            icon=":material/account_circle:",
            use_container_width=True,
        ):
            st.switch_page("pages/3_Profile.py")

    with col4:
        ui.section_card(
            "Session Control",
            "End the current authenticated session and return to secure access.",
            accent="red",
        )
        if st.button(
            "Log out",
            icon=":material/logout:",
            use_container_width=True,
        ):
            logout_streamlit_user()
            st.rerun()

else:
    overview_column, access_column = st.columns([0.8, 1.2], gap="large")

    with overview_column:
        ui.section_card(
            "Protected intelligence workspace",
            "Gatekeeper brings incident monitoring, operational data, and "
            "assisted analysis into one authenticated command centre.",
            accent="cyan",
        )
        st.write("")
        ui.status_card(
            "Credential boundary active",
            "Account passwords remain protected by the existing hashing and "
            "validation controls.",
            accent="green",
        )

    with access_column:
        login_tab, register_tab = st.tabs(["Operator login", "Register account"])

        with login_tab:
            st.markdown("#### Secure access")
            st.caption("Authenticate to enter the Gatekeeper command centre.")

            with st.form("login_form"):
                login_username = st.text_input("Username")
                login_password = st.text_input(
                    "Password",
                    type="password"
                )
                login_submitted = st.form_submit_button(
                    "Log in",
                    icon=":material/login:",
                    use_container_width=True,
                )

            if st.button(
                "Forgot password?",
                icon=":material/lock_reset:",
                use_container_width=True,
            ):
                st.switch_page("pages/4_Forgot_Password.py")

            if login_submitted:
                login_streamlit_user(login_username, login_password)

        with register_tab:
            st.markdown("#### Create secure account")
            st.caption("Passwords are validated before being stored as hashes.")

            # Regular widgets allow the strength display to update as the value changes.
            with st.container(border=True):
                register_username = st.text_input("New username")
                register_email = st.text_input("Recovery email")
                register_password = st.text_input(
                    "New password",
                    type="password"
                )
                display_password_strength(register_password)

                # The final field is in a form so Enter submits registration.
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
                        use_container_width=True,
                    )

            if register_submitted:
                if register_password != register_confirm_password:
                    st.error("The passwords do not match.")
                else:
                    register_streamlit_user(
                        register_username,
                        register_password,
                        register_email,
                    )
