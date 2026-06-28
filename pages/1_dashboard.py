import pandas as pd
import streamlit as st
from app_model import db, ui
from app_model.logic import cyber_incidents


st.set_page_config(
    page_title="Cyber Incident Dashboard",
    page_icon="📊",
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
        "Authentication is required to open the Security Dashboard.",
        status="ACCESS DENIED",
        status_accent="red",
        logo_path="assets/logos/dashboard_logo.png",
        logo_text="D",
        logo_alt="Dashboard logo",
    )
    ui.status_card(
        "Protected route",
        "Return to Gatekeeper home and authenticate before viewing incident data.",
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


def load_cyber_incident_data():
    """Load cyber incident data from the SQLite database."""
    conn = db.get_connection()

    try:
        data = cyber_incidents.get_all_cyber_incidents(conn)
    finally:
        conn.close()

    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")

    return data


ui.page_header(
    "Security Dashboard",
    "Cyber incident monitoring and operational intelligence",
    status="DATA LINK ACTIVE",
    logo_path="assets/logos/dashboard_logo.png",
    logo_text="D",
    logo_alt="Dashboard logo",
)
ui.status_card(
    "Authenticated operator",
    f"Incident workspace active for {st.session_state['username']}.",
    accent="green",
)

try:
    data = load_cyber_incident_data()

    if data.empty:
        ui.status_card(
            "No incident records available",
            "Use option 6 in main.py to migrate the CSV data into SQLite.",
            accent="amber",
        )
        st.stop()

    st.sidebar.markdown("### Incident filters")
    st.sidebar.caption("Filter every dashboard view by incident severity.")

    severity_options = ["All"] + sorted(data["severity"].dropna().unique().tolist())

    selected_severity = st.sidebar.selectbox(
        "Select incident severity:",
        severity_options
    )

    if selected_severity == "All":
        filtered_data = data
    else:
        filtered_data = data[data["severity"] == selected_severity]

    ui.section_heading(
        "Incident summary",
        "Current totals for the selected severity scope.",
    )

    if selected_severity == "All":
        filter_note = "All severity levels"
    else:
        filter_note = f"{selected_severity} severity only"

    ui.status_card(
        "Active data scope",
        filter_note,
        accent="blue",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        ui.metric_card(
            "Total incidents",
            len(filtered_data),
            note="Records in the active scope",
            accent="cyan",
        )

    with col2:
        ui.metric_card(
            "Unique categories",
            filtered_data["category"].nunique(),
            note="Distinct incident classifications",
            accent="blue",
        )

    with col3:
        ui.metric_card(
            "Unique statuses",
            filtered_data["status"].nunique(),
            note="Distinct workflow states",
            accent="green",
        )

    ui.section_heading(
        "Incident visualisations",
        "Category and status distribution for the active data scope.",
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        with st.container(border=True):
            st.markdown("#### Incidents by category")
            st.caption("Frequency of each cyber incident classification.")

            category_counts = filtered_data["category"].value_counts().reset_index()
            category_counts.columns = ["Category", "Number of incidents"]

            st.bar_chart(
                category_counts,
                x="Category",
                y="Number of incidents",
                color="#22D3EE",
            )

    with chart_col2:
        with st.container(border=True):
            st.markdown("#### Incidents by status")
            st.caption("Distribution across open, resolved, and closed states.")

            status_counts = filtered_data["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Number of incidents"]

            st.bar_chart(
                status_counts,
                x="Status",
                y="Number of incidents",
                color="#34D399",
            )

    ui.section_heading(
        "Incident records",
        "Detailed records matching the selected severity filter.",
    )

    st.dataframe(filtered_data, width="stretch")

    ui.section_heading("Operational insight")
    ui.section_card(
        "What this view highlights",
        "This dashboard helps identify the most common cyber incident categories "
        "and shows the current status of reported incidents. The severity filter "
        "allows users to focus on specific risk levels and inspect matching records.",
        accent="amber",
    )

except Exception as error:
    st.error("The cyber incident data could not be loaded.")
    st.info(
        "Make sure you have migrated the CSV datasets into SQLite using option 6 "
        "in main.py."
    )
    st.caption(f"Technical detail: {error}")
