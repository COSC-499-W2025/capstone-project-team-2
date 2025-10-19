import os
import json

import unittest

from src.file_data_saving import SaveFileAnalysisAsJSON

class Test_JSON_saving(unittest.TestCase):
    '''
    Test file for file_data_saving.py
    '''


    test_name = "test_project"
    test_dict = {
        "name": "project",
        "folders": [{
            "name": "folder1"
            }, {
            "name": "folder2"
            }
        ],
        "files": [{
            "name": "file1",
            "file type": "txt",
            "file size": 128
            }
        ]
    }

    def test_json_save(self):
        '''
        Tests that file is saved
        '''
        SaveFileAnalysisAsJSON.saveAnalysis(self.test_name, self.test_dict, r"./")
        self.assertTrue(os.path.exists(r"./"+self.test_name+r".json"))

    def test_json_integrity(self):
        '''
        Tests that file is saved with correct data, fails if file was not saved successfully
        '''
        SaveFileAnalysisAsJSON.saveAnalysis(self.test_name, self.test_dict, r"./")
        if not os.path.exists(r"./"+self.test_name+r".json"):
            assert False
        with open(r"./"+self.test_name+r".json", 'r') as file:
            file_text = file.read()
        json_text = json.loads(file_text)
        self.assertTrue(json_text == self.test_dict)

    def tearDown(self):
        '''
        Removes the file created during tests if it exists
        '''
        if os.path.exists(r"./"+self.test_name+r".json"):
            os.remove(r"./"+self.test_name+r".json")