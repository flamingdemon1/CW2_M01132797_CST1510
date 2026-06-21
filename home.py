import sqlite3

import streamlit as st

from app_model import db, schema, users
from main import generate_hash, is_valid_hash


st.set_page_config(
    page_title="Gatekeeper Home",
    page_icon="H",
    layout="wide"
)


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


def register_streamlit_user(username, password):
    """Register a new user in the SQLite users table."""
    username = username.strip()

    if username == "" or password == "":
        st.error("Please enter both a username and a password.")
        return

    password_errors = get_password_errors(password)

    if password_errors:
        st.error("Weak password. Please fix the following:")

        for error in password_errors:
            st.write(f"- {error}")

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


st.title("Gatekeeper System")
st.write(
    "Welcome to the Streamlit version of the CST1510 coursework project. "
    "Log in or register below to access the cyber incident dashboard."
)

if st.session_state["logged_in"]:
    st.success(f"Welcome, {st.session_state['username']}. You are logged in.")

    st.write(
        "You can now open the protected dashboard, or log out when you have "
        "finished using the system."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Open dashboard"):
            st.switch_page("pages/1_dashboard.py")

    with col2:
        if st.button("Open SmartBoyAI"):
            st.switch_page("pages/2_SmartBoyAI.py")

    with col3:
        if st.button("Log out"):
            logout_streamlit_user()
            st.rerun()

else:
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.subheader("Login")
        st.write("Enter your username and password to access the dashboard.")

        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input(
                "Password",
                type="password"
            )
            login_submitted = st.form_submit_button("Log in")

        if login_submitted:
            login_streamlit_user(login_username, login_password)

    with register_tab:
        st.subheader("Register")
        st.write("Create a new account. Your password will be stored as a hash.")

        with st.form("register_form"):
            register_username = st.text_input("New username")
            register_password = st.text_input(
                "New password",
                type="password"
            )

            st.caption(
                "Password rule: at least 8 characters, one uppercase letter, "
                "one number, and one symbol."
            )

            register_submitted = st.form_submit_button("Register")

        if register_submitted:
            register_streamlit_user(register_username, register_password)
