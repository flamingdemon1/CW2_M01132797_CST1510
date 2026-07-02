"""Reusable Streamlit presentation helpers for the Gatekeeper interface."""

from html import escape
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GATEKEEPER_LOGO = PROJECT_ROOT / "assets" / "logos" / "gatekeeper_logo.png"

ACCENT_COLOURS = {
    "cyan": "#0891b2",
    "blue": "#2563eb",
    "green": "#059669",
    "amber": "#d97706",
    "red": "#e11d48",
}

STATUS_STYLES = {
    "green": ("#059669", "#10b981"),
    "amber": ("#d97706", "#f59e0b"),
    "red": ("#e11d48", "#fb7185"),
}

THEMES = {
    "dark": {
        "bg": "#05080f",
        "surface": "#0b1220",
        "surface_raised": "#101a2a",
        "input": "#07101c",
        "sidebar": "#080f1b",
        "border": "#1e3a4f",
        "border_soft": "#172638",
        "text": "#f4f7fb",
        "muted": "#a8b4c6",
        "button": "#0c2433",
        "button_hover": "#103047",
        "shadow": "rgba(0, 0, 0, 0.18)",
        "chart_text": "#e5edf7",
        "chart_grid": "#26364a",
    },
    "light": {
        "bg": "#f3f7fb",
        "surface": "#ffffff",
        "surface_raised": "#eef5fa",
        "input": "#ffffff",
        "sidebar": "#eaf2f8",
        "border": "#b8cbd9",
        "border_soft": "#d7e3ec",
        "text": "#102235",
        "muted": "#526579",
        "button": "#e2f2f7",
        "button_hover": "#cdeaf2",
        "shadow": "rgba(20, 52, 74, 0.10)",
        "chart_text": "#23384d",
        "chart_grid": "#d6e1e9",
    },
}


def get_theme():
    """Return the currently selected Gatekeeper theme name."""
    if "theme" not in st.session_state:
        old_toggle_value = st.session_state.get("theme_toggle", False)
        st.session_state["theme"] = "light" if old_toggle_value else "dark"

    return st.session_state["theme"]


def get_chart_colours():
    """Return colours that keep Altair charts readable in either theme."""
    palette = THEMES[get_theme()]
    return {
        "text": palette["chart_text"],
        "grid": palette["chart_grid"],
        "background": palette["surface"],
    }


def apply_theme():
    """Apply presentation-only CSS for the selected Gatekeeper theme."""
    palette = THEMES[get_theme()]

    # This CSS changes presentation only. Authentication, database, email and
    # AI behaviour remain in Python and use normal Streamlit widgets.
    css = f"""
    <style>
        :root {{
            color-scheme: {get_theme()};
            --gk-bg: {palette['bg']};
            --gk-surface: {palette['surface']};
            --gk-surface-raised: {palette['surface_raised']};
            --gk-input: {palette['input']};
            --gk-sidebar: {palette['sidebar']};
            --gk-border: {palette['border']};
            --gk-border-soft: {palette['border_soft']};
            --gk-text: {palette['text']};
            --gk-muted: {palette['muted']};
            --gk-button: {palette['button']};
            --gk-button-hover: {palette['button_hover']};
            --gk-shadow: {palette['shadow']};
            --gk-cyan: #0891b2;
        }}

        html, body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            background: var(--gk-bg);
            color: var(--gk-text);
        }}

        /* Streamlit keeps this fixed container for the sidebar control. Match
           it to the page so it forms an invisible safety strip over scrolled
           content while keeping the native sidebar button clickable. */
        [data-testid="stHeader"] {{
            height: 3.5rem !important;
            background: var(--gk-bg) !important;
            border: 0 !important;
            box-shadow: none !important;
            z-index: 1000 !important;
        }}

        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stSidebar"] {{
            background: var(--gk-sidebar);
            border-right: 1px solid var(--gk-border);
        }}

        [data-testid="stSidebarContent"] {{
            background: var(--gk-sidebar);
        }}

        /* Presentation-only spacing after Streamlit's official hideTopBar.
           This does not affect navigation or application logic. */
        .block-container {{
            max-width: 1380px;
            padding-top: 4.25rem;
            padding-bottom: 3rem;
        }}

        .st-key-content_profile_control {{
            position: fixed;
            top: 0.55rem;
            right: 1.25rem;
            z-index: 1002 !important;
            width: 210px;
            margin: 0;
            pointer-events: auto !important;
        }}

        .st-key-content_profile_control [data-testid="stVerticalBlock"] {{
            gap: 0;
        }}

        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stSidebar"] span,
        label {{
            color: var(--gk-text);
            letter-spacing: 0;
        }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stSidebar"] p {{
            color: var(--gk-muted);
        }}

        a {{ color: var(--gk-cyan) !important; }}

        .gk-page-header {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: end;
            gap: 1rem;
            margin: 1.25rem 0 1.5rem;
            padding-bottom: 1.1rem;
            border-bottom: 1px solid var(--gk-border);
        }}

        .gk-eyebrow {{
            margin: 0 0 0.25rem !important;
            color: var(--gk-cyan) !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.1rem !important;
            text-transform: uppercase;
        }}

        .gk-page-title {{
            margin: 0 !important;
            color: var(--gk-text) !important;
            font-size: 2rem !important;
            line-height: 1.15 !important;
        }}

        .gk-page-subtitle {{
            margin: 0.35rem 0 0 !important;
            color: var(--gk-muted) !important;
        }}

        .gk-system-state {{
            padding: 0.35rem 0.65rem;
            border: 1px solid var(--status-border);
            border-radius: 999px;
            color: var(--status-colour);
            font-size: 0.72rem;
            font-weight: 700;
            white-space: nowrap;
        }}

        .gk-section-heading {{
            margin: 2rem 0 0.8rem;
            padding-left: 0.75rem;
            border-left: 3px solid var(--gk-cyan);
        }}

        .gk-section-heading h2 {{ margin: 0; font-size: 1.15rem; }}
        .gk-section-heading p {{
            margin: 0.3rem 0 0 !important;
            color: var(--gk-muted) !important;
            font-size: 0.88rem !important;
        }}

        .gk-metric-card,
        .gk-section-card,
        .gk-status-card {{
            border: 1px solid var(--gk-border);
            border-radius: 6px;
            background: var(--gk-surface);
            box-shadow: 0 10px 24px var(--gk-shadow);
        }}

        .gk-metric-card {{
            min-height: 126px;
            padding: 1rem 1.05rem;
            border-left: 3px solid var(--accent);
        }}

        .gk-metric-label {{
            margin: 0 !important;
            color: var(--gk-muted) !important;
            font-size: 0.75rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
        }}

        .gk-metric-value {{
            margin: 0.45rem 0 0.3rem !important;
            color: var(--gk-text) !important;
            font-size: 2rem !important;
            font-weight: 750 !important;
            line-height: 1 !important;
        }}

        .gk-metric-note {{
            margin: 0 !important;
            color: var(--gk-muted) !important;
            font-size: 0.8rem !important;
        }}

        .gk-section-card {{
            min-height: 142px;
            padding: 1rem 1.1rem 1.15rem;
            border-top: 2px solid var(--accent);
        }}

        .gk-command-card {{
            min-height: 190px;
        }}

        .gk-status-card {{
            padding: 1rem 1.1rem;
            border-left: 3px solid var(--accent);
        }}

        .gk-section-card h3, .gk-status-card h3 {{
            margin: 0 0 0.55rem;
            font-size: 1rem;
        }}

        .gk-section-card p, .gk-status-card p {{
            margin: 0 !important;
            color: var(--gk-muted) !important;
            font-size: 0.88rem !important;
            line-height: 1.65 !important;
        }}

        .gk-sidebar-user {{
            margin: 0.35rem 0 1rem;
            padding: 0.85rem;
            border: 1px solid var(--gk-border);
            border-radius: 6px;
            background: var(--gk-surface);
        }}

        .gk-sidebar-user small {{
            display: block;
            color: var(--gk-cyan);
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        [data-testid="stForm"],
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stPopoverBody"],
        [data-baseweb="popover"],
        [data-baseweb="popover"] > div,
        div[role="dialog"] {{
            border-color: var(--gk-border) !important;
            background-color: var(--gk-surface) !important;
            color: var(--gk-text) !important;
        }}

        [data-baseweb="popover"] *,
        div[role="dialog"] * {{
            color: var(--gk-text);
        }}

        div[data-baseweb="input"],
        div[data-baseweb="base-input"],
        div[data-baseweb="textarea"],
        div[data-baseweb="select"] > div {{
            border-color: var(--gk-border) !important;
            background: var(--gk-input) !important;
            color: var(--gk-text) !important;
        }}

        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea,
        input, textarea {{
            color: var(--gk-text) !important;
            caret-color: var(--gk-cyan) !important;
            background-color: var(--gk-input) !important;
        }}

        .stButton > button,
        .stFormSubmitButton > button,
        [data-testid="stPopover"] > button {{
            min-height: 2.55rem;
            border: 1px solid var(--gk-border);
            border-radius: 5px;
            background: var(--gk-button);
            color: var(--gk-text);
            font-weight: 700;
        }}

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        [data-testid="stPopover"] > button:hover {{
            border-color: var(--gk-cyan);
            background: var(--gk-button-hover);
            color: var(--gk-text);
        }}

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {{
            border-color: #0891b2;
            background: #087f9b;
            color: white;
        }}

        [data-testid="stAlert"] {{
            border: 1px solid var(--gk-border);
            background: var(--gk-surface);
            color: var(--gk-text);
        }}

        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            border: 1px solid var(--gk-border);
            border-radius: 6px;
            background: var(--gk-surface) !important;
            overflow: hidden;
        }}

        [data-testid="stDataFrame"] > div,
        [data-testid="stDataFrame"] canvas,
        [data-testid="stTable"] > div {{
            background-color: var(--gk-surface) !important;
            color: var(--gk-text) !important;
        }}

        [data-testid="stChatMessage"] {{
            margin-bottom: 0.9rem;
            padding: 0.8rem 1.45rem 0.95rem 0.9rem;
            border: 1px solid var(--gk-border-soft);
            border-radius: 6px;
            background: var(--gk-surface);
        }}

        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
            padding: 0.1rem 0.8rem 0.1rem 0.15rem;
            line-height: 1.7;
        }}

        [data-testid="stChatInput"] {{
            border-color: var(--gk-border) !important;
            background: var(--gk-surface) !important;
        }}

        .gk-route-space {{ height: 1.5rem; }}

        hr {{ border-color: var(--gk-border-soft); }}

        @media (max-width: 700px) {{
            .block-container {{ padding-top: 4.25rem; }}
            .st-key-content_profile_control {{
                top: 0.45rem;
                right: 0.65rem;
                width: 175px;
            }}
            .gk-page-header {{ grid-template-columns: 1fr; }}
            .gk-system-state {{ width: fit-content; }}
            .gk-page-title {{ font-size: 1.65rem !important; }}
            .gk-section-card {{ min-height: auto; }}
            .gk-command-card {{ min-height: auto; }}
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def logout():
    """Clear the shared authenticated session."""
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""


def sidebar_logo(logo_path=None):
    """Place the current page logo in Streamlit's standard sidebar area."""
    selected_logo = Path(logo_path) if logo_path else GATEKEEPER_LOGO

    if not selected_logo.is_absolute():
        selected_logo = PROJECT_ROOT / selected_logo

    if not selected_logo.is_file():
        selected_logo = GATEKEEPER_LOGO

    if not selected_logo.is_file():
        return

    try:
        st.logo(
            str(selected_logo),
            size="large",
            icon_image=str(selected_logo),
        )
    except Exception:
        # Older Streamlit versions can still show the same local logo safely.
        st.sidebar.image(str(selected_logo), width=180)


def route_spacing():
    """Add consistent presentation spacing below protected-route messages."""
    st.markdown('<div class="gk-route-space"></div>', unsafe_allow_html=True)


def content_profile_control():
    """Show a compact authenticated profile menu above the page heading."""
    if not st.session_state.get("logged_in", False):
        return

    username = st.session_state.get("username", "User")

    with st.container(key="content_profile_control"):
        with st.popover(
            username,
            icon=":material/account_circle:",
            width="stretch",
        ):
            st.caption("🟢 Secure session")
            st.markdown(f"**Signed in as {escape(str(username))}**")
            st.page_link(
                "pages/3_Profile.py",
                label="Profile",
                icon=":material/account_circle:",
            )
            st.page_link(
                "pages/1_dashboard.py",
                label="Dashboard",
                icon=":material/dashboard:",
            )
            st.page_link(
                "pages/2_SmartBoyAI.py",
                label="SmartBoyAI",
                icon=":material/smart_toy:",
            )

            if st.button(
                "Log out",
                icon=":material/logout:",
                width="stretch",
                key="content_profile_logout",
            ):
                logout()
                st.switch_page("home.py")


def style_dataframe(data):
    """Return a pandas Styler that follows the selected interface theme."""
    palette = THEMES[get_theme()]
    return data.style.set_properties(
        **{
            "background-color": palette["surface"],
            "color": palette["text"],
            "border-color": palette["border_soft"],
        }
    )


def _accent_colour(accent):
    """Return a known accent colour, falling back to cyan."""
    return ACCENT_COLOURS.get(accent, ACCENT_COLOURS["cyan"])


def page_header(
    title,
    subtitle,
    status="SYSTEM ONLINE",
    status_accent="green",
    logo_path=None,
    logo_text="G",
    logo_alt="Gatekeeper logo",
):
    """Display a consistent page heading beneath the shared top bar."""
    del logo_path, logo_text, logo_alt  # Logos now belong in the shared top bar.
    dark_colour, light_colour = STATUS_STYLES.get(
        status_accent,
        STATUS_STYLES["green"],
    )

    st.markdown(
        f"""
        <header class="gk-page-header">
            <div>
                <p class="gk-eyebrow">Gatekeeper / Security Operations</p>
                <h1 class="gk-page-title">{escape(str(title))}</h1>
                <p class="gk-page-subtitle">{escape(str(subtitle))}</p>
            </div>
            <div class="gk-system-state"
                 style="--status-colour: {dark_colour};
                        --status-border: {light_colour};">
                {escape(str(status))}
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, subtitle=None):
    """Display a compact heading above a page section."""
    subtitle_html = f"<p>{escape(str(subtitle))}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="gk-section-heading">
            <h2>{escape(str(title))}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title, value, note=None, accent="cyan"):
    """Display a dashboard metric using the shared card style."""
    note_html = (
        f'<p class="gk-metric-note">{escape(str(note))}</p>' if note else ""
    )
    st.markdown(
        f"""
        <div class="gk-metric-card" style="--accent: {_accent_colour(accent)};">
            <p class="gk-metric-label">{escape(str(title))}</p>
            <p class="gk-metric-value">{escape(str(value))}</p>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_card(title, body, accent="cyan"):
    """Display a short explanatory section in a consistent panel."""
    st.markdown(
        f"""
        <section class="gk-section-card" style="--accent: {_accent_colour(accent)};">
            <h3>{escape(str(title))}</h3>
            <p>{escape(str(body))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def command_card(title, body, accent="cyan"):
    """Display an equal-height Home command card."""
    st.markdown(
        f"""
        <section class="gk-section-card gk-command-card"
                 style="--accent: {_accent_colour(accent)};">
            <h3>{escape(str(title))}</h3>
            <p>{escape(str(body))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def status_card(title, body, accent="green"):
    """Display a compact system or safety status message."""
    st.markdown(
        f"""
        <section class="gk-status-card" style="--accent: {_accent_colour(accent)};">
            <h3>{escape(str(title))}</h3>
            <p>{escape(str(body))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def sidebar_user(username):
    """Show the active username in the shared sidebar style."""
    st.sidebar.markdown(
        f"""
        <div class="gk-sidebar-user">
            <small>Secure session</small>
            <strong>{escape(str(username))}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
