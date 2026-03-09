import sys
from pathlib import Path

import streamlit as st

# Add project root to path so we can import src.web modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.web.user_configuration_helpers import (
    current_external_consent,
    current_name,
    current_theme,
    fetch_config,
    save_user_configuration,
)

_THEME_OPTIONS = ["No change", "light", "dark"]
_CONSENT_OPTIONS = ["Allow", "Do not allow"]

st.title("User Configuration")
st.caption("Set consent for external tools (required) and optional profile preferences.")

config = fetch_config(on_error=st.error)
if not config:
    st.stop()

current_consent = current_external_consent(config)
current_name_value = current_name(config) or "Not set"
current_theme_value = current_theme(config)

st.info(
    f"Current settings: External tools: {current_consent} | "
    f"Name: {current_name_value} | Theme: {current_theme_value}"
)

if current_consent == "Allow":
    default_consent_index = 0
else:
    default_consent_index = 1

with st.form("user_config_form", clear_on_submit=False):
    st.markdown("**External Tools Consent (Required)**")
    external_choice = st.radio(
        "Allow external tools/services like Gemini?",
        options=_CONSENT_OPTIONS,
        index=default_consent_index,
        horizontal=True,
    )
    st.caption("If you allow external tools, data consent is enabled automatically.")
    
    st.markdown(
        "<hr style='margin: 0.2rem 0 0.35rem 0; border-color: rgba(128,128,128,0.35);'>",
        unsafe_allow_html=True,
    )

    st.markdown("**Profile (Optional)**")
    full_name = st.text_input(
        "Name",
        value="" if current_name_value == "Not set" else current_name_value,
        placeholder="e.g., Jane Doe",
    )
    selected_theme = st.selectbox(
        "Streamlit Theme",
        options=_THEME_OPTIONS,
        index=0,
    )

    _, save_col = st.columns([3, 1.5])
    with save_col:
        submitted = st.form_submit_button(
            "Save Configuration",
            type="primary",
            icon=":material/save:",
            use_container_width=True,
        )

if submitted:
    if save_user_configuration(
        config,
        external_choice,
        full_name,
        selected_theme,
        on_error=st.error,
    ):
        st.success("Configuration saved.")
        st.rerun()
