"""Unit tests for the privacy consent FastAPI endpoint."""

from typing import assert_type
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.API.consent_API import update_config_file
from src.API.general_API import app
from src.core.app_context import runtimeAppContext
from pathlib import Path
import os
import orjson

class TestConsentAPI(unittest.TestCase):
    """
    Validate /privacy-consent behavior with mocked config persistence.

    Returns:
        None
    """

    def setUp(self) -> None:
        """
        Create a test client and snapshot runtime consent settings.

        Returns:
            None
        """
        self.client = TestClient(app)
        self.original_external = runtimeAppContext.external_consent
        self.original_data = runtimeAppContext.data_consent

    def tearDown(self) -> None:
        """
        Restore runtime consent settings after each test.

        Returns:
            None
        """
        runtimeAppContext.external_consent = self.original_external
        runtimeAppContext.data_consent = self.original_data

    def test_privacy_consent_updates_config(self) -> None:
        """
        Accept valid consent and persist updates through config helpers.

        Returns:
            None
        """
        sample_config = {"ID": 1, "First Name": "Jane"}
        config_instance = MagicMock()

        with patch("src.API.consent_API.ConfigLoader") as mock_loader, patch(
            "src.API.consent_API.configuration_for_users"
        ) as mock_config_class:
            mock_loader.return_value.load.return_value = sample_config
            mock_config_class.return_value = config_instance

            response = self.client.post(
                "/privacy-consent",
                json={"data_consent": True, "external_consent": False},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"data_consent": True, "external_consent": False},
        )
        mock_config_class.assert_called_once_with(sample_config)
        config_instance.save_with_consent.assert_called_once_with(False, True)
        config_instance.save_config.assert_called_once()
        self.assertFalse(runtimeAppContext.external_consent)
        self.assertTrue(runtimeAppContext.data_consent)

    def test_privacy_consent_rejects_external_without_data(self) -> None:
        """
        Reject invalid consent payloads before touching persistence.

        Returns:
            None
        """
        with patch("src.API.consent_API.ConfigLoader") as mock_loader, patch(
            "src.API.consent_API.configuration_for_users"
        ) as mock_config_class:
            response = self.client.post(
                "/privacy-consent",
                json={"data_consent": False, "external_consent": True},
            )

        self.assertEqual(response.status_code, 400)
        mock_loader.assert_not_called()
        mock_config_class.assert_not_called()

    def test_config_file_created_correctly(self):
        """
        Ensures that updating config correctly creates config file and inputs config data correctly
        """
        project_root = Path(__file__).resolve().parents[1]

        config_dir = project_root / "User_config_files"
        loc_to_save = config_dir / "UserConfigs.json"

        if loc_to_save.exists():
            os.remove(loc_to_save)

        test_dict = {"test": False}

        self.client.post("/config/update", json=test_dict)

        assert loc_to_save.exists()
        with loc_to_save.open("r") as op:
            open_str = op.read()

        assert orjson.loads(open_str) == test_dict

    def test_config_load(self):
        """
        Ensures that config is loaded successfully using API
        """
        response = self.client.get("/config/get")
        assert response.status_code == 200
        assert_type(response.json(), dict)

if __name__ == "__main__":
    unittest.main()
