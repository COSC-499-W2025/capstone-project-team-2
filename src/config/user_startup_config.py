from pathlib import Path
import orjson
from typing import Any, Dict

class ConfigLoader:
    """
    This class loads the configuration files of the user if present and default configurations if not
    
    """
    def __init__(self):
        """
        This method locates the project and configuration file

        """
        
        project_root = Path(__file__).resolve().parents[2]

        self.config_dir = project_root / "User_config_files"
        self.user_config_path = self.config_dir / "UserConfigs.json"
        self.default_config_path = project_root / "Templates" / "default_user_configuration.json"
        
    def _load_file(self, path: Path) -> Dict[str, Any]:
        """
        This method takes a file path, opens it in binary mode, 
        reads its contents, and uses orjson to convert that 
        JSON data into a Python dictionary
        """
        with path.open("rb") as f:  # orjson expects bytes
            return orjson.loads(f.read())

    def load(self) -> Dict[str, Any]:
        """
        This method tries to load the user configuration first
        and if it fails it loads the default configuration instead.
        """
        try:
            return self._load_file(self.user_config_path)
        except (FileNotFoundError, orjson.JSONDecodeError):
            pass  # Silent fail - fall back to defaults

        try:
            return self._load_file(self.default_config_path)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Default config not found at {self.default_config_path}"
            )
        except orjson.JSONDecodeError as e:
            raise ValueError(
                f"Default configuration file {self.default_config_path} is invalid: {e}"
            )
