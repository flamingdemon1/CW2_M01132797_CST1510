"""Protected Gatekeeper profile and password management page."""

import streamlit as st
from app_model import db, schema, ui, users
from app_model.security import display_password_strength, get_password_errors
from main import generate_hash, is_valid_hash


PROFILE_LOGO_PATH = "assets/logos/gatekeeper_logo.png"


st.set_page_config(
    page_title="Gatekeeper Profile",
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="auto",
)

ui.apply_theme()


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""


if not st.session_state["logged_in"]:
    ui.page_header(
        "Restricted Area",
        "Authentication is required to open your Gatekeeper Profile.",
        status="ACCESS DENIED",
        status_accent="red",
        logo_path=PROFILE_LOGO_PATH,
        logo_text="👤",
        logo_alt="Gatekeeper profile logo",
    )
    ui.status_card(
        "Protected route",
        "Return to Gatekeeper home and authenticate before viewing account details.",
        accent="red",
    )
    st.markdown('<div style="height: 1.25rem;"></div>', unsafe_allow_html=True)

    if st.button("Go to home page", icon=":material/home:"):
        st.switch_page("home.py")

    st.stop()


def change_password(username, current_password, new_password, confirm_password):
    """Verify the account and securely update its stored password hash."""
    if not current_password or not new_password or not confirm_password:
        return False, "Please complete all password fields."

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
                "The new password does not meet the required rules. "
                "Please check the password feedback above.",
            )

        new_password_hash = generate_hash(new_password)
        updated = users.update_password(conn, username, new_password_hash)

        if not updated:
            return False, "The password could not be updated."

        return True, "Password changed successfully. Your session remains active."

    finally:
        conn.close()


ui.sidebar_user(st.session_state["username"])

if st.sidebar.button(
    "Log out",
    icon=":material/logout:",
    use_container_width=True,
):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.switch_page("home.py")


ui.page_header(
    "Profile",
    "Account details and session security",
    status="SECURE SESSION",
    logo_path=PROFILE_LOGO_PATH,
    logo_text="👤",
    logo_alt="Gatekeeper profile logo",
)

identity_column, status_column = st.columns(2)

with identity_column:
    ui.section_card(
        "Account identity",
        f"Username: {st.session_state['username']}",
        accent="blue",
    )

with status_column:
    ui.status_card(
        "Secure session active",
        "Your authenticated Gatekeeper session remains protected.",
        accent="green",
    )


ui.section_heading(
    "Quick access",
    "Move between protected Gatekeeper workspaces or end this session.",
)

dashboard_column, assistant_column, logout_column = st.columns(3)

with dashboard_column:
    if st.button(
        "Open dashboard",
        icon=":material/dashboard:",
        use_container_width=True,
    ):
        st.switch_page("pages/1_dashboard.py")

with assistant_column:
    if st.button(
        "Open SmartBoyAI",
        icon=":material/smart_toy:",
        use_container_width=True,
    ):
        st.switch_page("pages/2_SmartBoyAI.py")

with logout_column:
    if st.button(
        "Log out",
        icon=":material/logout:",
        use_container_width=True,
    ):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.switch_page("home.py")


ui.section_heading(
    "Change password",
    "Confirm your current password before setting a new one.",
)

ui.section_card(
    "Password security",
    "The new password uses the same validation rules and bcrypt hashing as registration.",
    accent="amber",
)

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

    # Enter submits only after the user reaches the confirmation field.
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
            use_container_width=True,
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
