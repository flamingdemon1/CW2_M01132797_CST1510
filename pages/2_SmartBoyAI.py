import os

import pandas as pd
import streamlit as st
from app_model import db, ui
from app_model.logic import cyber_incidents, it_tickets, metadatas


st.set_page_config(
    page_title="SmartBoyAI",
    page_icon="🤖",
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
        "Authentication is required to open SmartBoyAI Assistant.",
        status="ACCESS DENIED",
        status_accent="red",
        logo_path="assets/logos/smartboyai_logo.png",
        logo_text="AI",
        logo_alt="SmartBoyAI logo",
    )
    ui.status_card(
        "Protected route",
        "Return to Gatekeeper home and authenticate before opening the AI workspace.",
        accent="red",
    )

    if st.button("Go to home page", icon=":material/home:"):
        st.switch_page("home.py")

    st.stop()


ui.sidebar_user(st.session_state["username"])

if st.sidebar.button(
    "Log out",
    icon=":material/logout:",
    use_container_width=True,
):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.switch_page("home.py")


def get_groq_api_key():
    """Return the Groq API key from Streamlit secrets or an environment variable."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY", "")


def load_table(conn, table_name, load_function):
    """Load one migrated table and report whether it was available."""
    try:
        return load_function(conn), None
    except Exception:
        return pd.DataFrame(), table_name


def format_counts(data, column_name):
    """Turn a pandas value_counts result into simple text."""
    if column_name not in data.columns:
        return "Column not found."

    counts = data[column_name].value_counts()

    if counts.empty:
        return "No records found."

    count_lines = []

    for name, count in counts.items():
        count_lines.append(f"- {name}: {count}")

    return "\n".join(count_lines)


def get_average_resolution_time(ticket_data):
    """Return the average IT ticket resolution time if the column is available."""
    if "resolution_time_hours" not in ticket_data.columns:
        return "Not available."

    resolution_times = pd.to_numeric(
        ticket_data["resolution_time_hours"],
        errors="coerce"
    ).dropna()

    if resolution_times.empty:
        return "Not available."

    return f"{resolution_times.mean():.1f} hours"


def load_project_data():
    """Load the dashboard tables from SQLite."""
    conn = db.get_connection()
    missing_tables = []

    try:
        cyber_data, missing_cyber = load_table(
            conn,
            "cyber_incidents",
            cyber_incidents.get_all_cyber_incidents
        )
        ticket_data, missing_tickets = load_table(
            conn,
            "it_tickets",
            it_tickets.get_all_it_tickets
        )
        metadata_data, missing_metadata = load_table(
            conn,
            "datasets_metadata",
            metadatas.get_all_datasets_metadata
        )
    finally:
        conn.close()

    for table_name in [missing_cyber, missing_tickets, missing_metadata]:
        if table_name is not None:
            missing_tables.append(table_name)

    return cyber_data, ticket_data, metadata_data, missing_tables


def format_rows(data, columns, max_rows=80):
    """Format a filtered set of dashboard rows for the AI prompt."""
    available_columns = []

    for column in columns:
        if column in data.columns:
            available_columns.append(column)

    if not available_columns:
        return "No matching columns found."

    shown_data = data[available_columns].head(max_rows)
    result = shown_data.to_string(index=False)

    if len(data) > max_rows:
        result += f"\nOnly the first {max_rows} matching rows are shown."

    return result


def add_matching_rows(summary_parts, data, column_name, question, title, columns):
    """Add filtered dashboard rows when the user's question mentions a value."""
    if data.empty or column_name not in data.columns:
        return

    question_lower = question.lower()
    values = data[column_name].dropna().unique()

    for value in values:
        value_text = str(value)

        if value_text.lower() in question_lower:
            matching_rows = data[data[column_name].astype(str).str.lower() == value_text.lower()]
            summary_parts.extend([
                "",
                f"{title} where {column_name} is {value_text}:",
                f"Matching records: {len(matching_rows)}",
                format_rows(matching_rows, columns)
            ])


def create_database_context(question):
    """Create hidden, question-focused database context for SmartBoyAI."""
    cyber_data, ticket_data, metadata_data, missing_tables = load_project_data()

    summary_parts = [
        "Hidden project database context for SmartBoyAI:",
        "",
        "Use this context only to answer the user's current question.",
        "This context is loaded from migrated dashboard tables in SQLite.",
        "It never includes user accounts, login details, API keys, or password hashes.",
        "Do not say that the user can see this context on the page."
    ]

    if not cyber_data.empty:
        summary_parts.extend([
            "",
            "Cyber incident summary:",
            f"- Total incidents: {len(cyber_data)}",
            "- Severity counts:",
            format_counts(cyber_data, "severity"),
            "- Category/type counts:",
            format_counts(cyber_data, "category"),
            "- Status counts:",
            format_counts(cyber_data, "status")
        ])

        add_matching_rows(
            summary_parts,
            cyber_data,
            "severity",
            question,
            "Cyber incidents",
            ["incident_id", "timestamp", "severity", "category", "status", "description"]
        )
        add_matching_rows(
            summary_parts,
            cyber_data,
            "category",
            question,
            "Cyber incidents",
            ["incident_id", "timestamp", "severity", "category", "status", "description"]
        )
        add_matching_rows(
            summary_parts,
            cyber_data,
            "status",
            question,
            "Cyber incidents",
            ["incident_id", "timestamp", "severity", "category", "status", "description"]
        )

    if not ticket_data.empty:
        summary_parts.extend([
            "",
            "IT ticket summary:",
            f"- Total tickets: {len(ticket_data)}",
            "- Priority counts:",
            format_counts(ticket_data, "priority"),
            "- Status counts:",
            format_counts(ticket_data, "status"),
            f"- Average resolution time: {get_average_resolution_time(ticket_data)}"
        ])

        add_matching_rows(
            summary_parts,
            ticket_data,
            "priority",
            question,
            "IT tickets",
            [
                "ticket_id",
                "priority",
                "status",
                "assigned_to",
                "created_at",
                "resolution_time_hours",
                "description"
            ]
        )
        add_matching_rows(
            summary_parts,
            ticket_data,
            "status",
            question,
            "IT tickets",
            [
                "ticket_id",
                "priority",
                "status",
                "assigned_to",
                "created_at",
                "resolution_time_hours",
                "description"
            ]
        )

    if not metadata_data.empty:
        total_rows = "Not available."
        average_columns = "Not available."
        dataset_names = "Not available."

        if "rows" in metadata_data.columns:
            rows = pd.to_numeric(metadata_data["rows"], errors="coerce").dropna()
            if not rows.empty:
                total_rows = f"{int(rows.sum())}"

        if "columns" in metadata_data.columns:
            columns = pd.to_numeric(
                metadata_data["columns"],
                errors="coerce"
            ).dropna()
            if not columns.empty:
                average_columns = f"{columns.mean():.1f}"

        if "name" in metadata_data.columns:
            dataset_names = ", ".join(metadata_data["name"].head(10).astype(str))

        summary_parts.extend([
            "",
            "Dataset metadata summary:",
            f"- Total datasets: {len(metadata_data)}",
            f"- Combined dataset rows: {total_rows}",
            f"- Average number of columns: {average_columns}",
            f"- Dataset names: {dataset_names}"
        ])

        if "dataset" in question.lower() or "metadata" in question.lower():
            summary_parts.extend([
                "",
                "Dataset metadata rows:",
                format_rows(
                    metadata_data,
                    ["dataset_id", "name", "rows", "columns", "uploaded_by", "upload_date"]
                )
            ])

    if missing_tables:
        summary_parts.extend([
            "",
            "Unavailable tables:",
            ", ".join(missing_tables),
            "If a user asks about unavailable data, explain that the CSV data "
            "must be migrated into SQLite first."
        ])

    if len(summary_parts) == 4:
        summary_parts.append("")
        summary_parts.append(
            "No migrated dashboard tables were available in SQLite."
        )

    return "\n".join(summary_parts)


def ask_smartboyai(message_history, api_key, database_context):
    """Send the conversation history to Groq and return the assistant reply."""
    try:
        from groq import Groq
    except ImportError:
        return (
            "The Groq package is not installed yet. "
            "Install the project requirements before using SmartBoyAI."
        )

    client = Groq(api_key=api_key)

    system_message = {
        "role": "system",
        "content": (
            "You are SmartBoyAI, a helpful cybersecurity and IT support "
            "assistant for a first-year computer science coursework project. "
            "Keep answers clear, safe, and beginner-friendly. Help users "
            "understand cyber incidents, IT tickets, and dataset questions. "
            "Use the hidden database context below when answering questions "
            "about the current dashboard or project data. If matching dashboard "
            "rows are included, use them to give specific answers. Do not "
            "pretend to know data that is not included. If tables are missing, "
            "tell the user to migrate the CSV data into SQLite first.\n\n"
            f"{database_context}"
        )
    }

    messages = [system_message] + message_history

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4
    )

    return completion.choices[0].message.content


if "messages" not in st.session_state:
    st.session_state["messages"] = []


api_key = get_groq_api_key()

if api_key == "":
    ai_status = "CONFIGURATION REQUIRED"
    ai_status_accent = "amber"
else:
    ai_status = "AI GATEWAY READY"
    ai_status_accent = "green"

ui.page_header(
    "SmartBoyAI Assistant",
    "Database-aware cybersecurity and IT support",
    status=ai_status,
    status_accent=ai_status_accent,
    logo_path="assets/logos/smartboyai_logo.png",
    logo_text="AI",
    logo_alt="SmartBoyAI logo",
)
session_column, safety_column = st.columns(2)

with session_column:
    ui.status_card(
        "Authenticated operator",
        f"AI workspace active for {st.session_state['username']}.",
        accent="green",
    )

with safety_column:
    ui.status_card(
        "Sensitive data boundary",
        "Do not enter passwords, API keys, personal information, or other "
        "private data.",
        accent="amber",
    )

if api_key == "":
    ui.status_card(
        "AI gateway unavailable",
        "Add GROQ_API_KEY to .streamlit/secrets.toml before using SmartBoyAI.",
        accent="red",
    )

ui.section_heading(
    "Secure conversation",
    "Ask about current cyber incidents, IT tickets, or migrated dataset summaries.",
)

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_prompt = st.chat_input("Ask SmartBoyAI about the Gatekeeper data...")

if user_prompt:
    st.session_state["messages"].append(
        {
            "role": "user",
            "content": user_prompt
        }
    )

    with st.chat_message("user"):
        st.write(user_prompt)

    if api_key == "":
        assistant_reply = (
            "SmartBoyAI cannot answer yet because the Groq API key is missing."
        )
    else:
        with st.spinner("SmartBoyAI is thinking..."):
            try:
                database_context = create_database_context(user_prompt)
                assistant_reply = ask_smartboyai(
                    st.session_state["messages"],
                    api_key,
                    database_context
                )
            except Exception as error:
                assistant_reply = "SmartBoyAI could not get a response."
                st.caption(f"Technical detail: {error}")

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": assistant_reply
        }
    )

    with st.chat_message("assistant"):
        st.write(assistant_reply)
