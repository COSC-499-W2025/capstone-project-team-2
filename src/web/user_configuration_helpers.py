"""Helper functions for user-configuration Streamlit page."""

from typing import Callable

import requests

from src.web.streamlit_helpers import API_BASE, api_error

_VALID_THEMES = {"light", "dark"}


def fetch_config(on_error: Callable[[str], None] | None = None) -> dict:
    """Fetch current user configuration from API.

    Args:
        on_error (Callable[[str], None] | None): Optional error callback.

    Returns:
        dict: Loaded configuration data, or empty dict on failure.
    """
    try:
        response = requests.get(f"{API_BASE}/config/get", timeout=10)
    except requests.ConnectionError:
        if on_error:
            on_error("Cannot reach API server.")
        return {}

    if not response.ok:
        if on_error:
            on_error(api_error(response))
        return {}

    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def current_name(config: dict) -> str:
    """Build full name from stored config keys.

    Args:
        config (dict): User configuration payload.

    Returns:
        str: Combined first and last name.
    """
    first = str(config.get("First Name", "")).strip()
    last = str(config.get("Last Name", "")).strip()
    return " ".join(part for part in [first, last] if part)


def current_theme(config: dict) -> str:
    """Read theme value from config preferences.

    Args:
        config (dict): User configuration payload.

    Returns:
        str: Theme value or "Not set".
    """
    prefs = config.get("Preferences", {})
    if isinstance(prefs, dict):
        return str(prefs.get("theme", "Not set"))
    return "Not set"


def current_external_consent(config: dict) -> str:
    """Read external-tool consent from config.

    Args:
        config (dict): User configuration payload.

    Returns:
        str: "Allow", "Do not allow", or "Not set".
    """
    consented = config.get("consented", {})
    if isinstance(consented, dict):
        if consented.get("external") is True:
            return "Allow"
        if consented.get("external") is False:
            return "Do not allow"
    return "Not set"


def save_user_configuration(
    base_config: dict,
    external_choice: str,
    full_name: str,
    selected_theme: str,
    on_error: Callable[[str], None] | None = None,
) -> bool:
    """Persist consent and optional settings through existing endpoints.

    Args:
        base_config (dict): Existing configuration to update.
        external_choice (str): Selected external-tools consent option.
        full_name (str): Optional full name input.
        selected_theme (str): Optional selected theme value.
        on_error (Callable[[str], None] | None): Optional error callback.

    Returns:
        bool: True when both API updates succeed, otherwise False.
    """
    external_allowed = external_choice == "Allow"

    consent_response = requests.post(
        f"{API_BASE}/privacy-consent",
        json={"data_consent": True, "external_consent": external_allowed},
        timeout=10,
    )
    if not consent_response.ok:
        if on_error:
            on_error(api_error(consent_response))
        return False

    updated_config = dict(base_config)
    updated_config["consented"] = {
        "external": external_allowed,
        "Data consent": True,
    }

    cleaned_name = full_name.strip()
    if cleaned_name:
        parts = cleaned_name.split()
        updated_config["First Name"] = parts[0]
        updated_config["Last Name"] = " ".join(parts[1:]) if len(parts) > 1 else ""

    if selected_theme in _VALID_THEMES:
        preferences = updated_config.get("Preferences")
        if not isinstance(preferences, dict):
            preferences = {}
        preferences["theme"] = selected_theme
        updated_config["Preferences"] = preferences

    config_response = requests.post(
        f"{API_BASE}/config/update",
        json=updated_config,
        timeout=10,
    )
    if not config_response.ok:
        if on_error:
            on_error(api_error(config_response))
        return False

    return True
