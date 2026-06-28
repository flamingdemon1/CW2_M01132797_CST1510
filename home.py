import sqlite3
import streamlit as st
from app_model import db, schema, ui, users
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


def get_password_errors(password):
    """Return a list of password strength problems."""
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")

    if not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")

    if not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one number.")

    if not any(not char.isalnum() for char in password):
        errors.append("Password must contain at least one symbol.")

    return errors


def get_password_strength(password):
    """Return a display label, score, colour, and feedback for a password."""
    score = 0
    missing_requirements = []

    if len(password) >= 8:
        score += 20
    else:
        missing_requirements.append("at least 8 characters")

    if any(char.isupper() for char in password):
        score += 15
    else:
        missing_requirements.append("uppercase letter")

    if any(char.islower() for char in password):
        score += 15

    if any(char.isdigit() for char in password):
        score += 15
    else:
        missing_requirements.append("number")

    if any(not char.isalnum() for char in password):
        score += 20
    else:
        missing_requirements.append("symbol")

    if len(password) >= 12:
        score += 15

    if score <= 20:
        label, colour = "Very weak", "#8B0000"
    elif score <= 40:
        label, colour = "Weak", "#E57373"
    elif score <= 60:
        label, colour = "Medium", "#F9A825"
    elif score <= 80:
        label, colour = "Strong", "#81C784"
    else:
        label, colour = "Very strong", "#1B5E20"

    if missing_requirements:
        feedback = "Missing: " + ", ".join(missing_requirements) + "."
    elif len(password) < 12:
        feedback = (
            "Good password. Use 12 or more characters for an even stronger "
            "password."
        )
    elif not any(char.islower() for char in password):
        feedback = "Good password. Add a lowercase letter for extra strength."
    else:
        feedback = "Excellent password. All recommended checks are passed."

    return label, score, colour, feedback


def display_password_strength(password):
    """Display a coloured strength bar without changing password validation."""
    if password == "":
        st.caption("Start typing a password to see its strength.")
        return

    label, score, colour, feedback = get_password_strength(password)

    st.markdown(
        f"""
        <div style="max-width: 520px; margin-top: 0.25rem;
                    margin-bottom: 0.25rem;">
            <div style="display: flex; align-items: baseline; gap: 0.6rem;">
                <strong>Password strength: {label}</strong>
                <span style="color: {colour}; font-size: 0.9rem;">{score}%</span>
            </div>
            <div style="background-color: #1E293B; height: 10px;
                        border-radius: 5px; overflow: hidden; margin-top: 6px;">
                <div style="background-color: {colour}; width: {score}%;
                            height: 10px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.caption(feedback)


def register_streamlit_user(username, password):
    """Register a new user in the SQLite users table."""
    username = username.strip()

    if username == "" or password == "":
        st.error("Please enter both a username and a password.")
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
        users.add_user(conn, username, password_hash)
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

    col1, col2, col3 = st.columns(3)

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

            if login_submitted:
                login_streamlit_user(login_username, login_password)

        with register_tab:
            st.markdown("#### Create secure account")
            st.caption("Passwords are validated before being stored as hashes.")

            # Regular widgets allow the strength display to update as the value changes.
            with st.container(border=True):
                register_username = st.text_input("New username")
                register_password = st.text_input(
                    "New password",
                    type="password"
                )
                display_password_strength(register_password)

                register_submitted = st.button(
                    "Register",
                    type="primary",
                    icon=":material/person_add:",
                    use_container_width=True,
                )

            if register_submitted:
                register_streamlit_user(register_username, register_password)
