from pathlib import Path
from typing import Any, Dict
from src.core.app_context import runtimeAppContext
import uuid
import orjson

# Default configuration 
DEFAULT_USER_CONFIG: Dict[str, Any] = {
    "ID": None, 
    "name": "",
    "email": "",
    "consented": {
        "external": False,
        "Data consent": False
    }
}

def get_default_config() -> Dict[str, Any]:
    """
     Get a fresh copy of the default configuration with a new generated ID.
    
    Returns:
        dict: Default configuration with a unique ID.
    """
    config = DEFAULT_USER_CONFIG.copy()
    config["consented"] = DEFAULT_USER_CONFIG["consented"].copy()
    config["ID"] = str(uuid.uuid4())
    return config

class ConfigLoader:
    """
    Utility class for loading default configuration and initializing the database.
    
    Primary use cases:
    - First-time setup: Load defaults from file and save to database
    - Reset to defaults: Reload default configuration
    
    For normal config access, use configuration_for_users class instead.
    
    """
    def __init__(self):
        """
        Initialize the ConfigLoader.
        
        Sets up the path to the default configuration file.

        """
        
        project_root = Path(__file__).resolve().parents[2]

        self.config_dir = project_root / "User_config_files"
        self.user_config_path = self.config_dir / "UserConfigs.json"
        self.default_config_path = self.config_dir / "default_user_configuration.json"
        
    def get_defaults(self) -> Dict[str, Any]:
        """
        Get the default configuration.
        
        Returns:
            dict: Default configuration with a unique ID.
        """
        return get_default_config()

    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset the database configuration to defaults.
        
        Overwrites any existing config in database with fresh defaults.
        Note: This generates a new ID.
        
        Returns:
            dict: The default configuration that was saved.
        """
        defaults = get_default_config()
        runtimeAppContext.store.save_config(defaults, "user_settings")
        print("[INFO] Configuration reset to defaults.")
        return defaults


    def initialize_database_config(self) -> Dict[str, Any]:
        """
        Initialize the database with default configuration.
        
        Creates a new default config with a fresh ID and saves to database.
        Useful for first-time setup.
        
        Returns:
            dict: The default configuration that was saved.
        """
        defaults = get_default_config()
        runtimeAppContext.store.save_config(defaults, "user_settings")
        print("[INFO] Database initialized with default configuration.")
        return defaults
    
    def ensure_config_exists(self) -> Dict[str, Any]:
        """
        Ensure configuration exists in database, initializing if needed.
        
        Checks if config exists in database. If not, creates default config.
        
        Returns:
            dict: The configuration (existing or newly initialized).
        """
        existing = runtimeAppContext.store.get_config("user_settings")
        if existing:
            return existing
        
        print("[INFO] No configuration found. Initializing with defaults...")
        return self.initialize_database_config()
    
    # might not need this one anymore
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
            existing = runtimeAppContext.store.get_config("user_settings")
            if existing:
             return existing
        except Exception as e:
            print(f"[WARN] Could not load config from database: {e}. Using defaults...")

        print("[INFO] No saved user configuration found. Loading defaults...")
        return get_default_config()
