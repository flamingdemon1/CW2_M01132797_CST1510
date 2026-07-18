"""Protected cyber incident dashboard for Gatekeeper."""

import math
import sqlite3
import altair as alt
import pandas as pd
import streamlit as st
from app_model import db, export_service, ui
from app_model.logic import cyber_incidents, cisa_kev, it_tickets, metadatas


REQUIRED_INCIDENT_COLUMNS = {
    "timestamp",
    "severity",
    "category",
    "status",
}
REQUIRED_TICKET_COLUMNS = {
    "ticket_id",
    "priority",
    "status",
    "resolution_time_hours",
}
REQUIRED_METADATA_COLUMNS = {
    "name",
    "rows",
    "columns",
}
CISA_TABLE_COLUMNS = [
    "cveID",
    "vendorProject",
    "product",
    "vulnerabilityName",
    "dateAdded",
    "dueDate",
    "knownRansomwareCampaignUse",
    "cwes",
]
SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]
CHART_HEIGHT = 270
CHART_PADDING = {"left": 25, "right": 35, "top": 10, "bottom": 25}
STATUS_COLOURS = {
    "Open": "#e11d48",
    "In Progress": "#d97706",
    "Resolved": "#059669",
    "Closed": "#2563eb",
    "Unknown": "#64748b",
}
VISUALISATION_OPTIONS = [
    "Category",
    "Status",
    "Severity Heatmap",
    "Time Trend",
]


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
ui.sidebar_theme_control("dashboard")


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

if not str(st.session_state.get("username", "")).strip():
    st.error("Your session is missing a username. Please log in again.")
    ui.logout()

    if st.button("Return to login", icon=":material/login:"):
        st.switch_page("home.py")

    st.stop()

active_username = str(st.session_state["username"]).strip()


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


def load_cisa_kev_data():
    """Load the external CISA KEV extension from its separate SQLite table."""
    conn = db.get_connection()

    try:
        data = cisa_kev.get_all_cisa_kev(conn)
    finally:
        conn.close()

    missing_columns = set(cisa_kev.EXPECTED_COLUMNS).difference(data.columns)

    if missing_columns:
        missing_names = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing CISA KEV columns: {missing_names}")

    data = data.copy()
    data["dateAddedParsed"] = pd.to_datetime(data["dateAdded"], errors="coerce")
    data["dueDateParsed"] = pd.to_datetime(data["dueDate"], errors="coerce")
    data["yearAdded"] = data["dateAddedParsed"].dt.year
    return data


def load_it_ticket_data():
    """Load the required IT ticket dataset from SQLite."""
    conn = db.get_connection()

    try:
        data = it_tickets.get_all_it_tickets(conn)
    finally:
        conn.close()

    missing_columns = REQUIRED_TICKET_COLUMNS.difference(data.columns)

    if missing_columns:
        missing_names = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing IT ticket columns: {missing_names}")

    data = data.copy()
    data["resolution_time_hours"] = pd.to_numeric(
        data["resolution_time_hours"],
        errors="coerce",
    )
    return data


def load_dataset_metadata():
    """Load the required dataset metadata table from SQLite."""
    conn = db.get_connection()

    try:
        data = metadatas.get_all_datasets_metadata(conn)
    finally:
        conn.close()

    missing_columns = REQUIRED_METADATA_COLUMNS.difference(data.columns)

    if missing_columns:
        missing_names = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing dataset metadata columns: {missing_names}")

    data = data.copy()
    data["rows"] = pd.to_numeric(data["rows"], errors="coerce")
    data["columns"] = pd.to_numeric(data["columns"], errors="coerce")
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
            labelPadding=6,
            titlePadding=12,
        )
        .configure_legend(
            labelColor=colours["text"],
            titleColor=colours["text"],
            labelPadding=6,
            titlePadding=8,
            padding=10,
        )
        .configure_view(strokeOpacity=0)
    )


def format_summary_counts(data, column_name):
    """Format one dashboard value-count series for saved text content."""
    counts = data[column_name].fillna("Unknown").value_counts()
    return ", ".join(f"{name}: {count}" for name, count in counts.items())


def get_top_cwes(data, limit=10):
    """Split the CISA CWE column and return the most common categories."""
    if "cwes" not in data.columns:
        return pd.DataFrame(columns=["CWE", "Vulnerabilities"])

    cwe_values = []

    for cwe_text in data["cwes"].fillna("").astype(str):
        for cwe in cwe_text.split(","):
            clean_cwe = cwe.strip()

            if clean_cwe:
                cwe_values.append(clean_cwe)

    if not cwe_values:
        return pd.DataFrame(columns=["CWE", "Vulnerabilities"])

    return (
        pd.Series(cwe_values)
        .value_counts()
        .head(limit)
        .rename_axis("CWE")
        .reset_index(name="Vulnerabilities")
    )


def paginate_dataframe(data, state_prefix, default_page_size=20):
    """Return the current page of a DataFrame and display table controls."""
    total_records = len(data)
    max_page_size = max(total_records, 1)
    current_page_size = int(
        st.session_state.get(f"{state_prefix}_records_per_page", default_page_size)
    )
    current_page_size = min(max(current_page_size, 1), max_page_size)

    page_size = st.number_input(
        "Records per page",
        min_value=1,
        max_value=max_page_size,
        value=current_page_size,
        step=1,
        format="%d",
        key=f"{state_prefix}_records_per_page",
        disabled=total_records == 0,
    )
    page_signature = f"{state_prefix}:{page_size}:{total_records}"

    if st.session_state.get(f"{state_prefix}_page_signature") != page_signature:
        st.session_state[f"{state_prefix}_page"] = 1
        st.session_state[f"{state_prefix}_page_signature"] = page_signature

    total_pages = max(1, math.ceil(total_records / page_size))
    current_page = int(st.session_state.get(f"{state_prefix}_page", 1))
    current_page = min(max(current_page, 1), total_pages)
    st.session_state[f"{state_prefix}_page"] = current_page

    start_index = (current_page - 1) * page_size
    end_index = min(start_index + page_size, total_records)
    page_data = data.iloc[start_index:end_index]

    ui.themed_dataframe(page_data, height=380)

    if total_records == 0:
        st.caption("Showing 0 records. Try changing the filters.")
    else:
        st.caption(f"Showing records {start_index + 1}-{end_index} of {total_records}")

    previous_column, page_column, next_column = st.columns([1, 3, 1])

    with previous_column:
        if st.button(
            "Previous",
            icon=":material/chevron_left:",
            disabled=current_page == 1,
            width="stretch",
            key=f"{state_prefix}_previous",
        ):
            st.session_state[f"{state_prefix}_page"] -= 1
            st.rerun()

    with page_column:
        st.markdown(f"**Page {current_page} of {total_pages}**")
        st.caption(f"{total_records} filtered records | {page_size} records per page")

    with next_column:
        if st.button(
            "Next",
            icon=":material/chevron_right:",
            disabled=current_page == total_pages,
            width="stretch",
            key=f"{state_prefix}_next",
        ):
            st.session_state[f"{state_prefix}_page"] += 1
            st.rerun()

    return page_data


def create_dashboard_summary(data, severity_filter):
    """Create the text stored for the current filtered dashboard view."""
    return "\n".join(
        [
            f"Selected severity filter: {severity_filter}",
            f"Total incidents shown: {len(data)}",
            f"Category counts: {format_summary_counts(data, 'category')}",
            f"Status counts: {format_summary_counts(data, 'status')}",
            f"Severity counts: {format_summary_counts(data, 'severity')}",
            "Pagination affects only the displayed records and does not change "
            "this saved dashboard summary.",
        ]
    )


def save_dashboard_summary(username, severity_filter, data):
    """Save the active dashboard summary through the shared export service."""
    connection = db.get_connection()

    try:
        return export_service.save_result_to_database(
            connection,
            username,
            "Dashboard Summary",
            f"Cyber Incident Dashboard - {severity_filter}",
            create_dashboard_summary(data, severity_filter),
            save_source="Streamlit Dashboard",
        )
    finally:
        connection.close()


def load_user_saved_results(username):
    """Load saved-result summaries belonging to the logged-in user."""
    connection = db.get_connection()

    try:
        return export_service.get_saved_results(connection, username)
    finally:
        connection.close()


def load_user_saved_result(result_id, username):
    """Load one full saved result while enforcing ownership."""
    connection = db.get_connection()

    try:
        return export_service.get_saved_result(connection, result_id, username)
    finally:
        connection.close()


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
    f"Workspace active for {active_username} · {filter_note}",
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
    "Save dashboard summary",
    "Store the current filtered summary in the shared SQLite saved-results table.",
)
st.caption("Saved summaries appear in the Saved Results section below the records table.")

save_message = st.session_state.pop("dashboard_save_message", None)

if save_message:
    st.success(save_message)

if st.button(
    "Save dashboard summary to database",
    icon=":material/save:",
    type="primary",
):
    try:
        saved_result_id = save_dashboard_summary(
            active_username,
            selected_severity,
            filtered_data,
        )
        st.session_state["dashboard_save_message"] = (
            f"Dashboard summary saved successfully with ID {saved_result_id}."
        )
        st.rerun()
    except (sqlite3.Error, OSError, ValueError):
        st.error("The dashboard summary could not be saved to SQLite.")
    except Exception as error:
        st.error("The dashboard summary could not be saved.")
        st.caption(f"Technical detail: {type(error).__name__}")


ui.section_heading(
    "Incident visualisations",
    "Charts use the same active severity filter as the table below.",
)
selected_visualisations = st.multiselect(
    "Choose visualisations to display",
    VISUALISATION_OPTIONS,
    default=VISUALISATION_OPTIONS,
    key="dashboard_visualisations",
)

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
status_counts["Colour"] = (
    status_counts["Status"].map(STATUS_COLOURS).fillna("#64748b")
)

heatmap_counts = (
    filtered_data.assign(
        severity=filtered_data["severity"].fillna("Unknown"),
        category=filtered_data["category"].fillna("Unknown"),
    )
    .groupby(["severity", "category"])
    .size()
)
heatmap_categories = category_counts["Category"].tolist()
heatmap_severities = [
    severity
    for severity in SEVERITY_ORDER
    if severity in heatmap_counts.index.get_level_values("severity")
]
heatmap_severities.extend(
    sorted(
        severity
        for severity in heatmap_counts.index.get_level_values("severity").unique()
        if severity not in heatmap_severities
    )
)
heatmap_index = pd.MultiIndex.from_product(
    [heatmap_severities, heatmap_categories],
    names=["severity", "category"],
)
heatmap_data = (
    heatmap_counts.reindex(heatmap_index, fill_value=0)
    .rename("Incidents")
    .reset_index()
)
chart_text_colour = ui.get_chart_colours()["text"]

category_bars = (
    alt.Chart(category_counts)
    .mark_bar(color="#0891b2", cornerRadiusEnd=3)
    .encode(
        y=alt.Y(
            "Category:N",
            sort="-x",
            title="Incident category",
            axis=alt.Axis(labelLimit=150),
        ),
        x=alt.X(
            "Incidents:Q",
            title="Incident count",
            scale=alt.Scale(zero=True),
            axis=alt.Axis(tickMinStep=1),
        ),
        tooltip=[
            alt.Tooltip("Category:N", title="Category"),
            alt.Tooltip("Incidents:Q", title="Incidents"),
        ],
    )
)
category_labels = category_bars.mark_text(
    align="left",
    baseline="middle",
    dx=5,
    color=chart_text_colour,
).encode(text=alt.Text("Incidents:Q"))
category_chart = (category_bars + category_labels).properties(
    height=CHART_HEIGHT,
    padding=CHART_PADDING,
)

status_bars = (
    alt.Chart(status_counts)
    .mark_bar(cornerRadiusEnd=3)
    .encode(
        y=alt.Y(
            "Status:N",
            sort="-x",
            title="Workflow status",
            axis=alt.Axis(labelLimit=150),
        ),
        x=alt.X(
            "Incidents:Q",
            title="Incident count",
            scale=alt.Scale(zero=True),
            axis=alt.Axis(tickMinStep=1),
        ),
        color=alt.Color("Colour:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("Status:N", title="Status"),
            alt.Tooltip("Incidents:Q", title="Incidents"),
        ],
    )
)
status_labels = status_bars.mark_text(
    align="left",
    baseline="middle",
    dx=5,
    color=chart_text_colour,
).encode(text=alt.Text("Incidents:Q"))
status_chart = (status_bars + status_labels).properties(
    height=CHART_HEIGHT,
    padding=CHART_PADDING,
)

heatmap_rectangles = (
    alt.Chart(heatmap_data)
    .mark_rect(cornerRadius=2)
    .encode(
        x=alt.X(
            "category:N",
            title="Incident category",
            sort=heatmap_categories,
            axis=alt.Axis(labelAngle=0, labelLimit=90),
        ),
        y=alt.Y(
            "severity:N",
            title="Severity level",
            sort=heatmap_severities,
        ),
        color=alt.Color(
            "Incidents:Q",
            scale=alt.Scale(scheme="tealblues"),
            title="Incident count",
            legend=alt.Legend(orient="bottom", direction="horizontal"),
        ),
        tooltip=[
            alt.Tooltip("severity:N", title="Severity"),
            alt.Tooltip("category:N", title="Category"),
            alt.Tooltip("Incidents:Q", title="Incidents"),
        ],
    )
)
heatmap_midpoint = max(1, heatmap_data["Incidents"].max() * 0.55)
heatmap_labels = heatmap_rectangles.mark_text(fontWeight="bold").encode(
    text=alt.Text("Incidents:Q"),
    color=alt.condition(
        alt.datum.Incidents >= heatmap_midpoint,
        alt.value("#ffffff"),
        alt.value(chart_text_colour),
    ),
)
heatmap = (heatmap_rectangles + heatmap_labels).properties(
    height=CHART_HEIGHT,
    padding=CHART_PADDING,
)

trend_data = filtered_data.dropna(subset=["timestamp"]).copy()
trend_chart = None

if not trend_data.empty:
    trend_data["Date"] = trend_data["timestamp"].dt.date
    trend_counts = trend_data.groupby("Date").size().reset_index(name="Incidents")
    trend_chart = (
        alt.Chart(trend_counts)
        .mark_line(point=True, color="#2563eb", strokeWidth=2)
        .encode(
            x=alt.X(
                "Date:T",
                title="Incident date",
                axis=alt.Axis(format="%d %b", tickCount=6, labelAngle=0),
            ),
            y=alt.Y(
                "Incidents:Q",
                title="Daily incident count",
                scale=alt.Scale(zero=True),
                axis=alt.Axis(tickMinStep=1),
            ),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Incidents:Q", title="Incidents"),
            ],
        )
        .properties(height=CHART_HEIGHT, padding=CHART_PADDING)
    )

chart_definitions = [
    {
        "name": "Category",
        "title": "📂 Incidents by category",
        "caption": "Compares classifications from most to least common; labels show exact totals.",
        "chart": category_chart,
    },
    {
        "name": "Status",
        "title": "✅ Incidents by status",
        "caption": "Shows response workload by state; red/amber need attention and green indicates resolution.",
        "chart": status_chart,
    },
    {
        "name": "Severity Heatmap",
        "title": "🔥 Severity and category heatmap",
        "caption": "Darker cells and larger counts identify concentrated category/severity combinations.",
        "chart": heatmap,
    },
    {
        "name": "Time Trend",
        "title": "📈 Incidents over time",
        "caption": "Tracks daily volume; peaks identify dates with unusually high incident activity.",
        "chart": trend_chart,
    },
]

visible_charts = [
    chart
    for chart in chart_definitions
    if chart["name"] in selected_visualisations
]

if not visible_charts:
    st.info("No visualisations selected.")

for row_start in range(0, len(visible_charts), 2):
    chart_row = visible_charts[row_start : row_start + 2]
    chart_columns = st.columns(len(chart_row))

    for chart_column, chart_details in zip(chart_columns, chart_row):
        with chart_column:
            with st.container(border=True):
                st.subheader(chart_details["title"])
                st.caption(chart_details["caption"])

                if chart_details["chart"] is None:
                    st.info("No valid timestamps are available for a time trend.")
                else:
                    st.altair_chart(
                        style_chart(chart_details["chart"]),
                        width="stretch",
                    )


ui.section_heading(
    "Incident records",
    "Browse the filtered SQLite records in manageable pages.",
)

paginate_dataframe(filtered_data, "dashboard", default_page_size=20)

ui.section_heading(
    "Saved Results",
    "Recent SQLite results saved by your account.",
)

try:
    saved_results = load_user_saved_results(active_username)

    if not saved_results:
        st.info(
            "No saved results found yet. Click 'Save dashboard summary to database' "
            "above to store the current dashboard summary."
        )
    else:
        recent_saved_results = saved_results[:10]
        st.caption("Showing the 10 most recent saved results for this account.")
        saved_results_table = pd.DataFrame(
            [
                {
                    "ID": result["id"],
                    "Result type": result["result_type"],
                    "Title": result["title"],
                    "Created at": result["created_at"],
                    "Save source": result["save_source"],
                }
                for result in recent_saved_results
            ]
        )
        ui.themed_dataframe(saved_results_table, height=360)

        result_ids = [result["id"] for result in recent_saved_results]
        selected_result_id = st.selectbox(
            "View saved result content",
            [None] + result_ids,
            format_func=lambda result_id: (
                "Select a saved result"
                if result_id is None
                else f"Result ID {result_id}"
            ),
        )

        if selected_result_id is not None:
            selected_result = load_user_saved_result(
                selected_result_id,
                active_username,
            )

            if selected_result is None:
                st.error("The saved result could not be found.")
            else:
                with st.expander(
                    f"{selected_result['title']} (ID {selected_result_id})",
                    expanded=True,
                ):
                    st.text(selected_result["content"])

except (sqlite3.Error, OSError):
    st.error("Saved results could not be loaded from SQLite.")
except Exception as error:
    st.error("Saved results could not be displayed.")
    st.caption(f"Technical detail: {type(error).__name__}")


ui.section_heading(
    "Coursework dataset coverage",
    "Compact Streamlit summaries for the required IT ticket and metadata datasets.",
)
st.caption(
    "The main dashboard focuses on cyber incidents, while these summaries show "
    "that the other required CSV datasets are also migrated into SQLite."
)

ticket_tab, metadata_tab = st.tabs(["IT Operations", "Dataset Metadata"])

with ticket_tab:
    try:
        ticket_data = load_it_ticket_data()
    except Exception as error:
        ticket_data = pd.DataFrame()
        st.info(
            "IT ticket data is not available yet. Use the CLI migration option "
            "to migrate DATA/it_tickets.csv into SQLite."
        )
        st.caption(f"Technical detail: {type(error).__name__}")

    if not ticket_data.empty:
        ticket_metric_columns = st.columns(4)
        open_tickets = int(
            ticket_data["status"].fillna("").str.lower().eq("open").sum()
        )
        high_priority = int(
            ticket_data["priority"]
            .fillna("")
            .str.lower()
            .isin(["high", "critical"])
            .sum()
        )
        average_resolution = ticket_data["resolution_time_hours"].dropna().mean()

        with ticket_metric_columns[0]:
            ui.metric_card(
                "Total tickets",
                len(ticket_data),
                note="Rows in it_tickets",
                accent="blue",
            )

        with ticket_metric_columns[1]:
            ui.metric_card(
                "Open tickets",
                open_tickets,
                note="Current open workload",
                accent="red",
            )

        with ticket_metric_columns[2]:
            ui.metric_card(
                "High/Critical priority",
                high_priority,
                note="Tickets needing attention",
                accent="amber",
            )

        with ticket_metric_columns[3]:
            ui.metric_card(
                "Avg resolution",
                (
                    f"{average_resolution:.1f}h"
                    if not pd.isna(average_resolution)
                    else "N/A"
                ),
                note="resolution_time_hours",
                accent="green",
            )

        priority_counts = (
            ticket_data["priority"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Priority")
            .reset_index(name="Tickets")
        )
        priority_chart = (
            alt.Chart(priority_counts)
            .mark_bar(color="#d97706", cornerRadiusEnd=3)
            .encode(
                x=alt.X("Priority:N", sort="-y", title="Priority"),
                y=alt.Y("Tickets:Q", title="Number of tickets"),
                tooltip=["Priority:N", "Tickets:Q"],
            )
            .properties(height=240, padding=CHART_PADDING)
        )

        status_counts = (
            ticket_data["status"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Tickets")
        )
        status_chart = (
            alt.Chart(status_counts)
            .mark_bar(color="#2563eb", cornerRadiusEnd=3)
            .encode(
                y=alt.Y("Status:N", sort="-x", title="Status"),
                x=alt.X("Tickets:Q", title="Number of tickets"),
                tooltip=["Status:N", "Tickets:Q"],
            )
            .properties(height=240, padding=CHART_PADDING)
        )

        ticket_chart_columns = st.columns(2)

        with ticket_chart_columns[0]:
            with st.container(border=True):
                st.subheader("Tickets by priority")
                st.caption("Shows how IT-support workload is distributed by urgency.")
                st.altair_chart(style_chart(priority_chart), width="stretch")

        with ticket_chart_columns[1]:
            with st.container(border=True):
                st.subheader("Tickets by status")
                st.caption("Shows workflow state across the migrated ticket records.")
                st.altair_chart(style_chart(status_chart), width="stretch")

        st.subheader("IT ticket preview")
        st.caption("A small preview of the SQLite ticket table used by SmartBoyAI.")
        ticket_preview_columns = [
            "ticket_id",
            "priority",
            "status",
            "assigned_to",
            "resolution_time_hours",
        ]
        ui.themed_dataframe(ticket_data[ticket_preview_columns].head(10), height=280)

with metadata_tab:
    try:
        metadata_data = load_dataset_metadata()
    except Exception as error:
        metadata_data = pd.DataFrame()
        st.info(
            "Dataset metadata is not available yet. Use the CLI migration option "
            "to migrate DATA/datasets_metadata.csv into SQLite."
        )
        st.caption(f"Technical detail: {type(error).__name__}")

    if not metadata_data.empty:
        metadata_metric_columns = st.columns(4)
        total_rows = metadata_data["rows"].dropna().sum()
        average_columns = metadata_data["columns"].dropna().mean()
        largest_dataset = (
            metadata_data.sort_values("rows", ascending=False)["name"].iloc[0]
            if "name" in metadata_data.columns and not metadata_data.empty
            else "N/A"
        )

        with metadata_metric_columns[0]:
            ui.metric_card(
                "Datasets",
                len(metadata_data),
                note="Rows in datasets_metadata",
                accent="cyan",
            )

        with metadata_metric_columns[1]:
            ui.metric_card(
                "Combined rows",
                f"{int(total_rows):,}" if not pd.isna(total_rows) else "N/A",
                note="Sum of metadata row counts",
                accent="green",
            )

        with metadata_metric_columns[2]:
            ui.metric_card(
                "Avg columns",
                (
                    f"{average_columns:.1f}"
                    if not pd.isna(average_columns)
                    else "N/A"
                ),
                note="Mean dataset width",
                accent="blue",
            )

        with metadata_metric_columns[3]:
            ui.metric_card(
                "Largest dataset",
                largest_dataset,
                note="By row count",
                accent="amber",
            )

        row_chart_data = metadata_data.sort_values("rows", ascending=False)
        row_chart = (
            alt.Chart(row_chart_data)
            .mark_bar(color="#0891b2", cornerRadiusEnd=3)
            .encode(
                y=alt.Y("name:N", sort="-x", title="Dataset"),
                x=alt.X("rows:Q", title="Rows"),
                tooltip=[
                    alt.Tooltip("name:N", title="Dataset"),
                    alt.Tooltip("rows:Q", title="Rows", format=","),
                    alt.Tooltip("columns:Q", title="Columns"),
                ],
            )
            .properties(height=260, padding=CHART_PADDING)
        )

        with st.container(border=True):
            st.subheader("Dataset size comparison")
            st.caption(
                "Compares the datasets listed in the migrated metadata table."
            )
            st.altair_chart(style_chart(row_chart), width="stretch")

        st.subheader("Dataset metadata table")
        st.caption("Shows the migrated metadata records used for data-context questions.")
        ui.themed_dataframe(metadata_data, height=280)


ui.section_heading(
    "External Threat Intelligence - CISA KEV",
    "Official real-world exploited-vulnerability data from CISA.",
)
st.caption("Source: CISA Known Exploited Vulnerabilities Catalog.")

try:
    cisa_data = load_cisa_kev_data()
except Exception as error:
    cisa_data = pd.DataFrame()
    st.info(
        "CISA KEV data is not available yet. Use the CLI migration option to "
        "migrate DATA/external/known_exploited_vulnerabilities.csv into SQLite."
    )
    st.caption(f"Technical detail: {type(error).__name__}")

if not cisa_data.empty:
    cisa_filter_columns = st.columns(5)

    with cisa_filter_columns[0]:
        vendor_options = sorted(
            cisa_data["vendorProject"].replace("", pd.NA).dropna().unique().tolist()
        )
        selected_vendor = st.selectbox(
            "CISA vendor",
            ["All"] + vendor_options,
            key="cisa_vendor_filter",
        )

    with cisa_filter_columns[1]:
        ransomware_options = sorted(
            cisa_data["knownRansomwareCampaignUse"]
            .replace("", "Unknown")
            .fillna("Unknown")
            .unique()
            .tolist()
        )
        selected_ransomware = st.selectbox(
            "Ransomware usage",
            ["All"] + ransomware_options,
            key="cisa_ransomware_filter",
        )

    with cisa_filter_columns[2]:
        year_options = sorted(
            int(year) for year in cisa_data["yearAdded"].dropna().unique().tolist()
        )
        selected_year = st.selectbox(
            "Year added",
            ["All"] + year_options,
            key="cisa_year_filter",
        )

    with cisa_filter_columns[3]:
        cwe_options = get_top_cwes(cisa_data, limit=50)["CWE"].tolist()
        selected_cwe = st.selectbox(
            "CWE category",
            ["All"] + cwe_options,
            key="cisa_cwe_filter",
        )

    with cisa_filter_columns[4]:
        cisa_search = st.text_input(
            "Search CVE, vendor, or product",
            key="cisa_search_filter",
            placeholder="Example: CVE-2024 or Microsoft",
        ).strip()

    filtered_cisa = cisa_data.copy()

    if selected_vendor != "All":
        filtered_cisa = filtered_cisa[
            filtered_cisa["vendorProject"].astype(str) == selected_vendor
        ]

    if selected_ransomware != "All":
        filtered_cisa = filtered_cisa[
            filtered_cisa["knownRansomwareCampaignUse"]
            .replace("", "Unknown")
            .fillna("Unknown")
            .astype(str)
            == selected_ransomware
        ]

    if selected_year != "All":
        filtered_cisa = filtered_cisa[filtered_cisa["yearAdded"] == selected_year]

    if selected_cwe != "All":
        filtered_cisa = filtered_cisa[
            filtered_cisa["cwes"].fillna("").astype(str).str.contains(
                selected_cwe,
                na=False,
                regex=False,
            )
        ]

    if cisa_search:
        search_text = cisa_search.lower()
        searchable_text = (
            filtered_cisa["cveID"].fillna("")
            + " "
            + filtered_cisa["vendorProject"].fillna("")
            + " "
            + filtered_cisa["product"].fillna("")
            + " "
            + filtered_cisa["vulnerabilityName"].fillna("")
        ).str.lower()
        filtered_cisa = filtered_cisa[
            searchable_text.str.contains(search_text, na=False, regex=False)
        ]

    if filtered_cisa.empty:
        st.warning("No CISA KEV records match the selected filters.")
    else:
        cisa_metric_columns = st.columns(4)
        cisa_dates = filtered_cisa["dateAddedParsed"].dropna()
        latest_cisa_date = cisa_dates.max() if not cisa_dates.empty else pd.NaT
        latest_30_days = (
            int((cisa_dates >= latest_cisa_date - pd.Timedelta(days=30)).sum())
            if not pd.isna(latest_cisa_date)
            else 0
        )
        ransomware_known = int(
            filtered_cisa["knownRansomwareCampaignUse"]
            .fillna("")
            .str.lower()
            .eq("known")
            .sum()
        )

        with cisa_metric_columns[0]:
            ui.metric_card(
                "Known exploited vulnerabilities",
                len(filtered_cisa),
                note="Filtered CISA KEV rows",
                accent="red",
            )

        with cisa_metric_columns[1]:
            ui.metric_card(
                "Vendors represented",
                filtered_cisa["vendorProject"].replace("", pd.NA).nunique(),
                note="Unique vendor/project values",
                accent="blue",
            )

        with cisa_metric_columns[2]:
            ui.metric_card(
                "Known ransomware links",
                ransomware_known,
                note="Rows marked Known",
                accent="amber",
            )

        with cisa_metric_columns[3]:
            ui.metric_card(
                "Latest 30-day additions",
                latest_30_days,
                note="Based on latest date added",
                accent="green",
            )

        top_vendors = (
            filtered_cisa["vendorProject"]
            .replace("", "Unknown")
            .fillna("Unknown")
            .value_counts()
            .head(10)
            .rename_axis("Vendor")
            .reset_index(name="Vulnerabilities")
        )
        vendor_chart = (
            alt.Chart(top_vendors)
            .mark_bar(color="#dc2626", cornerRadiusEnd=3)
            .encode(
                y=alt.Y("Vendor:N", sort="-x", title="Vendor/project"),
                x=alt.X("Vulnerabilities:Q", title="CISA KEV count"),
                tooltip=["Vendor:N", "Vulnerabilities:Q"],
            )
            .properties(height=CHART_HEIGHT, padding=CHART_PADDING)
        )

        monthly_data = filtered_cisa.dropna(subset=["dateAddedParsed"]).copy()
        monthly_chart = None

        if not monthly_data.empty:
            monthly_data["Month"] = (
                monthly_data["dateAddedParsed"].dt.to_period("M").dt.to_timestamp()
            )
            monthly_counts = (
                monthly_data.groupby("Month").size().reset_index(name="Vulnerabilities")
            )
            monthly_chart = (
                alt.Chart(monthly_counts)
                .mark_line(point=True, color="#2563eb", strokeWidth=2)
                .encode(
                    x=alt.X("Month:T", title="Month added"),
                    y=alt.Y("Vulnerabilities:Q", title="Vulnerabilities added"),
                    tooltip=[
                        alt.Tooltip("Month:T", title="Month", format="%b %Y"),
                        alt.Tooltip("Vulnerabilities:Q", title="Added"),
                    ],
                )
                .properties(height=CHART_HEIGHT, padding=CHART_PADDING)
            )

        ransomware_counts = (
            filtered_cisa["knownRansomwareCampaignUse"]
            .replace("", "Unknown")
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Ransomware usage")
            .reset_index(name="Vulnerabilities")
        )
        ransomware_chart = (
            alt.Chart(ransomware_counts)
            .mark_bar(color="#d97706", cornerRadiusEnd=3)
            .encode(
                y=alt.Y("Ransomware usage:N", sort="-x", title="Ransomware usage"),
                x=alt.X("Vulnerabilities:Q", title="CISA KEV count"),
                tooltip=["Ransomware usage:N", "Vulnerabilities:Q"],
            )
            .properties(height=CHART_HEIGHT, padding=CHART_PADDING)
        )

        cwe_counts = get_top_cwes(filtered_cisa)
        cwe_chart = None

        if not cwe_counts.empty:
            cwe_chart = (
                alt.Chart(cwe_counts)
                .mark_bar(color="#0891b2", cornerRadiusEnd=3)
                .encode(
                    y=alt.Y("CWE:N", sort="-x", title="CWE category"),
                    x=alt.X("Vulnerabilities:Q", title="CISA KEV count"),
                    tooltip=["CWE:N", "Vulnerabilities:Q"],
                )
                .properties(height=CHART_HEIGHT, padding=CHART_PADDING)
            )

        cisa_charts = [
            (
                "Top 10 vendors by known exploited vulnerabilities",
                "Ranks vendors/projects by count in the filtered CISA KEV data.",
                vendor_chart,
            ),
            (
                "Vulnerabilities added over time",
                "Groups CISA KEV additions by month.",
                monthly_chart,
            ),
            (
                "Known ransomware campaign usage",
                "Compares whether vulnerabilities are linked to known ransomware use.",
                ransomware_chart,
            ),
            (
                "Top CWE categories",
                "Shows common weakness categories where CWE values are available.",
                cwe_chart,
            ),
        ]

        for row_start in range(0, len(cisa_charts), 2):
            chart_pair = cisa_charts[row_start : row_start + 2]
            chart_columns = st.columns(len(chart_pair))

            for chart_column, (title, caption, chart) in zip(chart_columns, chart_pair):
                with chart_column:
                    with st.container(border=True):
                        st.subheader(title)
                        st.caption(caption)

                        if chart is None:
                            st.info("Not enough usable data is available for this chart.")
                        else:
                            st.altair_chart(style_chart(chart), width="stretch")

        ui.section_heading(
            "CISA KEV records",
            "Paginated external threat-intelligence rows from the filtered CISA data.",
        )
        cisa_table = filtered_cisa[CISA_TABLE_COLUMNS].rename(
            columns={
                "cveID": "CVE ID",
                "vendorProject": "Vendor",
                "product": "Product",
                "vulnerabilityName": "Vulnerability",
                "dateAdded": "Date added",
                "dueDate": "Due date",
                "knownRansomwareCampaignUse": "Ransomware usage",
                "cwes": "CWE",
            }
        )
        paginate_dataframe(cisa_table, "cisa_kev", default_page_size=20)

        selected_cve = st.selectbox(
            "View full CISA record",
            [None] + filtered_cisa["cveID"].dropna().astype(str).tolist(),
            format_func=lambda value: "Select a CVE" if value is None else value,
        )

        if selected_cve is not None:
            selected_record = filtered_cisa[
                filtered_cisa["cveID"].astype(str) == selected_cve
            ].iloc[0]

            with st.expander(f"{selected_cve} details", expanded=True):
                st.markdown(
                    f"**Vendor/Product:** {selected_record['vendorProject']} - "
                    f"{selected_record['product']}"
                )
                st.markdown(f"**Vulnerability:** {selected_record['vulnerabilityName']}")
                st.markdown(f"**Description:** {selected_record['shortDescription']}")
                st.markdown(f"**Required action:** {selected_record['requiredAction']}")
                st.markdown(f"**Notes:** {selected_record['notes'] or 'No notes provided.'}")

ui.section_heading("Operational insight")
ui.section_card(
    "💡 What this view highlights",
    "The sorted charts reveal common classifications and workflow states, while "
    "the heatmap shows where severity and category overlap. The time trend helps "
    "operators identify changes in reporting activity.",
    accent="amber",
)
