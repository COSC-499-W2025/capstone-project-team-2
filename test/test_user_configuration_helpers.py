"""Unit tests for src.web.user_configuration_helpers."""

import unittest
from unittest.mock import MagicMock, patch

import requests

from src.web.user_configuration_helpers import (
    current_external_consent,
    current_name,
    current_theme,
    fetch_config,
    save_user_configuration,
)


class _Resp:
    """Small response stub for requests mocking in tests."""

    def __init__(self, ok: bool, payload=None, text: str = ""):
        self.ok = ok
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


class TestUserConfigurationHelpers(unittest.TestCase):
    """Validate helper logic used by the User Configuration page."""

    def test_current_name_combines_parts(self):
        """Return a combined first/last name with whitespace trimmed."""
        self.assertEqual(
            current_name({"First Name": " Jane ", "Last Name": " Doe "}),
            "Jane Doe",
        )

    def test_current_theme_handles_missing_preferences(self):
        """Return Not set when Preferences is missing or invalid."""
        self.assertEqual(current_theme({}), "Not set")
        self.assertEqual(current_theme({"Preferences": "dark"}), "Not set")

    def test_current_external_consent_mapping(self):
        """Map boolean consent values to display labels."""
        self.assertEqual(current_external_consent({"consented": {"external": True}}), "Allow")
        self.assertEqual(current_external_consent({"consented": {"external": False}}), "Do not allow")
        self.assertEqual(current_external_consent({}), "Not set")

    @patch("src.web.user_configuration_helpers.requests.get")
    def test_fetch_config_success(self, mock_get):
        """Return config dict for a successful /config/get response."""
        mock_get.return_value = _Resp(ok=True, payload={"First Name": "Jane"})
        self.assertEqual(fetch_config(), {"First Name": "Jane"})

    @patch("src.web.user_configuration_helpers.requests.get")
    def test_fetch_config_connection_error(self, mock_get):
        """Return empty dict and send callback message when API is unreachable."""
        mock_get.side_effect = requests.ConnectionError
        on_error = MagicMock()

        self.assertEqual(fetch_config(on_error=on_error), {})
        on_error.assert_called_once_with("Cannot reach API server.")

    @patch("src.web.user_configuration_helpers.requests.get")
    def test_fetch_config_non_ok_response(self, mock_get):
        """Return empty dict and report API detail when /config/get fails."""
        mock_get.return_value = _Resp(ok=False, payload={"detail": "Config unavailable"})
        on_error = MagicMock()

        self.assertEqual(fetch_config(on_error=on_error), {})
        on_error.assert_called_once_with("Config unavailable")

    @patch("src.web.user_configuration_helpers.requests.post")
    def test_save_user_configuration_success(self, mock_post):
        """Persist consent and optional name/theme updates with two API calls."""
        mock_post.side_effect = [_Resp(ok=True, payload={}), _Resp(ok=True, payload={})]

        base = {"ID": 1, "Preferences": {"theme": "dark"}}
        ok = save_user_configuration(
            base_config=base,
            external_choice="Allow",
            full_name="Jane Doe",
            selected_theme="light",
            on_error=MagicMock(),
        )

        self.assertTrue(ok)
        self.assertEqual(mock_post.call_count, 2)

        first_call = mock_post.call_args_list[0]
        self.assertTrue(first_call.args[0].endswith("/privacy-consent"))
        self.assertEqual(
            first_call.kwargs["json"],
            {"data_consent": True, "external_consent": True},
        )

        second_call = mock_post.call_args_list[1]
        self.assertTrue(second_call.args[0].endswith("/config/update"))
        payload = second_call.kwargs["json"]
        self.assertEqual(payload["First Name"], "Jane")
        self.assertEqual(payload["Last Name"], "Doe")
        self.assertEqual(payload["Preferences"]["theme"], "light")
        self.assertEqual(payload["consented"]["external"], True)
        self.assertEqual(payload["consented"]["Data consent"], True)

    @patch("src.web.user_configuration_helpers.requests.post")
    def test_save_user_configuration_consent_failure(self, mock_post):
        """Stop and report error when /privacy-consent fails."""
        mock_post.return_value = _Resp(ok=False, payload={"detail": "Consent failed"})
        on_error = MagicMock()

        ok = save_user_configuration(
            base_config={"ID": 1},
            external_choice="Allow",
            full_name="Jane Doe",
            selected_theme="No change",
            on_error=on_error,
        )

        self.assertFalse(ok)
        self.assertEqual(mock_post.call_count, 1)
        on_error.assert_called_once_with("Consent failed")

    @patch("src.web.user_configuration_helpers.requests.post")
    def test_save_user_configuration_update_failure(self, mock_post):
        """Report failure when config update call fails after consent passes."""
        mock_post.side_effect = [
            _Resp(ok=True, payload={}),
            _Resp(ok=False, payload={"detail": "Update failed"}),
        ]
        on_error = MagicMock()

        ok = save_user_configuration(
            base_config={"ID": 1},
            external_choice="Do not allow",
            full_name="",
            selected_theme="No change",
            on_error=on_error,
        )

        self.assertFalse(ok)
        self.assertEqual(mock_post.call_count, 2)
        on_error.assert_called_once_with("Update failed")

        second_call = mock_post.call_args_list[1]
        payload = second_call.kwargs["json"]
        self.assertEqual(payload["consented"]["external"], False)
        self.assertEqual(payload["consented"]["Data consent"], True)


if __name__ == "__main__":
    unittest.main()
