import json
import os, datetime, pandas as pd

class SaveLoader:
    '''
    Class for loading saved project data in json format, converting to a dictionary

    Constructor handles file loading
    '''

    def __init__(self, json_filepath):
        '''
        Constructor: loads json file as string

        Paramater json_filepath is the full path for the file to load

        Will raise exception if file cannot be read
        '''

        with open(json_filepath, 'r') as file:
            self.json_text = file.read()

    def return_dict(self) -> dict:
        '''
        Returns loaded json file as a dictionary

        Converts variables that were saved as strings back to their non-string variables
        '''

        project_dict = json.loads(self.json_text)   #Loads json string into a dictionary
        if "duration" in project_dict:
            project_dict = self.convertProjectDuration(project_dict)
        return project_dict

    def convertProjectDuration(self, project_dict: dict) -> dict:
        '''
        Converts project duration from string to timedelta
        '''

        project_dict["duration"] = pd.Timedelta(project_dict["duration"]).to_pytimedelta()  #Converts project duration to timedelta using a pandas library
        return project_dict