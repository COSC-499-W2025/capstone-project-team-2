"""Unit tests for src.web.theme."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import src.web.theme as theme_mod


class TestThemeHelpers(unittest.TestCase):
    """Validate light/dark theme helper behavior."""

    @patch("src.web.theme.ConfigLoader")
    def test_get_saved_theme_normalizes_case(self, mock_loader):
        """Return normalized lowercase theme from config."""
        mock_loader.return_value.load.return_value = {"Preferences": {"theme": "Light"}}
        self.assertEqual(theme_mod.get_saved_theme(), "light")

    @patch("src.web.theme.ConfigLoader")
    def test_get_saved_theme_invalid_value_uses_default(self, mock_loader):
        """Fallback to default when config contains unsupported theme value."""
        mock_loader.return_value.load.return_value = {"Preferences": {"theme": "blue"}}
        self.assertEqual(theme_mod.get_saved_theme(default="dark"), "dark")

    @patch("src.web.theme.ConfigLoader")
    def test_get_saved_theme_loader_error_uses_default(self, mock_loader):
        """Fallback to default when config loading fails."""
        mock_loader.return_value.load.side_effect = RuntimeError("read failed")
        self.assertEqual(theme_mod.get_saved_theme(default="light"), "light")

    @patch("src.web.theme.st.markdown")
    def test_apply_theme_invalid_input_defaults_to_dark(self, mock_markdown):
        """Unknown theme value should apply dark CSS and return 'dark'."""
        applied = theme_mod.apply_theme("invalid-theme")
        self.assertEqual(applied, "dark")
        args, kwargs = mock_markdown.call_args
        self.assertIn("color-scheme: dark", args[0])
        self.assertTrue(kwargs.get("unsafe_allow_html"))

    @patch("src.web.theme.st.markdown")
    def test_apply_theme_light_uses_light_css(self, mock_markdown):
        """Light theme value should apply light CSS and return 'light'."""
        applied = theme_mod.apply_theme("light")
        self.assertEqual(applied, "light")
        args, kwargs = mock_markdown.call_args
        self.assertIn("color-scheme: light", args[0])
        self.assertTrue(kwargs.get("unsafe_allow_html"))

    @patch("src.web.theme.get_saved_theme", return_value="light")
    @patch("src.web.theme.apply_theme", return_value="light")
    def test_apply_theme_from_config_uses_saved_theme_when_session_missing(self, mock_apply, mock_saved):
        """Use saved config theme when session has no ui_theme value."""
        fake_st = SimpleNamespace(session_state={})
        with patch.object(theme_mod, "st", fake_st):
            result = theme_mod.apply_theme_from_config()

        self.assertEqual(result, "light")
        mock_saved.assert_called_once()
        mock_apply.assert_called_once_with("light")
        self.assertEqual(fake_st.session_state["ui_theme"], "light")

    @patch("src.web.theme.get_saved_theme")
    @patch("src.web.theme.apply_theme", return_value="dark")
    def test_apply_theme_from_config_prefers_session_theme(self, mock_apply, mock_saved):
        """Use existing session theme before consulting config."""
        fake_st = SimpleNamespace(session_state={"ui_theme": "dark"})
        with patch.object(theme_mod, "st", fake_st):
            result = theme_mod.apply_theme_from_config()

        self.assertEqual(result, "dark")
        mock_saved.assert_not_called()
        mock_apply.assert_called_once_with("dark")
        self.assertEqual(fake_st.session_state["ui_theme"], "dark")


if __name__ == "__main__":
    unittest.main()
