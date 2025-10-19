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

    def convertAnalysisToJSON(hierarchy_analysis: dict) -> str:
        '''
        Takes a dictionary and converts it to JSON string format

        For use only within SaveFileAnalysisAsJSON
        '''
        hierarchy_analysis_json  = json.dumps(hierarchy_analysis, indent=4)
        return hierarchy_analysis_json
    
    def saveAnalysis(project_name: str , hierarchy_analysis: dict, folder_path: str):
        '''
        Saves a dictionary to a JSON file in the directory "folder_path"

        Saves as "project_name.json"
        '''
        json_analysis = SaveFileAnalysisAsJSON.convertAnalysisToJSON(hierarchy_analysis)
        write_file = os.path.join(folder_path, project_name + r".json")
        with open(write_file, 'w') as file:
            file.write(json_analysis)