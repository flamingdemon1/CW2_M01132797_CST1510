"""Read-only administrator monitoring page for Gatekeeper."""

import sqlite3

import pandas as pd
import streamlit as st

from app_model import db, schema, ui, users
from app_model.security import is_valid_email


MONITORED_TABLES = {
    "users": "User accounts",
    "saved_results": "Saved results",
    "cyber_incidents": "Cyber incidents",
    "it_tickets": "IT tickets",
    "datasets_metadata": "Dataset metadata",
}


st.set_page_config(
    page_title="Gatekeeper Admin",
    page_icon=":material/admin_panel_settings:",
    layout="wide",
    initial_sidebar_state="auto",
)

for key, default_value in {"logged_in": False, "username": ""}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

ui.apply_theme()
ui.sidebar_logo()
ui.sidebar_theme_control("admin")


def get_logged_in_role(username):
    """Read the current account role directly from SQLite."""
    connection = db.get_connection()

    try:
        schema.create_user_table(connection)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username = ?;",
            (username,),
        )
        row = cursor.fetchone()
        return str(row["role"] or "user").strip().lower() if row else None
    finally:
        connection.close()


def table_exists(connection, table_name):
    """Return True when one expected SQLite table is available."""
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table' AND name = ?;
        """,
        (table_name,),
    )
    return cursor.fetchone() is not None


def get_table_count(connection, table_name):
    """Count rows in a predefined monitored table."""
    if table_name not in MONITORED_TABLES or not table_exists(connection, table_name):
        return None

    cursor = connection.cursor()
    # The name comes only from MONITORED_TABLES, never from user input.
    cursor.execute(f'SELECT COUNT(*) AS total FROM "{table_name}";')
    return cursor.fetchone()["total"]


def load_admin_monitoring_data():
    """Load safe summaries without selecting passwords or result content."""
    connection = db.get_connection()

    try:
        schema.create_user_table(connection)
        schema.create_saved_results_table(connection)
        safe_user_rows = users.get_all_users_safe(connection)
        users_table = pd.DataFrame([dict(row) for row in safe_user_rows])

        if not users_table.empty:
            users_table = users_table.rename(
                columns={
                    "username": "Username",
                    "role": "Role",
                    "recovery_email_status": "Recovery email",
                    "created_at": "Created at",
                }
            )

        saved_results_table = pd.read_sql_query(
            """
            SELECT
                username AS Username,
                result_type AS 'Result type',
                title AS Title,
                created_at AS 'Created at',
                save_source AS Source
            FROM saved_results
            ORDER BY id DESC
            LIMIT 20;
            """,
            connection,
        )

        row_counts = {
            table_name: get_table_count(connection, table_name)
            for table_name in MONITORED_TABLES
        }
    finally:
        connection.close()

    database_table = pd.DataFrame(
        [
            {
                "Table": display_name,
                "SQLite name": table_name,
                "Status": "Available" if row_counts[table_name] is not None else "Not migrated",
                "Rows": row_counts[table_name] if row_counts[table_name] is not None else "N/A",
            }
            for table_name, display_name in MONITORED_TABLES.items()
        ]
    )
    return users_table, saved_results_table, database_table, row_counts


def save_user_role(username, role):
    """Save one validated role through the shared user model."""
    connection = db.get_connection()

    try:
        schema.create_user_table(connection)
        return users.update_user_role(connection, username, role)
    finally:
        connection.close()


def save_user_recovery_email(username, email):
    """Validate and save a recovery email through the shared user model."""
    normalised_email = email.strip().lower()

    if not normalised_email:
        raise ValueError("Recovery email cannot be empty.")

    if not is_valid_email(normalised_email):
        raise ValueError("Enter a valid recovery email address.")

    connection = db.get_connection()

    try:
        schema.create_user_table(connection)
        return users.update_recovery_email(
            connection,
            username,
            normalised_email,
        )
    finally:
        connection.close()


if not st.session_state["logged_in"]:
    ui.page_header(
        "Restricted Area",
        "Authentication is required to open the Gatekeeper Admin page.",
        status="ACCESS DENIED",
        status_accent="red",
    )
    st.warning("Return to Gatekeeper home and authenticate before opening Admin monitoring.")
    ui.route_spacing()

    if st.button("Go to home page", icon=":material/home:"):
        st.switch_page("home.py")

    st.stop()

active_username = str(st.session_state.get("username", "")).strip()

if not active_username:
    st.error("Your session is missing a username. Please log in again.")
    ui.logout()
    st.stop()

try:
    active_role = get_logged_in_role(active_username)
except (sqlite3.Error, OSError):
    st.error("Your administrator role could not be verified from SQLite.")
    st.stop()

if active_role != "admin":
    ui.page_header(
        "Access Denied",
        "Administrator privileges are required to view system monitoring data.",
        status="ADMIN ONLY",
        status_accent="red",
    )
    st.error("Your account does not have permission to access this page.")
    ui.route_spacing()

    if st.button("Open dashboard", icon=":material/dashboard:"):
        st.switch_page("pages/1_dashboard.py")

    st.stop()

ui.content_profile_control()
ui.sidebar_user(active_username)

if st.sidebar.button("Log out", icon=":material/logout:", width="stretch"):
    ui.logout()
    st.switch_page("home.py")

ui.page_header(
    "Admin Monitoring",
    "System oversight and controlled account administration",
    status="ADMIN VERIFIED",
    status_accent="green",
)

try:
    user_data, result_data, database_data, counts = load_admin_monitoring_data()
except (sqlite3.Error, OSError) as error:
    st.error("Administrator monitoring data could not be loaded from SQLite.")
    st.caption(f"Technical detail: {type(error).__name__}")
    st.stop()

admin_notice = st.session_state.pop("admin_account_notice", None)

if admin_notice:
    notice_type, notice_message = admin_notice

    if notice_type == "success":
        st.success(notice_message)
    else:
        st.error(notice_message)

ui.section_heading(
    "System overview",
    "Current row totals from the shared Gatekeeper SQLite database.",
)
overview_columns = st.columns(5)
overview_metrics = [
    ("Total users", counts["users"], "Registered accounts", "blue"),
    ("Saved results", counts["saved_results"], "Stored summaries", "cyan"),
    ("Cyber incidents", counts["cyber_incidents"], "Migrated incident rows", "red"),
    ("IT tickets", counts["it_tickets"], "Migrated support rows", "amber"),
    ("Metadata rows", counts["datasets_metadata"], "Dataset catalogue rows", "green"),
]

for column, (label, value, note, accent) in zip(overview_columns, overview_metrics):
    with column:
        ui.metric_card(
            label,
            value if value is not None else "N/A",
            note=note,
            accent=accent,
        )

ui.section_heading(
    "User overview",
    "Account roles and recovery readiness without passwords or email addresses.",
)

if user_data.empty:
    st.info("No user accounts are available.")
else:
    ui.themed_dataframe(user_data, height=380)

st.caption(
    "Admins can update roles and recovery emails, but password hashes, reset "
    "codes, and secrets are never displayed."
)

if not user_data.empty:
    ui.section_heading(
        "Edit user account",
        "Select one account, then update its role or recovery email.",
    )
    user_options = user_data["Username"].tolist()
    user_search = st.text_input(
        "Search users",
        placeholder="Type part of a username",
        autocomplete="off",
        key="admin_user_search",
    ).strip().lower()
    filtered_user_options = [
        username
        for username in user_options
        if user_search in username.lower()
    ]
    selected_username = st.selectbox(
        "Select user",
        filtered_user_options,
        placeholder="No matching users",
        key="admin_selected_user",
    )
    st.caption("Select a user or press Esc to close the dropdown before scrolling.")
    selection_available = selected_username is not None

    if not selection_available:
        st.info("No users match the current search. Change the search text to continue.")

    selected_row = (
        user_data[user_data["Username"] == selected_username].iloc[0]
        if selection_available
        else None
    )
    current_role = (
        str(selected_row["Role"]).strip().lower()
        if selected_row is not None
        else "user"
    )
    role_column, email_column = st.columns(2, gap="large")

    with role_column:
        with st.form(
            f"admin_role_form_{selected_username or 'no_selection'}",
            enter_to_submit=False,
            border=True,
        ):
            selected_role = st.segmented_control(
                "Account role",
                ["user", "admin"],
                default=current_role if current_role in {"user", "admin"} else "user",
                selection_mode="single",
                disabled=not selection_available,
            )
            role_submitted = st.form_submit_button(
                "Save role",
                icon=":material/admin_panel_settings:",
                type="primary",
                width="stretch",
                disabled=not selection_available,
            )

    with email_column:
        with st.form(
            f"admin_email_form_{selected_username or 'no_selection'}",
            clear_on_submit=True,
            enter_to_submit=False,
            border=True,
        ):
            recovery_email = st.text_input(
                "New recovery email",
                placeholder="name@example.com",
                autocomplete="off",
                disabled=not selection_available,
            )
            email_submitted = st.form_submit_button(
                "Save recovery email",
                icon=":material/alternate_email:",
                type="primary",
                width="stretch",
                disabled=not selection_available,
            )

    if role_submitted:
        try:
            if selected_role is None:
                raise ValueError("Select either the user or admin role.")

            if selected_role == current_role:
                raise ValueError("This account already has the selected role.")

            if not save_user_role(selected_username, selected_role):
                raise ValueError("The selected account could not be updated.")

            st.session_state["admin_account_notice"] = (
                "success",
                f"Role updated for {selected_username}.",
            )
            st.rerun()
        except (ValueError, sqlite3.Error, OSError) as error:
            st.error(str(error))

    if email_submitted:
        try:
            if not save_user_recovery_email(selected_username, recovery_email):
                raise ValueError("The selected account could not be updated.")

            st.session_state["admin_account_notice"] = (
                "success",
                f"Recovery email updated for {selected_username}.",
            )
            st.rerun()
        except (ValueError, sqlite3.Error, OSError) as error:
            st.error(str(error))

ui.section_heading(
    "Recent saved results",
    "The latest 20 saved-result records without their full content.",
)

if result_data.empty:
    st.info("No saved results are available.")
else:
    ui.themed_dataframe(result_data, height=380)

ui.section_heading(
    "Dataset and database overview",
    "Expected Gatekeeper tables, migration availability, and row counts.",
)
ui.themed_dataframe(database_data, height=340)

st.caption(
    "Monitoring tables are read-only. Password hashes, recovery codes, API keys, "
    "secrets, full recovery email addresses, and saved-result content are never "
    "displayed."
)
