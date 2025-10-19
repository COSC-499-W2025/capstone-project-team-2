import os
import tempfile
import shutil
import unittest
import json
from pathlib import Path
from src.Configuration import configuration_for_users


class TestUserConfigStore(unittest.TestCase):

    """
    This is Test unit used in testing in terms of
    user configurations

    """
    def setUp(self):

        """
        This is a setup function that does the following
        at the start of this pytest run:
        - Creates a temporary directory and changes the
        working directory to that the temporary directory
        - Generates
            - JSON test data to save to the system
            - Valid Json file
            - Not Valid JSON file


        """

        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.json_test_data = {
            "id": 1,
            "FirstName": "Jane",
            "Student_id": "2003357",
            "last Name": "Doe",
            "Email": "Jane.Doe@gmail.com",
            "Role": "Student",
            "preferences": {
                "theme": "dark"
            }
        }
        self.bad_json = Path(os.path.join(self.temp_dir, "bad.json"))
        self.bad_json.write_text('{"id": 1, "name": "Jane",}', encoding="utf-8")  # trailing comma = invalid

        self.good_json = Path(os.path.join(self.temp_dir, "Good.json"))
        self.good_json.write_text("""
        {"id":1,
            "FirstName": "Jane",
            "Student_id": "2003357"
            }
        
        """, encoding="utf-8")
        os.chdir(self.temp_dir)
        self.instance=configuration_for_users()

    def test_save_config(self):


        """
        This is a test to check to see
        if the created json file is saved
        successfully

        This test verifies the following:
        - That the sample json is saved successfully
        to the temp directory

        :return: pass or fail
        """

        self.instance.save_config(self.json_test_data)



        self.assertTrue(os.path.exists("UserConfigs.json"))

    def test_invalid_valid_json(self):

        """
        This test check to see if the stored
        Json is not valid.

        - This test verifies the following:
          - That the sample json is a valid one

        :return: pass or fail
        """

        bad_json_text = self.bad_json.read_text(encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(bad_json_text)

    def test_valid_json(self):

        """
         This test check to see if the stored
        Json is not valid.

        - This test verifies the following:
          - That the sample json is a valid one
        :return: pass or fail
        """


        try:
            with open(self.good_json, "r", encoding='utf-8') as f:
                data = json.load(f)

        except json.JSONDecodeError as e:
            self.fail(f"JSON file failed to load: {e}")

        self.assertEqual(data['id'],1)
        self.assertEqual(data['FirstName'],"Jane")

    def tearDown(self):
        """
         This function cleans up after the test is complete.

        Does the following:
        -Returns to the original working directory.
        -Removes the temporary folder and its associated
        content.
        """

        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

