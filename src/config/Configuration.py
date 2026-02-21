import os
from pathlib import Path
import orjson

class configuration_for_users:

    """
    This is class which takes in json file which in this case is the user configuration
    and save locally

    """
    def __init__(self,jsonfile):
        """
        Initializes the Configuration class instance

        This constructor sets up the user configuration file, determines the
        root directory of the project, and defines the path where configuration file("UserConfigs.json")
        will be stored

        :param jsonfile: User Configuration **json file**
        """
        self.jsonfile = jsonfile

        project_root = Path(__file__).resolve().parents[2]

        self.config_dir = project_root / "User_config_files"
        self.loc_to_save = self.config_dir / "UserConfigs.json"

        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_with_consent(self, external_consent:bool=False,data_consent:bool=False):
        """
        Adds a new entry to the json file with consent preferences
        Does not save the JSON file

       :param external_consent: (bool) Whether user consents to external data sharing (default: False)
       :param data_consent: (bool) Whether user consents to data collection (default: False)
        """
        if self.jsonfile is not None:
            self.jsonfile.update({'consented':{
                "external": external_consent,
                "Data consent": data_consent
            }})
            #Here I am added a new key,value pair to the actual user configuration when the json file is not none


    def save_config(self):

        """
           Saves the JSON configuration file to the user's system.

           :return:
               bool: True if the file was saved successfully, False otherwise.
           """


        try:
            with open(self.loc_to_save, "wb") as f:
                f.write(orjson.dumps(self.jsonfile, option=orjson.OPT_INDENT_2))
            return os.path.exists(self.loc_to_save)
        except Exception:
            return False
        #Returns bool state to see if the actually file exists and created successfully

























