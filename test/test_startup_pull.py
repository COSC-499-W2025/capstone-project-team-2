import os
import tempfile
import shutil
import unittest
import json
from pathlib import Path


class TestStartupConfigPull(unittest.TestCase):
    """
    This is a test unit used in testing ability to 
    pull settings from a configuration file at startup
    """

    def setUp(self):
        """
        - Creates a temporary directory
        - Writes an invalid JSON file (bad.json)
        - Writes a full configuration json file
        
        """
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # test configuration
        self.json_test_data = {
            "id": 1,
            "FirstName": "Jane",
            "Student_id": "2003357",
            "last Name": "Doe",
            "Email": "Jane.Doe@gmail.com",
            "Role": "Student",
            "preferences": {
                "theme": "dark",
                "language": "en",
                "region": "canada",
                "font size": "14"
            }
        }

        # Writing test configuration to disk
        self.full_json = Path(os.path.join(self.temp_dir, "full_config.json"))
        self.full_json.write_text(json.dumps(self.json_test_data), encoding="utf-8")

        # Invalid JSON 
        self.bad_json = Path(os.path.join(self.temp_dir, "bad.json"))
        self.bad_json.write_text('{"id": 1, "name": "Jane",}', encoding="utf-8")

        # Work from the temp directory
        os.chdir(self.temp_dir)


    def _import_user_config(self):
        """
        Try to import UserConfig.
        If not found, skip the test suite gracefully (for now).
        TODO: once startup configuration code is written, swap in correct file
        import

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

        self.skipTest(
            "UserConfig not implemented yet or import path not found. "
            "Create src/config.py (or config.py) with class UserConfig."
        )

    def test_uses_defaults_when_no_config_file(self):
        """
        If no config file is found, defaults should be returned.
        TODO: once startup configuration code is written, 
        load in real defuaults

        """
        UserConfig = self._import_user_config()

        defaults = {
            "language": "en",
            "region": "canada",
            "theme": "light",
            "font size": "12"
        }
        cfg = UserConfig(defaults=defaults)

        # Point to a file that does not exist in the temp dir
        missing_path = str(Path(self.temp_dir) / "no_such_config.json")
        result = cfg.load(missing_path)

        # Uses defaults
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["region"], "canada")
        self.assertEqual(result["theme"], "light")
        self.assertEqual(result["font size"], "12")

    def test_loads_from_valid_json_when_present(self):
        """
        If a valid JSON config is present, data should be loaded from that file.
        """
        UserConfig = self._import_user_config()

        defaults = {
            "language": "en",
            "region": "canada",
            "theme": "light",
            "font size": "12"
        }
        cfg = UserConfig(defaults=defaults)

        # Load from test configuration
        result = cfg.load(str(self.full_json))

        # Expect exactly the on-disk contents (no merging with defaults)
        expected = json.loads(self.full_json.read_text(encoding="utf-8"))
        self.assertEqual(result, expected)

        # Ensure it didn't just return the defaults when a good file exists
        self.assertNotEqual(result, defaults)


    def test_loaded_preferences_are_present(self):
        """
        Ensure nested preferences from the file are present and intact.

        """
        UserConfig = self._import_user_config()

        # Supply defaults that differ from the file to ensure the file wins
        cfg = UserConfig(defaults={
            "preferences": {
                "theme": "light",
                "language": "fr",
                "region": "france",
                "font size": "12"
            }
        })

        result = cfg.load(str(self.full_json))
        self.assertIn("preferences", result)
        self.assertEqual(result["preferences"]["theme"], "dark")
        self.assertEqual(result["preferences"]["language"], "en")
        self.assertEqual(result["preferences"]["region"], "canada")
        self.assertEqual(result["preferences"]["font size"], "14")

    def test_invalid_json_falls_back_to_defaults(self):
        """
        If the JSON is invalid, implementation should fall back to defaults.
        
        """
        UserConfig = self._import_user_config()

        defaults = {
            "preferences": {
                "theme": "light",
                "language": "fr",
                "region": "france",
                "font size": "12"
            }
        }
        cfg = UserConfig(defaults=defaults)

        result = cfg.load(str(self.bad_json))

        # Falls back to defaults
        self.assertEqual(result, defaults)

    def tearDown(self):
        """
        Cleanup after each test:
        - Return to the original working directory.
        - Remove the temporary folder and its contents.
        """
        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
