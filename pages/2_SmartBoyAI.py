import os
import pandas as pd
import streamlit as st
from app_model import db, ui
from app_model.logic import cyber_incidents, it_tickets, metadatas, cisa_kev

# AI assistance was used for the Groq integration, system prompt design,
# scope restrictions, database context construction, refactoring, and debugging.

GROQ_KEY_PLACEHOLDERS = {
    "put_your_groq_api_key_here",
    "your_groq_api_key_here",
}

SCOPE_REFUSAL = (
    "I can only help with the Gatekeeper cybersecurity dashboard, incidents, "
    "IT tickets, dataset metadata, CISA KEV records, CVEs, and related "
    "IT/cybersecurity support. Please ask a question related to those areas."
)

ALLOWED_SCOPE_TERMS = {
    "gatekeeper",
    "dashboard",
    "incident",
    "severity",
    "category",
    "status",
    "ticket",
    "dataset",
    "metadata",
    "database",
    "sqlite",
    "cyber",
    "security",
    "phishing",
    "malware",
    "ddos",
    "misconfiguration",
    "unauthorized access",
    "risk",
    "threat",
    "vulnerability",
    "vulnerabilities",
    "cisa",
    "kev",
    "cve",
    "cwe",
    "ransomware",
    "remediation",
    "vendor",
    "vendors",
    "microsoft",
    "attacked",
    "exploited",
    "network",
    "password",
    "authentication",
    "login",
    "server",
    "software",
    "hardware",
    "technical support",
    "it support",
}

UNRELATED_TERMS = {
    "recipe",
    "cook",
    "food",
    "restaurant",
    "movie",
    "music",
    "celebrity",
    "horoscope",
    "relationship advice",
    "fashion",
    "holiday",
    "travel itinerary",
    "joke",
    "football",
    "soccer",
    "sports score",
    "dating advice",
    "life advice",
    "poem",
    "fiction story",
}


st.set_page_config(
    page_title="SmartBoyAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
)

ui.apply_theme()
ui.sidebar_logo("assets/logos/smartboyai_logo.png")
ui.sidebar_theme_control("smartboyai")


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
    )
    ui.status_card(
        "Protected route",
        "Return to Gatekeeper home and authenticate before opening the AI workspace.",
        accent="red",
    )
    ui.route_spacing()

    if st.button("Go to home page", icon=":material/home:"):
        st.switch_page("home.py")

    st.stop()


ui.content_profile_control()


ui.sidebar_user(st.session_state["username"])

if st.sidebar.button(
    "Log out",
    icon=":material/logout:",
    width="stretch",
):
    ui.logout()
    st.switch_page("home.py")


def get_groq_api_key():
    """Return the Groq API key from Streamlit secrets or an environment variable."""
    try:
        api_key = str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        api_key = os.getenv("GROQ_API_KEY", "").strip()

    return "" if api_key in GROQ_KEY_PLACEHOLDERS else api_key


def is_prompt_in_scope(prompt, earlier_messages):
    """Reject clearly unrelated prompts while allowing relevant follow-ups."""
    prompt_lower = prompt.strip().lower()

    if any(term in prompt_lower for term in ALLOWED_SCOPE_TERMS):
        return True

    if any(term in prompt_lower for term in UNRELATED_TERMS):
        return False

    if prompt_lower in {"hi", "hello", "hey", "help", "what can you do?"}:
        return True

    # Short follow-up questions may rely on an earlier in-scope user message.
    recent_user_messages = [
        message["content"].lower()
        for message in earlier_messages[-6:]
        if message.get("role") == "user"
    ]
    recent_context_is_in_scope = any(
        term in earlier_message
        for earlier_message in recent_user_messages
        for term in ALLOWED_SCOPE_TERMS
    )

    if recent_context_is_in_scope:
        return True

    # vague prompts are allowed. The system prompt keeps the answer in scope-
    # and asks for clarification when there is no useful conversation context
    return True


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


def format_top_counts(data, column_name, limit=10):
    """Turn the most common values in one column into simple text."""
    if column_name not in data.columns:
        return "Column not found."

    counts = data[column_name].replace("", "Unknown").fillna("Unknown").value_counts()

    if counts.empty:
        return "No records found."

    return "\n".join(
        f"- {name}: {count}"
        for name, count in counts.head(limit).items()
    )


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
        cisa_data, missing_cisa = load_table(
            conn,
            "cisa_known_exploited_vulnerabilities",
            cisa_kev.get_all_cisa_kev
        )
    finally:
        conn.close()

    for table_name in [missing_cyber, missing_tickets, missing_metadata, missing_cisa]:
        if table_name is not None:
            missing_tables.append(table_name)

    return cyber_data, ticket_data, metadata_data, cisa_data, missing_tables


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


def add_cisa_context(summary_parts, cisa_data, question):
    """Add bounded CISA KEV summaries and a small number of relevant rows."""
    if cisa_data.empty:
        return

    summary_parts.extend([
        "",
        "External CISA Known Exploited Vulnerabilities summary:",
        "Important CISA interpretation rule: the KEV catalogue records known "
        "exploited vulnerability entries. It does not measure confirmed attack "
        "frequency against a company. If the user asks who was 'most attacked', "
        "answer using the vendor/project that appears most often in KEV entries "
        "and clearly explain that this is not the same as being attacked most.",
        f"- Total vulnerabilities: {len(cisa_data)}",
        "- Top vendors/projects:",
        format_top_counts(cisa_data, "vendorProject", limit=10),
        "- Known ransomware campaign usage:",
        format_counts(cisa_data, "knownRansomwareCampaignUse"),
    ])

    if "cwes" in cisa_data.columns:
        cwe_values = []

        for cwe_text in cisa_data["cwes"].fillna("").astype(str):
            for cwe in cwe_text.split(","):
                clean_cwe = cwe.strip()

                if clean_cwe:
                    cwe_values.append(clean_cwe)

        if cwe_values:
            cwe_counts = pd.Series(cwe_values).value_counts().head(10)
            summary_parts.extend([
                "- Top CWE categories:",
                "\n".join(f"- {name}: {count}" for name, count in cwe_counts.items()),
            ])

    question_lower = question.lower()
    matching_cisa = pd.DataFrame()

    cve_terms = [
        word.strip(".,:;!?()[]{}")
        for word in question.split()
        if word.upper().startswith("CVE-")
    ]

    if cve_terms and "cveID" in cisa_data.columns:
        matching_cisa = cisa_data[
            cisa_data["cveID"].str.upper().isin(
                [term.upper() for term in cve_terms]
            )
        ]

    if matching_cisa.empty and any(
        term in question_lower
        for term in ["latest", "recent", "newest", "added"]
    ):
        dated_cisa = cisa_data.copy()
        dated_cisa["dateAddedParsed"] = pd.to_datetime(
            dated_cisa["dateAdded"],
            errors="coerce"
        )
        matching_cisa = dated_cisa.sort_values(
            "dateAddedParsed",
            ascending=False
        ).head(10)

    if matching_cisa.empty:
        for column in ["vendorProject", "product", "knownRansomwareCampaignUse", "cwes"]:
            if column not in cisa_data.columns:
                continue

            values = cisa_data[column].dropna().astype(str).unique()

            for value in values:
                if value and value.lower() in question_lower:
                    matching_cisa = cisa_data[
                        cisa_data[column].astype(str).str.lower() == value.lower()
                    ].head(10)
                    break

            if not matching_cisa.empty:
                break

    if matching_cisa.empty and any(
        term in question_lower
        for term in ["most attacked", "most exploited", "most common", "most affected"]
    ):
        top_vendor_counts = (
            cisa_data["vendorProject"]
            .replace("", "Unknown")
            .fillna("Unknown")
            .value_counts()
            .head(5)
        )
        summary_parts.extend([
            "",
            "Top CISA KEV vendor/project entry counts:",
            "\n".join(
                f"- {vendor}: {count}"
                for vendor, count in top_vendor_counts.items()
            ),
            "For 'most attacked' wording, explain this means most KEV entries, "
            "not proven attack frequency.",
        ])
        matching_cisa = cisa_data[
            cisa_data["vendorProject"].astype(str).isin(
                cisa_data["vendorProject"].value_counts().head(3).index
            )
        ].head(10)

    if not matching_cisa.empty:
        summary_parts.extend([
            "",
            "Question-relevant CISA KEV rows:",
            format_rows(
                matching_cisa,
                [
                    "cveID",
                    "vendorProject",
                    "product",
                    "vulnerabilityName",
                    "dateAdded",
                    "dueDate",
                    "knownRansomwareCampaignUse",
                    "requiredAction",
                    "notes",
                    "cwes",
                ],
                max_rows=10,
            ),
        ])


def create_database_context(question):
    """Create hidden, question-focused database context for SmartBoyAI."""
    cyber_data, ticket_data, metadata_data, cisa_data, missing_tables = load_project_data()

    summary_parts = [
        "Hidden project database context for SmartBoyAI:",
        "",
        "Use this context only to answer the user's current question.",
        "This context is loaded from migrated dashboard tables in SQLite.",
        "It never includes user accounts, login details, API keys, or password hashes.",
        "Do not say that the user can see this context on the page."
    ]
    available_data_found = False

    if not cyber_data.empty:
        available_data_found = True
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
        available_data_found = True
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
        available_data_found = True
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

    if not cisa_data.empty:
        available_data_found = True
        add_cisa_context(summary_parts, cisa_data, question)

    if missing_tables:
        summary_parts.extend([
            "",
            "Unavailable tables:",
            ", ".join(missing_tables),
            "If a user asks about unavailable data, explain that the CSV data "
            "must be migrated into SQLite first."
        ])

    if not available_data_found:
        summary_parts.append("")
        summary_parts.append(
            "No migrated dashboard tables were available in SQLite."
        )

    return "\n".join(summary_parts)


def stream_smartboyai_response(message_history, api_key, database_context):
    """Send the conversation history to Groq and yield streamed reply text."""
    try:
        from groq import Groq
    except ImportError:
        yield (
            "The Groq package is not installed yet. "
            "Install the project requirements before using SmartBoyAI."
        )
        return

    client = Groq(api_key=api_key)

    system_message = {
        "role": "system",
        "content": (
            "You are SmartBoyAI, a helpful cybersecurity and IT support "
            "assistant for a first-year computer science coursework project. "
            "Only answer questions about Gatekeeper, its dashboard and project "
            "database, cyber incidents, IT tickets, dataset metadata, "
            "CISA known exploited vulnerabilities, CVEs, cybersecurity, or IT "
            "support. For every unrelated request, reply "
            f"with exactly: {SCOPE_REFUSAL} Do not add an unrelated answer or "
            "continue with internal incident data after refusing. "
            "Use the previous conversation messages when the user asks a vague "
            "follow-up such as 'why?', 'explain that', or 'what does this mean?'. "
            "If a vague request has no useful earlier context, ask the user to "
            "clarify which Gatekeeper, cybersecurity, database, or IT support "
            "topic they need help with. "
            "Keep answers clear, safe, and beginner-friendly. Help users "
            "understand cyber incidents, IT tickets, dataset questions, and "
            "CISA KEV threat-intelligence questions. "
            "For CISA KEV questions, never describe a top vendor as the most "
            "attacked. If the user asks who was most attacked, explain that "
            "the data shows which vendor/project appears most often in KEV "
            "entries, not confirmed attack frequency. "
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
        temperature=0.4,
        stream=True,
    )

    for chunk in completion:
        if not chunk.choices:
            continue

        delta = getattr(chunk.choices[0], "delta", None)
        content = getattr(delta, "content", None)

        if content:
            yield content


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

    earlier_messages = st.session_state["messages"][:-1]
    prompt_in_scope = is_prompt_in_scope(user_prompt, earlier_messages)

    if not prompt_in_scope:
        assistant_reply = SCOPE_REFUSAL
    elif api_key == "":
        assistant_reply = (
            "SmartBoyAI cannot answer yet because the Groq API key is missing."
        )
    else:
        assistant_reply = ""
        with st.chat_message("assistant"):
            response_placeholder = st.empty()

            try:
                database_context = create_database_context(user_prompt)

                for text_chunk in stream_smartboyai_response(
                    st.session_state["messages"],
                    api_key,
                    database_context
                ):
                    assistant_reply += text_chunk
                    response_placeholder.markdown(assistant_reply)

                if assistant_reply.strip() == "":
                    assistant_reply = "SmartBoyAI did not return a response."
                    response_placeholder.warning(assistant_reply)

            except Exception as error:
                assistant_reply = "SmartBoyAI could not get a response."
                response_placeholder.error(assistant_reply)
                st.caption(f"Technical detail: {type(error).__name__}")

    if not (api_key != "" and prompt_in_scope):
        with st.chat_message("assistant"):
            st.write(assistant_reply)

    st.session_state["messages"].append(
        {
            "role": "assistant",
            "content": assistant_reply
        }
    )
