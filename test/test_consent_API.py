"""Unit tests for the privacy consent FastAPI endpoint."""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.API.general_API import app
from src.core.app_context import runtimeAppContext

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

if __name__ == "__main__":
    unittest.main()
