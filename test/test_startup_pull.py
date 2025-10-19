import os
import tempfile
import shutil
import unittest
import json
from pathlib import Path

# Canary test to confirm pytest/unittest is collecting this file
def test__collection_smoke():
    assert True

class TestStartupConfigPull(unittest.TestCase):
    """
    This is a Test unit used in testing ability to 
    pull settings from a configuration file at startup

    """
    def setUp(self):

        """
        This is a setup function that does the following at
        the start of this pytest run:
        - Generates a temporary test directory
        - Generates
            - JSON test data to test pulling from the system
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

        # --- helper: resolve UserConfig import safely ---
    def _import_user_config(self):
        """
        Try to import UserConfig from typical locations.
        If not found, skip the test suite gracefully.
        """
        try:
            # Preferred: src/config.py
            from src.config import UserConfig
            return UserConfig
        except Exception:
            pass
        try:
            # Fallback: config.py alongside tests
            from config import UserConfig
            return UserConfig
        except Exception:
            pass

        self.skipTest("UserConfig not implemented yet or import path not found. "
                      "Create src/config.py (or config.py) with class UserConfig.")

    def test_uses_defaults_when_no_config_file(self):
        """If no config file is found, defaults should be returned (deep-copied)."""
        UserConfig = self._import_user_config()

        defaults = {
            "language": "en",
            "region": "CA",
            "preferences": {"theme": "light"}
        }
        cfg = UserConfig(defaults=defaults)

        # Point to a file that does not exist in the temp dir
        missing_path = str(Path(self.temp_dir) / "no_such_config.json")
        result = cfg.load(missing_path)

        # Uses defaults
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["region"], "CA")
        self.assertEqual(result["preferences"]["theme"], "light")

        # Must be a deep copy (mutating result should not mutate defaults)
        result["preferences"]["theme"] = "dark"
        self.assertEqual(defaults["preferences"]["theme"], "light")

    def test_loads_from_valid_json_when_present(self):
        """If a valid JSON config is present, data should be loaded from that file."""
        UserConfig = self._import_user_config()

        defaults = {
            "language": "en",
            "region": "CA",
            "preferences": {"theme": "light"}
        }
        cfg = UserConfig(defaults=defaults)

        result = cfg.load(str(self.good_json))

        # Expect exactly the contents of self.good_json (no merge required)
        expected = json.loads(self.good_json.read_text(encoding="utf-8"))
        self.assertEqual(result, expected)

        # And ensure it didn't just return the defaults when a good file exists
        self.assertNotEqual(result, defaults)

    def test_invalid_json_falls_back_to_defaults(self):
        """If the JSON is invalid, implementation should fall back to defaults."""
        UserConfig = self._import_user_config()

        defaults = {
            "language": "en",
            "region": "CA",
            "preferences": {"theme": "light"}
        }
        cfg = UserConfig(defaults=defaults)

        result = cfg.load(str(self.bad_json))

        # Falls back to defaults
        self.assertEqual(result, defaults)

        # Deep copy check again (no shared nested structures)
        result["preferences"]["theme"] = "dark"
        self.assertEqual(defaults["preferences"]["theme"], "light")


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


