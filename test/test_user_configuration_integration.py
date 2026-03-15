"""Integration tests for the user-configuration frontend flow via real API routes."""
import pytest
import unittest
from pathlib import Path

import orjson
from fastapi.testclient import TestClient

from src.API.general_API import app
import src.core.app_context as _app_context_module

@pytest.fixture(autouse=True)
def reset_consent():
    original_external = _app_context_module.runtimeAppContext.external_consent
    original_data = _app_context_module.runtimeAppContext.data_consent
    _app_context_module.runtimeAppContext.external_consent = False
    _app_context_module.runtimeAppContext.data_consent = False
    yield
    _app_context_module.runtimeAppContext.external_consent = original_external
    _app_context_module.runtimeAppContext.data_consent = original_data

class TestUserConfigurationIntegration(unittest.TestCase):
    """Validate end-to-end config flow used by the Streamlit User Configuration page."""

    def setUp(self) -> None:
        """Create test client, snapshot runtime consent, and seed a deterministic config."""
        self.client = TestClient(app)
        self.original_external = _app_context_module.runtimeAppContext.external_consent
        self.original_data = _app_context_module.runtimeAppContext.data_consent
        project_root = Path(__file__).resolve().parents[1]
        self.config_path = project_root / "User_config_files" / "UserConfigs.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_bytes = self.config_path.read_bytes() if self.config_path.exists() else None

        self.seed_config = {
            "ID": 1,
            "First Name": "Jane",
            "Last Name": "Doe",
            "Preferences": {"theme": "dark"},
            "consented": {"external": False, "Data consent": False},
        }
        self.client.post("/config/update", json=self.seed_config)

    def tearDown(self) -> None:
        """Restore runtime consent values and original config file content."""
        _app_context_module.runtimeAppContext.external_consent = False
        _app_context_module.runtimeAppContext.data_consent = False

        if self.backup_bytes is None:
            if self.config_path.exists():
                self.config_path.unlink()
        else:
            self.config_path.write_bytes(self.backup_bytes)

    def test_full_user_configuration_flow_updates_name_theme_and_consent(self) -> None:
        """Apply consent + optional profile updates, then verify persisted config values."""
        baseline = self.client.get("/config/get")
        self.assertEqual(baseline.status_code, 200)
        current = baseline.json()

        consent_resp = self.client.post(
            "/privacy-consent",
            json={"data_consent": True, "external_consent": True},
        )
        self.assertEqual(consent_resp.status_code, 200)

        updated = dict(current)
        updated["First Name"] = "Alex"
        updated["Last Name"] = "Morgan"
        prefs = updated.get("Preferences")
        if not isinstance(prefs, dict):
            prefs = {}
        prefs["theme"] = "light"
        updated["Preferences"] = prefs
        updated["consented"] = {"external": True, "Data consent": True}

        save_resp = self.client.post("/config/update", json=updated)
        self.assertEqual(save_resp.status_code, 200)

        final_resp = self.client.get("/config/get")
        self.assertEqual(final_resp.status_code, 200)
        final_cfg = final_resp.json()

        self.assertEqual(final_cfg["First Name"], "Alex")
        self.assertEqual(final_cfg["Last Name"], "Morgan")
        self.assertEqual(final_cfg["Preferences"]["theme"], "light")
        self.assertTrue(final_cfg["consented"]["external"])
        self.assertTrue(final_cfg["consented"]["Data consent"])
        self.assertTrue(_app_context_module.runtimeAppContext.external_consent)
        self.assertTrue(_app_context_module.runtimeAppContext.data_consent)

    def test_consent_only_flow_preserves_existing_profile_fields(self) -> None:
        """Update required consent only and ensure name/theme remain unchanged."""
        consent_resp = self.client.post(
            "/privacy-consent",
            json={"data_consent": True, "external_consent": False},
        )
        self.assertEqual(consent_resp.status_code, 200)

        final_resp = self.client.get("/config/get")
        self.assertEqual(final_resp.status_code, 200)
        final_cfg = final_resp.json()

        self.assertEqual(final_cfg["First Name"], "Jane")
        self.assertEqual(final_cfg["Last Name"], "Doe")
        self.assertEqual(final_cfg["Preferences"]["theme"], "dark")
        self.assertFalse(final_cfg["consented"]["external"])
        self.assertTrue(final_cfg["consented"]["Data consent"])
        self.assertFalse(_app_context_module.runtimeAppContext.external_consent)
        self.assertTrue(_app_context_module.runtimeAppContext.data_consent)

    def test_invalid_external_without_data_is_rejected(self) -> None:
        """Reject invalid consent request where external consent is true but data consent is false."""
        resp = self.client.post(
            "/privacy-consent",
            json={"data_consent": False, "external_consent": True},
        )
        self.assertEqual(resp.status_code, 400)

        get_resp = self.client.get("/config/get")
        self.assertEqual(get_resp.status_code, 200)
        cfg = get_resp.json()

        self.assertEqual(cfg["First Name"], "Jane")
        self.assertEqual(cfg["Last Name"], "Doe")
        self.assertEqual(cfg["Preferences"]["theme"], "dark")

    def test_config_file_written_as_valid_json(self) -> None:
        """Confirm /config/update writes valid JSON to UserConfigs.json on disk."""
        payload = {
            "ID": 99,
            "First Name": "Taylor",
            "Last Name": "Jordan",
            "Preferences": {"theme": "light"},
            "consented": {"external": False, "Data consent": True},
        }
        resp = self.client.post("/config/update", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.config_path.exists())

        disk_data = orjson.loads(self.config_path.read_bytes())
        self.assertEqual(disk_data, payload)


if __name__ == "__main__":
    unittest.main()
