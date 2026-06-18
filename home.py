import sqlite3

import streamlit as st

from app_model import db, schema, users
from main import generate_hash, is_strong_password, is_valid_hash


st.set_page_config(
    page_title="Gatekeeper Home",
    page_icon="H",
    layout="wide"
)


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""


def register_streamlit_user(username, password):
    """Register a new user in the SQLite users table."""
    username = username.strip()

    if username == "" or password == "":
        st.error("Please enter both a username and a password.")
        return

    if not is_strong_password(password):
        st.error(
            "Password must be at least 8 characters and include an uppercase "
            "letter, a number, and a symbol."
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
            st.success(f"Login successful. Welcome, {username}.")
        else:
            st.error("Incorrect username or password.")

    finally:
        conn.close()


def logout_streamlit_user():
    """Clear the Streamlit login session."""
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.info("You have been logged out.")


st.title("Gatekeeper System")
st.write(
    "Welcome to the Streamlit version of the CST1510 coursework project. "
    "This page is the main entry point for the web app."
)

if st.session_state["logged_in"]:
    st.success(f"Logged in as: {st.session_state['username']}")
else:
    st.warning("You are not logged in. Please log in before opening the dashboard.")

st.subheader("Login and Register")
st.write(
    "Use the login tab if you already have an account. Use the register tab "
    "to create a new account. Passwords are hashed before they are stored in SQLite."
)

login_tab, register_tab = st.tabs(["Login", "Register"])

with login_tab:
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    if st.button("Log in"):
        login_streamlit_user(login_username, login_password)

with register_tab:
    register_username = st.text_input("New username", key="register_username")
    register_password = st.text_input(
        "New password",
        type="password",
        key="register_password"
    )

    st.caption(
        "Password rule: at least 8 characters, one uppercase letter, "
        "one number, and one symbol."
    )

    if st.button("Register"):
        register_streamlit_user(register_username, register_password)

st.divider()

st.subheader("Dashboard Access")
st.write(
    "The cyber incident dashboard is stored as a separate Streamlit page inside "
    "the pages folder. It can only be viewed after a successful login."
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Open dashboard"):
        if st.session_state["logged_in"]:
            st.switch_page("pages/1_dashboard.py")
        else:
            st.error("Please log in before opening the dashboard.")

with col2:
    if st.button("Log out"):
        logout_streamlit_user()
