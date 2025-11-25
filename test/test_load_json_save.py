import json
import os, datetime, pandas as pd

import unittest

from src.load_json_save import SaveLoader

class TestLoadJSON(unittest.TestCase):
    '''
    Test class that tests load_json_save.py
    '''

    #Used for saving in setup for tests
    original_dict = {
        "duration": str(datetime.timedelta(weeks=2)),
        "name": "testname",
        "stuff": ["one", "two"]
    }

    #Used for comparing to the loaded result
    compare_dict = {
        "duration": datetime.timedelta(weeks=2),
        "name": "testname",
        "stuff": ["one", "two"]
    }

    def setUp(self):
        '''
        Sets up json file to be loaded in tests
        '''
        json_dict = json.dumps(self.original_dict)
        with open("load_test.json", 'w') as file:
            file.write(json_dict)

    def test_load_file(self):
        '''
        Positive Test
        Ensures loading file string returns no exception
        '''
        try:
            loader = SaveLoader("load_test.json")
        except:
            assert False
        assert True

    def test_load_duration(self):
        '''
        Positive Test
        Ensures timedelta correctly converted when loading into dictionary
        '''
        loader = SaveLoader("load_test.json")
        loaded_dict = loader.return_dict()
        self.assertTrue(datetime.timedelta(weeks=2) == loaded_dict["duration"])

    def test_load_dict(self):
        '''
        Positive Test
        Ensures entire loaded dictionary is correct
        '''
        loader = SaveLoader("load_test.json")
        loaded_dict = loader.return_dict()
        self.assertTrue(self.compare_dict == loaded_dict)

    def tearDown(self):
        '''
        Removes the file created for tests
        '''
        if os.path.exists("load_test.json"):
            os.remove("load_test.json")