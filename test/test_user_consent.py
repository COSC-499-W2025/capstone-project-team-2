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

    def test_default_consent_is_false(self):
        """Test that consent is False by default"""
        self.assertFalse(self.consent_manager.has_consent)

    def test_check_consent_returns_current_state(self):
        """Test that check_consent returns the current consent state"""
        self.assertFalse(self.consent_manager.check_consent())
        self.consent_manager.has_consent = True
        self.assertTrue(self.consent_manager.check_consent())

    def test_revoke_consent(self):
        """Test that revoking consent sets it to False"""
        self.consent_manager.has_consent = True
        self.consent_manager.revoke_consent()
        self.assertFalse(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['y'])
    def test_consent_yes(self, mock_input):
        """Test that answering 'y' grants consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        self.assertTrue(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['yes'])
    def test_consent_full_yes(self, mock_input):
        """Test that answering 'yes' grants consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        self.assertTrue(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['n', 'y'])
    def test_consent_no_confirmed(self, mock_input):
        """Test that answering 'n' and confirming exit denies consent"""
        self.assertFalse(self.consent_manager.ask_for_consent())
        self.assertFalse(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['no', 'yes'])
    def test_consent_full_no_confirmed(self, mock_input):
        """Test that answering 'no' and confirming exit denies consent"""
        self.assertFalse(self.consent_manager.ask_for_consent())
        self.assertFalse(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['n', 'n', 'y'])
    def test_consent_no_then_changed_mind(self, mock_input):
        """Test that answering 'n', not confirming exit, then 'y' grants consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        self.assertTrue(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['invalid', 'y'])
    def test_invalid_input_then_yes(self, mock_input):
        """Test that invalid input followed by 'y' eventually grants consent"""
        self.assertTrue(self.consent_manager.ask_for_consent())
        self.assertTrue(self.consent_manager.has_consent)

    @patch('builtins.input', side_effect=['n', 'invalid', 'y', 'y'])
    def test_invalid_confirmation_input(self, mock_input):
        """Test handling invalid input during exit confirmation"""
        self.assertFalse(self.consent_manager.ask_for_consent())
        self.assertFalse(self.consent_manager.has_consent)


if __name__ == "__main__":
    unittest.main()