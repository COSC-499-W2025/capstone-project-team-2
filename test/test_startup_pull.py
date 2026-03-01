import os
import tempfile
import shutil
import unittest
import json
from pathlib import Path
import orjson 
from src.user_startup_config import ConfigLoader


class TestStartupConfigPull(unittest.TestCase):
    """
    Tests the ability to pull settings from configuration files at startup,

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
        self.full_json = Path(self.temp_dir) / "full_config.json"
        self.full_json.write_text(json.dumps(self.json_test_data), encoding="utf-8")

        # Invalid JSON
        self.bad_json = Path(self.temp_dir) / "bad.json"
        self.bad_json.write_text('{"id": 1, "name": "Jane",}', encoding="utf-8")

        # Work from the temp directory
        os.chdir(self.temp_dir)

    def _import_user_config(self):
        """
        Provide a UserConfig adapter that stages files in the temp dir and
        delegates to the real ConfigLoader. 
        
        """
        temp_root = Path(self.temp_dir)
        user_path = temp_root / "UserConfigs.json"
        default_path = temp_root / "default_user_configuration.json"

        class UserConfig:
            def __init__(self, defaults=None):
                self._defaults = defaults or {}

            def _write_defaults_file(self):
                # Write defaults dict as the default config file (bytes for orjson)
                default_path.write_bytes(orjson.dumps(self._defaults))

            def _reset_stage(self):
                # Ensure a clean slate for each load() call
                for p in (user_path, default_path):
                    if p.exists():
                        p.unlink()

            def load(self, path=None):
                # Always use the real ConfigLoader, but point it at the temp root
                loader = ConfigLoader()
                loader.project_root = temp_root
                loader.user_config_path = user_path
                loader.default_config_path = default_path

                self._reset_stage()

                # If caller passed a path, stage it as the "user" file case
                if path is not None:
                    p = Path(path)
                    if not p.exists():
                        # No user file: write defaults as the default file
                        self._write_defaults_file()
                        return loader.load()

                    raw = p.read_bytes()
                    # Check if it's valid JSON; if yes, treat as user file
                    try:
                        orjson.loads(raw)  # validation only
                        user_path.write_bytes(raw)
                        # Also stage defaults (mirrors real layout; not strictly required)
                        self._write_defaults_file()
                        return loader.load()
                    except orjson.JSONDecodeError:
                        # Invalid user JSON -> fall back to default file
                        user_path.write_bytes(raw)   # keep the invalid user file
                        self._write_defaults_file()  # provide a valid default
                        return loader.load()

                # No path provided: create only the default file from provided defaults
                self._write_defaults_file()
                return loader.load()

        return UserConfig

    def test_uses_defaults_when_no_config_file(self):
        """
        If no config file is found, defaults should be returned.
        (Here: we emulate "defaults" by writing them to the default file and
        letting ConfigLoader load it.)
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
        (We stage the invalid user file and a valid default file.)
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
