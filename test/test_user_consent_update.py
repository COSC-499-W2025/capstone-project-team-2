import unittest
from unittest.mock import patch, MagicMock, call
import os
from pathlib import Path


from src.Configuration import configuration_for_users
import orjson
import tempfile
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
        self.temp_dir= tempfile.mkdtemp()
        self.test_file_path=Path(self.temp_dir).joinpath("test.json")
        self.instance.loc_to_save=self.test_file_path

    def _load_save_config(self):
        """
        Helper method to load the save_config file.
        :param file_path:
        :return:
        """
        path=self.test_file_path
        with open(path,"rb") as f:
            return orjson.loads(f.read())



    def test_consent_both_true(self):
        """Test when both consent flags are True"""
        self.instance.save_with_consent(True,True)
        self.instance.save_config()

        updated_data=self._load_save_config()

        self.assertIn('consented', updated_data)
        self.assertEqual(updated_data['consented']['external'], True)
        self.assertEqual(updated_data['consented']['Data consent'], True)
        self.assertEqual(updated_data['First Name'], 'Jane')


    def test_consent_both_false(self):
        """Test when both consent flags are False"""
        self.instance.save_with_consent(False,False)
        self.instance.save_config()
        updated_data=self._load_save_config()


        self.assertIn('consented', updated_data)
        self.assertEqual(updated_data['consented']['external'], False)
        self.assertEqual(updated_data['consented']['Data consent'], False)

    def test_mixed_external_true(self):
        """Test external=True, data_consent=False"""
        self.instance.save_with_consent(True,False)
        self.instance.save_config()
        updated_data=self._load_save_config()

        self.assertIn('consented', updated_data)
        self.assertEqual(updated_data['consented']['external'], True)
        self.assertEqual(updated_data['consented']['Data consent'], False)

    def test_mixed_data_true(self):
        """
        Test external=False, data_consent=True

        """
        self.instance.save_with_consent(False,True)
        self.instance.save_config()

        updated_data=self._load_save_config()
        self.assertIn('consented', updated_data)
        self.assertEqual(updated_data['consented']['external'], False)
        self.assertEqual(updated_data['consented']['Data consent'], True)



    def original_data_preserved(self):
        """
        Verify all original data is preserved after consent update
        """
        self.instance.save_with_consent(True,True)
        self.instance.save_config()
        updated_data=self._load_save_config()
        self.assertEqual(updated_data['ID'], 1)
        self.assertEqual(updated_data['First Name'], 'Jane')
        self.assertEqual(updated_data['Last Name'], 'Doe')
        self.assertEqual(updated_data['Student id'], '2003357')
        self.assertEqual(updated_data['Email'], 'Jane.Doe@gmail.com')
        self.assertEqual(updated_data['Role'], 'Student')
        self.assertIn('Preferences', updated_data)
        self.assertEqual(updated_data['Preferences']['theme'], 'dark')




    def tearDown(self):
        if self.test_file_path.exists():
            os.remove(self.test_file_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)








