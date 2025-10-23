import unittest
from unittest.mock import patch, MagicMock, call
from src.CLI_Interface_for_user_config import ConfigurationForUsersUI

import os
import sys
import shutil


class TestConfigurationCLI(unittest.TestCase):
    """
    This is a helper class to help test the functionality
    of the Configuration CLI where the use of mock_input are being used
    to simulate user input
    """

    def setUp(self):
        """
        Here we are creating a sample json configuration to be used in the test,
        and also we are also creating an instances to refer to our created class
        """
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
        self.instance = ConfigurationForUsersUI(self.sample_json)


    @patch('builtins.input', return_value='2')
    def test_select_first_choice(self, mock_input):
        """
        This a test validates that the function returns right object in the sample json
        to be modified are correctly returned and using mocking to simulate a user input which in this
        case is selecting which attribute ti modify based on a number
        """
        chosen_setting = self.instance.get_setting_choice()
        self.assertEqual(chosen_setting, 'First Name')
        mock_input.assert_called_once()

    @patch('builtins.input', return_value='1')
    def test_invalid_pick_ID(self, mock_input):
        """
        Here we are testing to see when the ID key is selected that the system successfully
        returns an error message telling the user that you cannot modify the ID option
        """
        with self.assertRaises(Exception) as context:
            chosen_setting = self.instance.get_setting_choice()
            self.instance.validate_modifiable_field(chosen_setting)

        self.assertIn("ID cannot be modified", str(context.exception))
        mock_input.assert_called_once()

    import sys

    @patch('builtins.input', side_effect=["2", "fdfd", "n"])
    @patch('builtins.print')
    def test_invalid_pick(self, mock_print, mock_input):
        chosen_setting = self.instance.get_setting_choice()
        self.instance.validate_modifiable_field(chosen_setting)
        result = self.instance.modify_settings(chosen_setting)

        mock_print.assert_any_call("ERROR: Please choose(y/n)")
        self.assertFalse(result)
    


    @patch('builtins.input', side_effect=['2', 'y', "Immanuel"])
    def test_save_updated_json(self, mock_input):
        """
        This test validates that the change has been successfully been made to the dictionary and saved to the system
        """
        chosen_setting = self.instance.get_setting_choice()
        self.instance.validate_modifiable_field(chosen_setting)
        self.instance.modify_settings(chosen_setting)
        self.assertTrue(os.path.exists("UserConfigs.json"))

        self.assertEqual(mock_input.call_count, 3)

    def tearDown(self):
        """
        After the test are completed this function cleans up the function  file, which in this case
        the single json file.
        """
        if os.path.exists("UserConfigs.json"):
            os.remove("UserConfigs.json")



