import pandas as pd
import streamlit as st

from app_model import db
from app_model.logic import cyber_incidents


st.set_page_config(
    page_title="Gatekeeper System Dashboard",
    page_icon="🛡️",
    layout="wide"
)


def load_cyber_incident_data():
    """Load cyber incident data from the SQLite database."""
    conn = db.get_connection()
    data = cyber_incidents.get_all_cyber_incidents(conn)
    conn.close()

    data["timestamp"] = pd.to_datetime(data["timestamp"])

    return data


st.title("🛡️ Gatekeeper System Dashboard")
st.write(
    "This dashboard displays cyber incident data stored in the SQLite database. "
    "Use the sidebar filter to explore incidents by severity."
)

try:
    data = load_cyber_incident_data()

    st.sidebar.header("Dashboard Filters")

    severity_options = ["All"] + sorted(data["severity"].unique().tolist())
    selected_severity = st.sidebar.selectbox(
        "Select incident severity:",
        severity_options
    )

    if selected_severity == "All":
        filtered_data = data
    else:
        filtered_data = data[data["severity"] == selected_severity]

    st.subheader("Cyber Incident Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total incidents", len(filtered_data))

    with col2:
        st.metric("Unique categories", filtered_data["category"].nunique())

    with col3:
        st.metric("Unique statuses", filtered_data["status"].nunique())

    st.subheader("Incident Visualisations")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("Incidents by category")
        category_counts = filtered_data["category"].value_counts()
        st.bar_chart(category_counts)

    with chart_col2:
        st.write("Incidents by status")
        status_counts = filtered_data["status"].value_counts()
        st.bar_chart(status_counts)

    st.subheader("Filtered Cyber Incident Table")
    st.write(
        "The table below shows the cyber incident records based on the selected severity filter."
    )
    st.dataframe(filtered_data, use_container_width=True)

    st.subheader("Dashboard Note")
    st.write(
        "This dashboard helps identify which cyber incident categories and statuses appear most often. "
        "The sidebar filter makes the dashboard interactive by allowing the user to focus on one severity level."
    )

except Exception:
    st.error("The cyber incident data could not be loaded.")
    st.info("Make sure you have migrated the CSV datasets into SQLite using option 6 in main.py.")