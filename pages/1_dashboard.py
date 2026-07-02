"""Protected cyber incident dashboard for Gatekeeper."""

import math

import altair as alt
import pandas as pd
import streamlit as st

from app_model import db, ui
from app_model.logic import cyber_incidents


REQUIRED_INCIDENT_COLUMNS = {
    "timestamp",
    "severity",
    "category",
    "status",
}
PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]
CHART_HEIGHT = 270


st.set_page_config(
    page_title="Cyber Incident Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)

for key, default_value in {"logged_in": False, "username": ""}.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

ui.apply_theme()
ui.sidebar_logo("assets/logos/dashboard_logo.png")


if not st.session_state["logged_in"]:
    ui.page_header(
        "Restricted Area",
        "Authentication is required to open the Security Dashboard.",
        status="ACCESS DENIED",
        status_accent="red",
    )
    st.warning("🔒 Return to Gatekeeper home and authenticate to view incident data.")
    ui.route_spacing()

    if st.button("Go to home page", icon=":material/home:"):
        st.switch_page("home.py")

    st.stop()


ui.content_profile_control()


def load_cyber_incident_data():
    """Load and validate cyber incident data from SQLite."""
    conn = db.get_connection()

    try:
        data = cyber_incidents.get_all_cyber_incidents(conn)
    finally:
        conn.close()

    missing_columns = REQUIRED_INCIDENT_COLUMNS.difference(data.columns)

    if missing_columns:
        missing_names = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing expected columns: {missing_names}")

    data = data.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    return data


def style_chart(chart):
    """Apply readable colours for the selected Gatekeeper theme."""
    colours = ui.get_chart_colours()
    return (
        chart.properties(background=colours["background"])
        .configure_axis(
            labelColor=colours["text"],
            titleColor=colours["text"],
            gridColor=colours["grid"],
            domainColor=colours["grid"],
        )
        .configure_legend(
            labelColor=colours["text"],
            titleColor=colours["text"],
        )
        .configure_view(strokeOpacity=0)
    )


ui.sidebar_user(st.session_state["username"])

if st.sidebar.button(
    "Log out",
    icon=":material/logout:",
    width="stretch",
):
    ui.logout()
    st.switch_page("home.py")


ui.page_header(
    "Security Dashboard",
    "Cyber incident monitoring and operational intelligence",
    status="DATA LINK ACTIVE",
)


try:
    data = load_cyber_incident_data()
except Exception as error:
    st.error("The cyber incident data could not be loaded from SQLite.")
    st.info(
        "Make sure the CSV datasets have been migrated using the CLI migration "
        "option in main.py."
    )
    st.caption(f"Technical detail: {error}")
    st.stop()

if data.empty:
    st.warning(
        "No cyber incidents are available. Migrate the CSV datasets into SQLite "
        "before opening the dashboard."
    )
    st.stop()

st.sidebar.markdown("### 🎛️ Incident filters")
st.sidebar.caption("The severity filter updates metrics, charts, and records.")

severity_values = sorted(data["severity"].dropna().astype(str).unique().tolist())
selected_severity = st.sidebar.selectbox(
    "Incident severity",
    ["All"] + severity_values,
)

if selected_severity == "All":
    filtered_data = data.copy()
    filter_note = "All severity levels"
else:
    filtered_data = data[data["severity"].astype(str) == selected_severity].copy()
    filter_note = f"{selected_severity} severity only"

if filtered_data.empty:
    st.warning("No incident records match the selected filters.")
    st.stop()

ui.status_card(
    "Authenticated operator",
    f"Workspace active for {st.session_state['username']} · {filter_note}",
    accent="green",
)

ui.section_heading(
    "Incident summary",
    "Current totals for the selected severity scope.",
)
metric_one, metric_two, metric_three, metric_four = st.columns(4)

with metric_one:
    ui.metric_card(
        "Total incidents",
        len(filtered_data),
        note="Records in the active scope",
        accent="cyan",
    )

with metric_two:
    ui.metric_card(
        "Categories",
        filtered_data["category"].nunique(),
        note="Distinct classifications",
        accent="blue",
    )

with metric_three:
    ui.metric_card(
        "Statuses",
        filtered_data["status"].nunique(),
        note="Distinct workflow states",
        accent="green",
    )

with metric_four:
    valid_dates = filtered_data["timestamp"].dropna()
    latest_date = valid_dates.max().strftime("%d %b %Y") if not valid_dates.empty else "N/A"
    ui.metric_card(
        "Latest incident",
        latest_date,
        note="Most recent valid timestamp",
        accent="amber",
    )


ui.section_heading(
    "Incident visualisations",
    "Charts use the same active severity filter as the table below.",
)
chart_column_one, chart_column_two = st.columns(2)

category_counts = (
    filtered_data["category"]
    .fillna("Unknown")
    .value_counts()
    .rename_axis("Category")
    .reset_index(name="Incidents")
    .sort_values("Incidents", ascending=False)
)

status_counts = (
    filtered_data["status"]
    .fillna("Unknown")
    .value_counts()
    .rename_axis("Status")
    .reset_index(name="Incidents")
    .sort_values("Incidents", ascending=False)
)

with chart_column_one:
    with st.container(border=True):
        st.subheader("📂 Incidents by category")
        st.caption(
            "Categories are sorted from most to least common. Hover for exact totals."
        )
        category_chart = (
            alt.Chart(category_counts)
            .mark_bar(color="#0891b2", cornerRadiusEnd=3)
            .encode(
                y=alt.Y("Category:N", sort="-x", title=None),
                x=alt.X("Incidents:Q", title="Number of incidents"),
                tooltip=["Category:N", "Incidents:Q"],
            )
            .properties(height=CHART_HEIGHT)
        )
        st.altair_chart(style_chart(category_chart), width="stretch")

with chart_column_two:
    with st.container(border=True):
        st.subheader("✅ Incidents by status")
        st.caption(
            "Statuses are sorted to show where reports sit in the response workflow."
        )
        status_chart = (
            alt.Chart(status_counts)
            .mark_bar(color="#059669", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("Status:N", sort="-y", title=None),
                y=alt.Y("Incidents:Q", title="Number of incidents"),
                tooltip=["Status:N", "Incidents:Q"],
            )
            .properties(height=CHART_HEIGHT)
        )
        st.altair_chart(style_chart(status_chart), width="stretch")


detail_column_one, detail_column_two = st.columns(2)

heatmap_data = (
    filtered_data.assign(
        severity=filtered_data["severity"].fillna("Unknown"),
        category=filtered_data["category"].fillna("Unknown"),
    )
    .groupby(["severity", "category"])
    .size()
    .reset_index(name="Incidents")
)

with detail_column_one:
    with st.container(border=True):
        st.subheader("🔥 Severity and category heatmap")
        st.caption(
            "Darker cells identify category and severity combinations with more reports."
        )
        heatmap = (
            alt.Chart(heatmap_data)
            .mark_rect(cornerRadius=2)
            .encode(
                x=alt.X("category:N", title="Category"),
                y=alt.Y(
                    "severity:N",
                    title="Severity",
                    sort=SEVERITY_ORDER,
                ),
                color=alt.Color(
                    "Incidents:Q",
                    scale=alt.Scale(scheme="tealblues"),
                    title="Incidents",
                ),
                tooltip=["severity:N", "category:N", "Incidents:Q"],
            )
            .properties(height=CHART_HEIGHT)
        )
        st.altair_chart(style_chart(heatmap), width="stretch")

with detail_column_two:
    with st.container(border=True):
        st.subheader("📈 Incidents over time")
        st.caption("Daily report volume reveals peaks and changes in incident activity.")

        trend_data = filtered_data.dropna(subset=["timestamp"]).copy()

        if trend_data.empty:
            st.info("No valid timestamps are available for a time trend.")
        else:
            trend_data["Date"] = trend_data["timestamp"].dt.date
            trend_counts = (
                trend_data.groupby("Date").size().reset_index(name="Incidents")
            )
            trend_chart = (
                alt.Chart(trend_counts)
                .mark_line(point=True, color="#2563eb", strokeWidth=2)
                .encode(
                    x=alt.X("Date:T", title="Date"),
                    y=alt.Y("Incidents:Q", title="Number of incidents"),
                    tooltip=[
                        alt.Tooltip("Date:T", title="Date"),
                        alt.Tooltip("Incidents:Q", title="Incidents"),
                    ],
                )
                .properties(height=CHART_HEIGHT)
            )
            st.altair_chart(style_chart(trend_chart), width="stretch")


ui.section_heading(
    "Incident records",
    "Browse the filtered SQLite records in manageable pages.",
)

page_size = st.selectbox(
    "Records per page",
    PAGE_SIZE_OPTIONS,
    index=1,
    key="dashboard_page_size",
)

page_signature = f"{selected_severity}:{page_size}:{len(filtered_data)}"

if st.session_state.get("dashboard_page_signature") != page_signature:
    st.session_state["dashboard_page"] = 1
    st.session_state["dashboard_page_signature"] = page_signature

total_records = len(filtered_data)
total_pages = max(1, math.ceil(total_records / page_size))
current_page = min(st.session_state.get("dashboard_page", 1), total_pages)
st.session_state["dashboard_page"] = current_page

start_index = (current_page - 1) * page_size
end_index = min(start_index + page_size, total_records)
page_data = filtered_data.iloc[start_index:end_index]

previous_column, page_column, next_column = st.columns([1, 3, 1])

with previous_column:
    if st.button(
        "Previous",
        icon=":material/chevron_left:",
        disabled=current_page == 1,
        width="stretch",
    ):
        st.session_state["dashboard_page"] -= 1
        st.rerun()

with page_column:
    st.markdown(f"**Page {current_page} of {total_pages}**")

with next_column:
    if st.button(
        "Next",
        icon=":material/chevron_right:",
        disabled=current_page == total_pages,
        width="stretch",
    ):
        st.session_state["dashboard_page"] += 1
        st.rerun()

st.caption(f"Showing records {start_index + 1}–{end_index} of {total_records}")
st.dataframe(ui.style_dataframe(page_data), width="stretch", hide_index=True)

ui.section_heading("Operational insight")
ui.section_card(
    "💡 What this view highlights",
    "The sorted charts reveal common classifications and workflow states, while "
    "the heatmap shows where severity and category overlap. The time trend helps "
    "operators identify changes in reporting activity.",
    accent="amber",
)
