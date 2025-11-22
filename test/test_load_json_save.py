import json
import os, datetime, pandas as pd

import unittest

from src.load_json_save import SaveLoader

class TestLoadJSON(unittest.TestCase):
    
    original_dict = {
        "duration": str(datetime.timedelta(weeks=2)),
        "name": "testname",
        "stuff": ["one", "two"]
    }

    compare_dict = {
        "duration": datetime.timedelta(weeks=2),
        "name": "testname",
        "stuff": ["one", "two"]
    }

    def setUp(self):
        json_dict = json.dumps(self.original_dict)
        with open("load_test.json", 'w') as file:
            file.write(json_dict)

    def test_load_file(self):
        try:
            loader = SaveLoader("load_test.json")
        except:
            assert False
        assert True

    def test_load_duration(self):
        loader = SaveLoader("load_test.json")
        loaded_dict = loader.return_dict()
        self.assertTrue(datetime.timedelta(weeks=2) == loaded_dict["duration"])

    def test_load_dict(self):
        loader = SaveLoader("load_test.json")
        loaded_dict = loader.return_dict()
        self.assertTrue(self.compare_dict == loaded_dict)