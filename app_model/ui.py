"""Reusable Streamlit presentation helpers for the Gatekeeper interface."""

from base64 import b64encode
from html import escape
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent

IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
}


THEME_CSS = """
<style>
    :root {
        --gk-bg: #05080f;
        --gk-surface: #0b1220;
        --gk-surface-raised: #101a2a;
        --gk-border: #1e3a4f;
        --gk-border-soft: #172638;
        --gk-text: #f4f7fb;
        --gk-muted: #94a3b8;
        --gk-cyan: #22d3ee;
        --gk-blue: #60a5fa;
        --gk-green: #34d399;
        --gk-amber: #fbbf24;
        --gk-red: #fb7185;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: var(--gk-bg);
        color: var(--gk-text);
    }

    [data-testid="stHeader"] {
        background: rgba(5, 8, 15, 0.92);
        border-bottom: 1px solid var(--gk-border-soft);
    }

    [data-testid="stSidebar"] {
        background: #080f1b;
        border-right: 1px solid var(--gk-border);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label {
        color: var(--gk-muted);
    }

    .block-container {
        max-width: 1380px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] strong {
        color: var(--gk-text);
        letter-spacing: 0;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"],
    label {
        color: var(--gk-muted);
        letter-spacing: 0;
    }

    a {
        color: var(--gk-cyan) !important;
    }

    .gk-page-header {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr) auto;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1.75rem;
        padding: 0.8rem 0 1.35rem;
        border-bottom: 1px solid var(--gk-border);
    }

    .gk-brand-mark {
        display: grid;
        place-items: center;
        width: 52px;
        height: 52px;
        border: 1px solid var(--gk-cyan);
        border-radius: 6px;
        background: #071827;
        color: var(--gk-cyan);
        font-size: 1.35rem;
        font-weight: 800;
        box-shadow: 0 0 20px rgba(34, 211, 238, 0.12);
    }

    .gk-brand-image {
        display: block;
        width: 34px;
        height: 34px;
        max-width: 100%;
        max-height: 100%;
        border-radius: 4px;
        object-fit: contain;
    }

    .gk-eyebrow {
        margin: 0 0 0.25rem !important;
        color: var(--gk-cyan) !important;
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.12rem !important;
        text-transform: uppercase !important;
    }

    .gk-page-title {
        margin: 0 !important;
        color: var(--gk-text) !important;
        font-size: 2.15rem !important;
        line-height: 1.1 !important;
        letter-spacing: 0 !important;
    }

    .gk-page-subtitle {
        margin: 0.4rem 0 0 !important;
        color: var(--gk-muted) !important;
        font-size: 0.98rem !important;
    }

    .gk-system-state {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        width: fit-content;
        padding: 0.35rem 0.65rem;
        border: 1px solid var(--status-border);
        border-radius: 999px;
        background: var(--status-background);
        color: var(--status-colour);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.05rem;
        white-space: nowrap;
    }

    .gk-system-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--status-colour);
        box-shadow: 0 0 9px var(--status-colour);
    }

    .gk-section-heading {
        margin: 2rem 0 0.8rem;
        padding-left: 0.75rem;
        border-left: 3px solid var(--gk-cyan);
    }

    .gk-section-heading h2 {
        margin: 0;
        font-size: 1.15rem;
        letter-spacing: 0;
    }

    .gk-section-heading p {
        margin: 0.3rem 0 0 !important;
        color: var(--gk-muted) !important;
        font-size: 0.88rem !important;
    }

    .gk-metric-card {
        min-height: 132px;
        padding: 1rem 1.05rem;
        border: 1px solid var(--gk-border);
        border-left: 3px solid var(--accent);
        border-radius: 6px;
        background: var(--gk-surface);
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
    }

    .gk-metric-label {
        margin: 0 !important;
        color: var(--gk-muted) !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.06rem !important;
        text-transform: uppercase !important;
    }

    .gk-metric-value {
        margin: 0.45rem 0 0.3rem !important;
        color: var(--gk-text) !important;
        font-size: 2rem !important;
        font-weight: 750 !important;
        line-height: 1 !important;
        letter-spacing: 0 !important;
    }

    .gk-metric-note {
        margin: 0 !important;
        color: var(--gk-muted) !important;
        font-size: 0.8rem !important;
    }

    .gk-section-card,
    .gk-status-card {
        padding: 1rem 1.1rem;
        border: 1px solid var(--gk-border);
        border-radius: 6px;
        background: var(--gk-surface);
    }

    .gk-section-card {
        border-top: 2px solid var(--accent);
    }

    .gk-section-card h3,
    .gk-status-card h3 {
        margin: 0 0 0.45rem;
        font-size: 1rem;
    }

    .gk-section-card p,
    .gk-status-card p {
        margin: 0 !important;
        color: var(--gk-muted) !important;
        font-size: 0.88rem !important;
        line-height: 1.6 !important;
    }

    .gk-status-card {
        display: grid;
        grid-template-columns: 9px minmax(0, 1fr);
        gap: 0.85rem;
        align-items: start;
    }

    .gk-status-marker {
        width: 9px;
        height: 9px;
        margin-top: 0.35rem;
        border-radius: 50%;
        background: var(--accent);
        box-shadow: 0 0 10px color-mix(in srgb, var(--accent), transparent 45%);
    }

    .gk-sidebar-user {
        margin: 0.35rem 0 1rem;
        padding: 0.85rem;
        border: 1px solid var(--gk-border);
        border-radius: 6px;
        background: var(--gk-surface);
    }

    .gk-sidebar-user small {
        display: block;
        margin-bottom: 0.25rem;
        color: var(--gk-cyan);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08rem;
        text-transform: uppercase;
    }

    .gk-sidebar-user strong {
        color: var(--gk-text);
        font-size: 0.95rem;
    }

    [data-testid="stForm"],
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--gk-border) !important;
        border-radius: 6px !important;
        background: var(--gk-surface) !important;
        box-shadow: 0 16px 34px rgba(0, 0, 0, 0.14);
    }

    div[data-baseweb="input"] {
        border: 1px solid var(--gk-border) !important;
        border-radius: 5px !important;
        background: #07101c !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: var(--gk-cyan) !important;
        box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.12) !important;
    }

    div[data-baseweb="input"] input {
        color: var(--gk-text) !important;
        caret-color: var(--gk-cyan) !important;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        min-height: 2.6rem;
        border: 1px solid #24627a;
        border-radius: 5px;
        background: #0c2433;
        color: var(--gk-text);
        font-weight: 700;
        transition: border-color 120ms ease, background-color 120ms ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: var(--gk-cyan);
        background: #103047;
        color: white;
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {
        border-color: var(--gk-cyan);
        background: #0e7490;
        color: white;
    }

    button[data-baseweb="tab"] {
        border-radius: 0;
        color: var(--gk-muted);
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: var(--gk-cyan);
    }

    [data-baseweb="tab-highlight"] {
        background-color: var(--gk-cyan) !important;
    }

    div[data-baseweb="select"] > div {
        border-color: var(--gk-border) !important;
        background: #07101c !important;
        color: var(--gk-text) !important;
    }

    [data-testid="stAlert"] {
        border: 1px solid var(--gk-border);
        border-radius: 5px;
        background: var(--gk-surface);
        color: var(--gk-text);
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid var(--gk-border);
        border-radius: 6px;
        overflow: hidden;
    }

    [data-testid="stChatMessage"] {
        margin-bottom: 0.75rem;
        border: 1px solid var(--gk-border-soft);
        border-radius: 6px;
        background: var(--gk-surface);
    }

    [data-testid="stChatInput"] {
        border: 1px solid var(--gk-border) !important;
        border-radius: 6px !important;
        background: var(--gk-surface) !important;
    }

    hr {
        border-color: var(--gk-border-soft);
    }

    @media (max-width: 700px) {
        .block-container {
            padding-top: 4rem;
        }

        .gk-page-header {
            grid-template-columns: auto minmax(0, 1fr);
            align-items: start;
        }

        .gk-system-state {
            grid-column: 2;
        }

        .gk-page-title {
            font-size: 1.75rem !important;
        }

        .gk-brand-mark {
            width: 46px;
            height: 46px;
        }

        .gk-metric-card {
            min-height: 116px;
        }
    }
</style>
"""


ACCENT_COLOURS = {
    "cyan": "#22d3ee",
    "blue": "#60a5fa",
    "green": "#34d399",
    "amber": "#fbbf24",
    "red": "#fb7185",
}

STATUS_STYLES = {
    "green": ("#34d399", "#185b4c", "#071b18"),
    "amber": ("#fbbf24", "#70551b", "#201805"),
    "red": ("#fb7185", "#713145", "#240a12"),
}


def apply_theme():
    """Apply the shared Gatekeeper CSS theme to the current Streamlit page."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def _accent_colour(accent):
    """Return a known accent colour, falling back to cyan."""
    return ACCENT_COLOURS.get(accent, ACCENT_COLOURS["cyan"])


def _image_data_uri(image_path):
    """Convert a local image into a data URI for use inside custom HTML."""
    if not image_path:
        return ""

    try:
        path = Path(image_path).expanduser()
    except TypeError:
        return ""

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    mime_type = IMAGE_MIME_TYPES.get(path.suffix.lower())

    if mime_type is None or not path.is_file():
        return ""

    try:
        image_bytes = path.read_bytes()
    except OSError:
        return ""

    if not image_bytes:
        return ""

    encoded_image = b64encode(image_bytes).decode("ascii")

    return f"data:{mime_type};base64,{encoded_image}"


def page_header(
    title,
    subtitle,
    status="SYSTEM ONLINE",
    status_accent="green",
    logo_path=None,
    logo_text="G",
    logo_alt="Gatekeeper logo",
):
    """Display a consistent Gatekeeper page heading."""
    status_colours = STATUS_STYLES.get(status_accent, STATUS_STYLES["green"])
    status_colour, status_border, status_background = status_colours

    logo_data_uri = _image_data_uri(logo_path)

    if logo_data_uri:
        logo_html = (
            f'<img class="gk-brand-image" src="{escape(logo_data_uri)}" '
            f'alt="{escape(str(logo_alt))}">'
        )
    else:
        fallback_text = "G" if logo_text in (None, "") else str(logo_text)
        logo_html = f'<span aria-hidden="true">{escape(fallback_text)}</span>'

    st.markdown(
        f"""
        <header class="gk-page-header">
            <div class="gk-brand-mark">{logo_html}</div>
            <div>
                <p class="gk-eyebrow">Gatekeeper / Security Operations</p>
                <h1 class="gk-page-title">{escape(str(title))}</h1>
                <p class="gk-page-subtitle">{escape(str(subtitle))}</p>
            </div>
            <div class="gk-system-state" style="--status-colour: {status_colour};
                        --status-border: {status_border};
                        --status-background: {status_background};">
                <span class="gk-system-dot"></span>
                {escape(str(status))}
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, subtitle=None):
    """Display a compact heading above a page section."""
    subtitle_html = ""

    if subtitle:
        subtitle_html = f"<p>{escape(str(subtitle))}</p>"

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
    note_html = ""

    if note:
        note_html = f'<p class="gk-metric-note">{escape(str(note))}</p>'

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


def status_card(title, body, accent="green"):
    """Display a compact system or safety status message."""
    st.markdown(
        f"""
        <section class="gk-status-card" style="--accent: {_accent_colour(accent)};">
            <span class="gk-status-marker"></span>
            <div>
                <h3>{escape(str(title))}</h3>
                <p>{escape(str(body))}</p>
            </div>
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
