import json
import os
import pathlib as pa

import orjson




class configuration_for_users:

    """
    This is class which takes in json file which in this case is the user configuration
    and save locally

    """
    def __init__(self,jsonfile,loc_to_save='User_config_files'):
        """
        Initializes the Configuration class instance

        This constructor sets up the user configuration file, determines the
        root directory of the project, and defines the path where configuration file("UserConfigs.json")
        will be stored

        :param jsonfile: User Configuration **json file**
        """
        self.jsonfile = jsonfile
        self.project_Root = pa.Path(__file__).parent.parent #Here I am assigning the project root to variable called project Root
        self.loc_to_save=pa.Path(os.path.join(self.project_Root,loc_to_save,"UserConfigs.json"))# Here I am creating the location path by combing the project root, the classes loc_save and file name itself


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
            #Here I am added a new key,value pair to the actual user configuration when the json file is not none


    def save_config(self):

        """
           Saves the JSON configuration file to the user's system.

           :return:
               bool: True if the file was saved successfully, False otherwise.
           """


        with open(self.loc_to_save, "wb") as f: #Reading the json_file
            print("HIT")
            f.write(orjson.dumps(self.jsonfile,option=orjson.OPT_INDENT_2)) #dumping the data it to be saved using the orjson library

        return os.path.exists(self.loc_to_save)
        #Returns bool state to see if the actually file exists and created successfully

























