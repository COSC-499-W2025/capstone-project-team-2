import unittest
from unittest.mock import patch, MagicMock, call
import os
from pathlib import Path
from src.Configuration import configuration_for_users
from src.user_startup_config import ConfigLoader
import orjson
from pathlib import Path


class testUserConstentUpdate(unittest.TestCase):

    def setUp(self):


        self.sample_json= {
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
        self.instance = configuration_for_users(self.sample_json)


    def test_successUpdate(self):
        self.instance.save_with_consent(True,True)
        test_file_path = Path(self.instance.loc_to_save).with_name("Test.json")
        self.instance.loc_to_save = test_file_path
        self.instance.save_config()



        with open(test_file_path, "rb") as f:
            updated_data=orjson.loads(f.read())

        self.assertIn('consented', updated_data)
        self.assertEqual(updated_data['consented']['external'], True)
        self.assertEqual(updated_data['consented']['Data consent'], True)
        self.assertEqual(updated_data['First Name'], 'Jane')

    def tearDown(self):
        if os.path.exists(self.instance.loc_to_save):
            os.remove(self.instance.loc_to_save)








