import os
from pathlib import Path
import orjson
from typing import Dict, Any
from src.core.app_context import runtimeAppContext

class configuration_for_users:

    """
    This is class handles user configuration storage using the MySQL database.
    All configuration data is stored in the user_config table.

    """
    def __init__(self, initial_data: Dict[str, Any] = None):
        """
        Initializes the Configuration class instance

        Args: 
            initial_data: Optional dictionary to initialize config with. 
            If None, loads, existing config from dataset
        """
        if initial_data is not None:
            self.config_data = initial_data
        else:
            # Load existing config from database, or start with empty dict
            self.config_data = runtimeAppContext.store.get_config("user_settings") or {}


    def save_with_consent(self, external_consent:bool=False,data_consent:bool=False):
        """
        Adds a new entry to the json file with consent preferences

       Args:
            external_consent: Whether user consents to external data sharing (default: False)
            data_consent: Whether user consents to data collection (default: False)
            
        """
        self.config_data["consented"] ={
            "external": external_consent,
            "Data consent": data_consent
        }


    def save_config(self):

        """
           Saves to MySQL

           :return:
               bool: True if the file was saved successfully, False otherwise.
           """

        return runtimeAppContext.store.save_config(self.config_data, "user_settings")

    def load_config(self) -> Dict[str, Any]:
        """
        Loads the configuration from the database.

        Returns:
            dict: The configuration dictionary, or empty dict if not found.
        """
        self.config_data = runtimeAppContext.store.get_config("user_settings") or {}
        return self.config_data

    def get_consent_status(self) -> Dict[str, bool]:
        """
        Get the current consent settings.

        Returns:
            dict: Dictionary with 'external' and 'data_consent' boolean values.
        """
        return runtimeAppContext.store.get_consent_settings()

    def update_field(self, key: str, value: Any) -> bool:
        """
        Update a specific field in the configuration.

        Args:
            key: The configuration key to update.
            value: The new value for the key.

        Returns:
            bool: True if successful, False otherwise.
        """
        self.config_data[key] = value
        return self.save_config()

    def get_field(self, key: str, default: Any = None) -> Any:
        """
        Get a specific field from the configuration.

        Args:
            key: The configuration key to retrieve.
            default: Default value if key doesn't exist.

        Returns:
            The value for the key, or default if not found.
        """
        if not self.config_data:
            self.load_config()
        return self.config_data.get(key, default)
























