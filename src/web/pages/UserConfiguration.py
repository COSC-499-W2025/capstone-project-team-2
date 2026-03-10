"""User Configuration page for consent and profile preferences.

This page is intentionally private-only because it mutates persisted settings.
It coordinates two backend concerns:
- privacy consent (`/privacy-consent`)
- user config preferences (`/config/update`)
"""

import sys
from html import escape
from pathlib import Path

import streamlit as st


# Add project root to path so we can import src.web modules.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.web.mode import render_page_header, require_private_mode
from src.web.user_configuration_helpers import (
    current_external_consent,
    current_name,
    current_theme,
    fetch_config,
    save_user_configuration,
)

# UI option labels mapped to backend-friendly values in helper layer.
_THEME_OPTIONS = ["No change", "light", "dark"]
_CONSENT_OPTIONS = ["Allow", "Do not allow"]

# This page modifies persisted config, so it should not appear in Public mode.
require_private_mode("User Configuration")

render_page_header(
    "User Configuration",
    "Set consent for external tools and manage profile preferences.",
)
st.markdown(
    """
    <div class="page-hero">
        <h3>Configuration Workspace</h3>
        <p>Manage external-tool consent and profile preferences used by resume/portfolio workflows.</p>
        <div class="page-chip-row">
            <span class="page-chip">Consent</span>
            <span class="page-chip">Profile</span>
            <span class="page-chip">Theme Preference</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

config = fetch_config(on_error=st.error)
if not config:
    # Stop cleanly if config cannot be loaded (error already shown).
    st.stop()

current_consent = current_external_consent(config)
current_name_value = current_name(config) or "Not set"
current_theme_value = current_theme(config)

with st.container(border=True):
    st.markdown("<p class='section-title'>Current Settings</p>", unsafe_allow_html=True)
    r1_label, r1_value, _ = st.columns([1.6, 1.8, 3.6], gap="small")
    with r1_label:
        st.markdown("**External Tools**")
    with r1_value:
        st.markdown(f"<span class='page-chip'>{escape(current_consent)}</span>", unsafe_allow_html=True)

    r2_label, r2_value, _ = st.columns([1.6, 1.8, 3.6], gap="small")
    with r2_label:
        st.markdown("**Name**")
    with r2_value:
        st.markdown(f"<span class='page-chip'>{escape(current_name_value)}</span>", unsafe_allow_html=True)

    r3_label, r3_value, _ = st.columns([1.6, 1.8, 3.6], gap="small")
    with r3_label:
        st.markdown("**Theme**")
    with r3_value:
        st.markdown(f"<span class='page-chip'>{escape(current_theme_value)}</span>", unsafe_allow_html=True)

if current_consent == "Allow":
    default_consent_index = 0
else:
    default_consent_index = 1

if "_user_external_choice" not in st.session_state:
    st.session_state["_user_external_choice"] = _CONSENT_OPTIONS[default_consent_index]

# One form submit updates consent + profile settings together so state
# remains consistent and avoids partial updates.
with st.container(border=True):
    st.markdown("<p class='section-title'>Update Configuration</p>", unsafe_allow_html=True)
    header_col, chip_col = st.columns([5, 2], gap="small")
    with header_col:
        st.markdown("**External Tools Consent**")
    with chip_col:
        st.markdown(
            f"<div class='chip-align-right'><span class='page-chip'>Active: {st.session_state['_user_external_choice']}</span></div>",
            unsafe_allow_html=True,
        )
    consent_col1, consent_col2, _ = st.columns([1.1, 1.25, 3.65], gap="small")
    with consent_col1:
        if st.button(
            "Allow",
            key="_consent_allow_btn",
            type="primary" if st.session_state["_user_external_choice"] == "Allow" else "secondary",
            use_container_width=True,
        ):
            st.session_state["_user_external_choice"] = "Allow"
            st.rerun()
    with consent_col2:
        if st.button(
            "Do not allow",
            key="_consent_deny_btn",
            type="primary" if st.session_state["_user_external_choice"] == "Do not allow" else "secondary",
            use_container_width=True,
        ):
            st.session_state["_user_external_choice"] = "Do not allow"
            st.rerun()
    st.caption("If you allow external tools, data consent is enabled automatically.")

    st.divider()
    with st.form("user_config_form", clear_on_submit=False):
        st.markdown("<p class='section-title'>Profile</p>", unsafe_allow_html=True)
        st.caption("Update your profile fields and save them as the active configuration.")
        input_col, _ = st.columns([2.25, 2.75], gap="large")
        with input_col:
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

        save_col, _ = st.columns([1.2, 3.8], gap="small")
        with save_col:
            submitted = st.form_submit_button(
                "Save Configuration",
                type="primary",
                icon=":material/save:",
                use_container_width=True,
            )

if submitted:
    # Save helper handles payload construction + API call.
    if save_user_configuration(
        config,
        st.session_state["_user_external_choice"],
        full_name,
        selected_theme,
        on_error=st.error,
    ):
        st.success("Configuration saved.")
        st.rerun()
