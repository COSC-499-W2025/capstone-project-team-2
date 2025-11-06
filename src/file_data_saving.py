import json
import os

'''

Subject to change, but general idea. Must be dictionary.
Analysis of each file of hierarchy should be modelled in a dictionary as so:
Starting with project folder
{
"name": "project folder name"
"folders": [
        {
        "name": "folder name"
        "folders": [...]
        "files": [...]
        },
        ...
    ]
"files": [
        {
        "name": "file name"
        "file type": "file type"
        "file size": int
        "created": datetime
        "modified": datetime
        "author": "author"
        },
        ...
    ]
}

'''

class SaveFileAnalysisAsJSON:
    '''
    A class containing the functions for saving a file hierarchy with each file associated with the data extracted from them.
    
    Saves those files in JSON format
    '''

    def convertAnalysisToJSON(self, project_dict: dict) -> str:
        '''
        Takes a dictionary and converts it to JSON string format

        For use only within SaveFileAnalysisAsJSON
        '''
        project_json  = json.dumps(project_dict, indent=4)
        return project_json
    
    def saveAnalysis(self, project_name: str , project_dict: dict, folder_path: str):
        '''
        Saves a dictionary to a JSON file in the directory "folder_path"

        Saves as "project_name.json"
        '''
        json_project = self.convertAnalysisToJSON(project_dict)
        write_file = os.path.join(folder_path, project_name + r".json")
        with open(write_file, 'w') as file:
            file.write(json_project)

    def hierarchyToProject(self, hierarchy_analysis: dict) -> dict:
        '''
        Places a hierarchy of files inside a dictionary.
        Intended to be used before adding overall project details to dictionary for saving.

        Returns a dictionary with hierarchy stored as "project_files"
        '''
        project_dict = {
            "project_files": hierarchy_analysis
        }
        return project_dict