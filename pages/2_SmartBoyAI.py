import streamlit as st

from app_model import db
from app_model.logic import cyber_incidents


st.set_page_config(
    page_title="SmartBoyAI",
    page_icon="S",
    layout="wide"
)


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "username" not in st.session_state:
    st.session_state["username"] = ""


if not st.session_state["logged_in"]:
    st.warning("Please log in before using SmartBoyAI.")
    st.info(
        "Go to the home page, enter your username and password, and then "
        "return to SmartBoyAI after a successful login."
    )

    if st.button("Go to home page"):
        st.switch_page("home.py")

    st.stop()


st.sidebar.success(f"Logged in as: {st.session_state['username']}")

if st.sidebar.button("Log out"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.switch_page("home.py")


def get_groq_api_key():
    """Return the Groq API key from Streamlit secrets."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return ""


def load_cyber_incident_data():
    """Load cyber incident data from the SQLite database."""
    conn = db.get_connection()

    try:
        data = cyber_incidents.get_all_cyber_incidents(conn)
    finally:
        conn.close()

    return data


def format_counts(counts):
    """Turn a pandas value_counts result into simple text."""
    if counts.empty:
        return "No records found."

    count_lines = []

    for name, count in counts.items():
        count_lines.append(f"- {name}: {count}")

    return "\n".join(count_lines)


def create_cyber_incident_summary():
    """Create a short text summary of the dashboard data for SmartBoyAI."""
    try:
        data = load_cyber_incident_data()
    except Exception:
        return "Cyber incident data could not be loaded from SQLite."

    if data.empty:
        return "The cyber incident table is empty."

    severity_counts = data["severity"].value_counts()
    category_counts = data["category"].value_counts()
    status_counts = data["status"].value_counts()

    summary = f"""
Cyber incident dashboard data summary:

Total number of incidents: {len(data)}

Severity counts:
{format_counts(severity_counts)}

Category counts:
{format_counts(category_counts)}

Status counts:
{format_counts(status_counts)}
"""

    return summary.strip()


def ask_smartboyai(message_history, api_key, dataset_summary):
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
            "Use the dashboard data summary below when answering questions "
            "about the current cyber incident dashboard.\n\n"
            f"{dataset_summary}"
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


st.title("SmartBoyAI")
st.success(f"Welcome, {st.session_state['username']}. You are logged in.")
st.write(
    "SmartBoyAI can help explain cybersecurity incidents, IT tickets, "
    "and dataset-related questions in simple language."
)
st.warning(
    "Do not enter private passwords, API keys, personal information, or other "
    "sensitive data into SmartBoyAI."
)

api_key = get_groq_api_key()
dataset_summary = create_cyber_incident_summary()

with st.expander("Current dashboard data summary"):
    st.markdown(dataset_summary)

if api_key == "":
    st.info(
        "SmartBoyAI is not configured yet. Add your Groq API key to "
        ".streamlit/secrets.toml as GROQ_API_KEY before using this page."
    )

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_prompt = st.chat_input("Ask SmartBoyAI a question...")

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
                assistant_reply = ask_smartboyai(
                    st.session_state["messages"],
                    api_key,
                    dataset_summary
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
