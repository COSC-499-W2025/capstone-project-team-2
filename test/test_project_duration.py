import unittest
import datetime

from src.project_duration_estimation import Project_Duration_Estimator

class TestDurationEstimator(unittest.TestCase):
    '''
    Test class for project_duration_estimation.py, class Project_Duration_Estimator
    '''

    mock_dictionary = { #Dictionary mocking the format shown by data_extraction.py for testing purposes
        "type": "DIR",
        "children": [{
            "type": "FILE",
            "created": datetime.datetime(2003, 11, 22),
            "modified": datetime.datetime(2025, 11, 22)
        }, {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": datetime.datetime(2001, 9, 1),
                "modified": datetime.datetime(2025, 9, 1)
            }, {
                "type": "FILE",
                "created": datetime.datetime(2000, 1, 1),
                "modified": datetime.datetime(2025, 1, 1)
            }]
        }]
    }

    no_file_dic = { #Intended for a no file test
        "type": "DIR",
        "children": []
    }

    correct_end_date = datetime.datetime(2025, 11, 22) #Correct latest last modified date of mock dictionary
    correct_start_date = datetime.datetime(2000, 1, 1)  #Correct earliest creation date of mock dictionary
    correct_duration = correct_end_date - correct_start_date    #Correct project duration of mock dictionary

    def setUp(self):
        '''
        Initalizes class for testing correct values. Inserts mock dictionary.
        '''
        self.Duration_Estimator = Project_Duration_Estimator(self.mock_dictionary)

    def test_correct_end_date(self):
        '''
        Postitive Test.
        Tests that the end estimate is correct for the mock dictionary
        '''
        self.assertEqual(self.Duration_Estimator.end_estimate, self.correct_end_date)

    def test_correct_start_date(self):
        '''
        Positive Test.
        Tests that the start estimate is correct for the mock dictionary
        '''
        self.assertEqual(self.Duration_Estimator.start_estimate, self.correct_start_date)

    def test_correct_duration(self):
        '''
        Positive Test.
        Tests that the duration estimate is correct for the mock dictionary.
        '''
        self.assertEqual(self.Duration_Estimator.get_duration(), self.correct_duration)

    def test_no_files(self):
        '''
        Negative Test.
        Tests that exception is raised that no files are present for estimation
        '''
        with self.assertRaises(Exception):
            no_files = Project_Duration_Estimator(self.no_file_dic)

if __name__== "__main__":
    unittest.main()