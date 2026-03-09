"""Theme helpers for applying light/dark mode in Streamlit pages."""

from __future__ import annotations

import streamlit as st

from src.config.user_startup_config import ConfigLoader

_VALID_THEMES = {"light", "dark"}

_DARK_THEME_CSS = """
<style>
:root { color-scheme: dark; }
.stApp,
[data-testid="stAppViewContainer"] {
  background-color: #0e1117;
}
[data-testid="stSidebar"] {
  background-color: #111827;
}
.stApp,
.stApp p,
.stApp span,
.stApp label,
.stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
  color: #f9fafb !important;
}
[data-testid="stSidebar"] * {
  color: #f9fafb !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
  background-color: #1f2937 !important;
  color: #f9fafb !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="input"] textarea {
  color: #f9fafb !important;
  -webkit-text-fill-color: #f9fafb !important;
}
div[data-baseweb="input"] input::placeholder,
div[data-baseweb="input"] textarea::placeholder {
  color: #9ca3af !important;
  -webkit-text-fill-color: #9ca3af !important;
}
code, pre {
  color: #f9fafb !important;
}
</style>
"""

_LIGHT_THEME_CSS = """
<style>
:root { color-scheme: light; }
.stApp,
[data-testid="stAppViewContainer"] {
  background-color: #ffffff;
}
[data-testid="stSidebar"] {
  background-color: #f3f4f6;
}
.stApp,
.stApp p,
.stApp span,
.stApp label,
.stApp li,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"] {
  color: #111827 !important;
}
[data-testid="stSidebar"] * {
  color: #111827 !important;
}
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {
  background-color: #ffffff !important;
  color: #111827 !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="input"] textarea {
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
}
div[data-baseweb="input"] input::placeholder,
div[data-baseweb="input"] textarea::placeholder {
  color: #6b7280 !important;
  -webkit-text-fill-color: #6b7280 !important;
}
button[kind="primary"] {
  color: #ffffff !important;
}
code, pre {
  color: #111827 !important;
}

/* Streamlit segmented_control / BaseWeb button-group */
div[data-baseweb="button-group"] {
  background-color: #e5e7eb !important;
}
div[data-baseweb="button-group"] button {
  background-color: #f9fafb !important;
  color: #111827 !important;
  border-color: #d1d5db !important;
}
div[data-baseweb="button-group"] button:hover {
  background-color: #f3f4f6 !important;
  color: #111827 !important;
}
div[data-baseweb="button-group"] button[aria-checked="true"],
div[data-baseweb="button-group"] button[aria-selected="true"] {
  background-color: #ffffff !important;
  color: #111827 !important;
}
div[data-baseweb="button-group"] button:disabled {
  background-color: #e5e7eb !important;
  color: #6b7280 !important;
  opacity: 1 !important;
}
</style>
"""


def get_saved_theme(default: str = "dark") -> str:
    """Read the saved light/dark preference from user config.

    Args:
        default (str): Fallback theme when config is unavailable/invalid.

    Returns:
        str: "light" or "dark".
    """
    try:
        cfg = ConfigLoader().load()
    except Exception:
        return default

    prefs = cfg.get("Preferences", {}) if isinstance(cfg, dict) else {}
    raw = prefs.get("theme", default) if isinstance(prefs, dict) else default
    candidate = str(raw).strip().lower()
    return candidate if candidate in _VALID_THEMES else default


def apply_theme(theme: str) -> str:
    """Apply light/dark styling to the current Streamlit page.

    Args:
        theme (str): Theme value to apply.

    Returns:
        str: Normalized applied theme.
    """
    normalized = str(theme).strip().lower()
    if normalized not in _VALID_THEMES:
        normalized = "dark"

    st.markdown(_LIGHT_THEME_CSS if normalized == "light" else _DARK_THEME_CSS, unsafe_allow_html=True)
    return normalized


def apply_theme_from_config() -> str:
    """Apply the active theme from session state/config to the page.

    Args:
        None

    Returns:
        str: Applied theme value.
    """
    theme = st.session_state.get("ui_theme") or get_saved_theme()
    theme = apply_theme(theme)
    st.session_state["ui_theme"] = theme
    return theme
