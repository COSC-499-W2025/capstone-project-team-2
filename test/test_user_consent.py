import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))
from src.user_consent import UserConsent

class TestUserConsent(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.consent_manager = UserConsent()

    def test_default_consents_are_false(self):
        """Test that both consents are False by default"""
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertFalse(data_consent)
        self.assertFalse(external_consent)

    def test_check_consent_returns_both_states(self):
        """Test that check_consent returns both consent states"""
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertFalse(data_consent)
        self.assertFalse(external_consent)

        self.consent_manager.has_data_consent = True
        self.consent_manager.has_external_consent = True
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertTrue(data_consent)
        self.assertTrue(external_consent)

    def test_revoke_consent(self):
        """Test that revoking consent sets both to False by default"""
        self.consent_manager.has_data_consent = True
        self.consent_manager.has_external_consent = True
        self.consent_manager.revoke_consent()
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertFalse(data_consent)
        self.assertFalse(external_consent)

    def test_revoke_data_consent_only(self):
        """Test revoking only data consent"""
        self.consent_manager.has_data_consent = True
        self.consent_manager.has_external_consent = True
        self.consent_manager.revoke_consent(include_external=False)
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertFalse(data_consent)
        self.assertTrue(external_consent)

    @patch('builtins.input', side_effect=['y', 'y'])
    def test_full_consent_flow(self, mock_input):
        """Test granting both data and external services consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertTrue(data_consent)
        self.assertTrue(external_consent)

    @patch('builtins.input', side_effect=['y', 'n', 'y'])
    def test_data_only_consent_flow(self, mock_input):
        """Test granting data consent but declining external with basic continue"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertTrue(data_consent)
        self.assertFalse(external_consent)

    @patch('builtins.input', side_effect=['y', 'n', 'n'])
    def test_decline_basic_analysis(self, mock_input):
        """Test declining to continue with basic analysis"""
        self.assertFalse(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertFalse(data_consent)
        self.assertFalse(external_consent)

    @patch('builtins.input', side_effect=['n', 'y'])
    def test_initial_data_consent_denied(self, mock_input):
        """Test denying initial data consent"""
        self.assertFalse(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertFalse(data_consent)
        self.assertFalse(external_consent)

    @patch('builtins.input', side_effect=['invalid', 'y', 'y'])
    def test_invalid_data_consent_input(self, mock_input):
        """Test invalid input for data consent followed by full consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertTrue(data_consent)
        self.assertTrue(external_consent)

    @patch('builtins.input', side_effect=['y', 'invalid', 'y'])
    def test_invalid_external_consent_input(self, mock_input):
        """Test invalid input for external consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertTrue(data_consent)
        self.assertTrue(external_consent)

    @patch('builtins.input', side_effect=['y', 'n', 'invalid', 'y'])
    def test_invalid_basic_analysis_input(self, mock_input):
        """Test invalid input when asking about basic analysis"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        data_consent, external_consent = self.consent_manager.check_consent()
        self.assertTrue(data_consent)
        self.assertFalse(external_consent)


if __name__ == "__main__":
    unittest.main()