import json
import os
import pathlib as pa

import orjson
from platformdirs import user_config_path
from watchfiles.cli import import_exit




class configuration_for_users:

    """
    This is class which takes in json file which in this case is the user configuration
    and save locally

    """
    def __init__(self,jsonfile,loc_to_save='User_config_files'):
        """
        :param jsonfile: User Configuration **json file**
        """
        self.jsonfile = jsonfile
        self.project_Root = pa.Path(__file__).parent.parent
        self.loc_to_save=pa.Path(os.path.join(self.project_Root,loc_to_save,"UserConfigs.json"))


    def save_with_consent(self, external_consent:bool=False,data_consent:bool=False):
        """
        Adds a new entry to the json file with consent preferences

       :param external_consent: (bool) Whether user consents to external data sharing (default: False)
       :param data_consent: (bool) Whether user consents to data collection (default: False)
        """
        if self.jsonfile is not None:
            self.jsonfile.update({'consented':{
                "external": external_consent,
                "Data consent": data_consent
            }})


    def save_config(self):

        """
           Saves the JSON configuration file to the user's system.

           :return:
               bool: True if the file was saved successfully, False otherwise.
           """


        with open(self.loc_to_save, "wb") as f:
            print("HIT")
            f.write(orjson.dumps(self.jsonfile,option=orjson.OPT_INDENT_2))

        return os.path.exists("UserConfigs.json")

























