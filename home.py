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

    try:
        data = cyber_incidents.get_all_cyber_incidents(conn)
    finally:
        conn.close()

    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")

    return data


st.title(" 🛡️ Gatekeeper System Dashboard 🛡️ ")
st.write(
    "This Streamlit dashboard shows cyber incident records that have been "
    "migrated from CSV files into the SQLite database. Use the sidebar to filter "
    "the data by incident severity."
)

try:
    data = load_cyber_incident_data()

    if data.empty:
        st.warning("No cyber incident records were found in the database.")
        st.info("Use option 6 in main.py to migrate the CSV data into SQLite.")
        st.stop()

    st.sidebar.header("Dashboard Filters")
    st.sidebar.write("Choose a severity level to update the charts and table.")

    severity_options = ["All"] + sorted(data["severity"].dropna().unique().tolist())

    selected_severity = st.sidebar.selectbox(
        "Select incident severity:",
        severity_options
    )

    if selected_severity == "All":
        filtered_data = data
    else:
        filtered_data = data[data["severity"] == selected_severity]

    st.subheader("Cyber Incident Summary")

    if selected_severity == "All":
        st.write("Currently showing: **All** cyber incidents.")
    else:
        st.write(f"Currently showing: **{selected_severity}** severity incidents.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total incidents", len(filtered_data))

    with col2:
        st.metric("Unique categories", filtered_data["category"].nunique())

    with col3:
        st.metric("Unique statuses", filtered_data["status"].nunique())

    st.subheader("Incident Visualisations")
    st.write(
        "The charts below summarise the filtered cyber incident records. "
        "They update when a different severity is selected in the sidebar."
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.write("Incidents by category")
        st.caption("This chart shows which type of cyber incident appears most often.")

        category_counts = filtered_data["category"].value_counts().reset_index()
        category_counts.columns = ["Category", "Number of incidents"]

        st.bar_chart(
            category_counts,
            x="Category",
            y="Number of incidents"
        )

    with chart_col2:
        st.write("Incidents by status")
        st.caption("This chart shows whether incidents are open, resolved, or closed.")

        status_counts = filtered_data["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Number of incidents"]

        st.bar_chart(
            status_counts,
            x="Status",
            y="Number of incidents"
        )

    st.subheader("Filtered Cyber Incident Table")
    st.write(
        "The table below shows the full incident records that match the selected "
        "severity filter. This makes it possible to inspect the details behind "
        "the summary charts."
    )

    st.dataframe(filtered_data, width="stretch")

    st.subheader("Dashboard Insight")
    st.write(
        "This dashboard helps identify the most common cyber incident categories "
        "and shows the current status of reported incidents. The severity filter "
        "allows users to focus on specific risk levels and inspect the matching records."
    )

except Exception as error:
    st.error("The cyber incident data could not be loaded.")
    st.info("Make sure you have migrated the CSV datasets into SQLite using option 6 in main.py.")
    st.caption(f"Technical detail: {error}")