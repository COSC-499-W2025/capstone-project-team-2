import json
import os
import orjson


class configuration_for_users:

    """
    This is class which takes in json file which in this case is the user configuration
    and save locally

    """
    def __init__(self,jsonfile):
        """
        :param jsonfile: User Configuration **json file**
        """
        self.jsonfile = jsonfile

    def save_config(self):
        """
           Saves the JSON configuration file to the user's system.

           :return:
               bool: True if the file was saved successfully, False otherwise.
           """
        with open("UserConfigs.json", "wb") as f:
            f.write(orjson.dumps(self.jsonfile,option=orjson.OPT_INDENT_2))

        if os.path.exists("UserConfigs.json"):
            return True

        if not os.path.exists("UserConfigs.json"):
            return False




















