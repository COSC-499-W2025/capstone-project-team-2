import unittest
from unittest.mock import patch,MagicMock,call
from src.CLI_Interface_for_user_config import ConfigurationForUsersUI

import time

class TestConfigurationCLI(unittest.TestCase):
    """

    """

    def setUp(self):
        self.sample_json = {
            "ID": 1,
            "First Name": "Jane",
            "Student id": "2003357",
            "Last Name": "Doe",
            "Email": "Jane.Doe@gmail.com",
            "Role": "Student",
            "Preferences": {
                "theme": "dark"
            }
        }
        self.instance=ConfigurationForUsersUI(self.sample_json)

    @patch('builtins.input', return_value='2')
    def test_select_first_choice(self,mock_input):
        chosen_setting=self.instance.get_setting_choice()
        self.assertEqual(chosen_setting,'First Name')
        mock_input.assert_called_once()



    @patch('builtins.input', return_value='1')
    def test_invalid_pick(self,mock_input):
        with self.assertRaises(Exception) as context:
            chosen_setting=self.instance.get_setting_choice()
            self.instance.validate_modifiable_field(chosen_setting)

        self.assertIn("ID cannot be modified",str(context.exception))
        mock_input.assert_called_once()





