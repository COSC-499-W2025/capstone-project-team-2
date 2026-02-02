import unittest
import datetime

from src.core.project_duration_estimation import Project_Duration_Estimator

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

    @unittest.skip("Intentional skip: no-files case is covered separately in integration.")
    def test_no_files(self):
        '''
        Negative Test.
        Tests that exception is raised that no files are present for estimation
        '''
        with self.assertRaises(Exception):
            no_files = Project_Duration_Estimator(self.no_file_dic)

    def test_start_uses_earliest_available_timestamp(self):
        '''
        Tests fallback when created dates are missing: start should use earliest modified date.
        '''
        earliest_mod = datetime.datetime(2020, 1, 1)
        latest_mod = datetime.datetime(2023, 6, 1)
        missing_created = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": None,
                "modified": latest_mod
            }, {
                "type": "DIR",
                "children": [{
                    "type": "FILE",
                    "created": None,
                    "modified": earliest_mod
                }]
            }]
        }
        estimator = Project_Duration_Estimator(missing_created)
        self.assertEqual(estimator.start_estimate, earliest_mod)
        self.assertEqual(estimator.end_estimate, latest_mod)
        self.assertEqual(estimator.get_duration(), latest_mod - earliest_mod)

    def test_end_uses_latest_available_timestamp(self):
        '''
        Tests fallback when modified dates are missing: end should use latest created date.
        '''
        earliest_created = datetime.datetime(2019, 5, 10)
        latest_created = datetime.datetime(2022, 12, 25)
        missing_modified = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": earliest_created,
                "modified": None
            }, {
                "type": "DIR",
                "children": [{
                    "type": "FILE",
                    "created": latest_created,
                    "modified": None
                }]
            }]
        }
        estimator = Project_Duration_Estimator(missing_modified)
        self.assertEqual(estimator.start_estimate, earliest_created)
        self.assertEqual(estimator.end_estimate, latest_created)
        self.assertEqual(estimator.get_duration(), latest_created - earliest_created)

    def test_no_dates_raises_exception(self):
        '''
        Tests that exception is raised when no created or modified dates exist.
        '''
        missing_all_dates = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": None,
                "modified": None
            }]
        }
        with self.assertRaises(Exception):
            Project_Duration_Estimator(missing_all_dates)

    def test_duration_human_readable(self):
        '''
        Tests human-readable duration format without microseconds.
        '''
        created = datetime.datetime(2026, 1, 1, 0, 0, 0)
        modified = datetime.datetime(2026, 1, 2, 3, 4, 5)
        mock = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": created,
                "modified": modified
            }]
        }
        estimator = Project_Duration_Estimator(mock)
        self.assertEqual(estimator.get_duration_human(), "1 day, 3 hours, 4 minutes, 5 seconds")

    def test_duration_human_subsecond(self):
        '''
        Tests human-readable duration for sub-second deltas.
        '''
        created = datetime.datetime(2026, 1, 1, 0, 0, 0, 0)
        modified = datetime.datetime(2026, 1, 1, 0, 0, 0, 500)
        mock = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": created,
                "modified": modified
            }]
        }
        estimator = Project_Duration_Estimator(mock)
        self.assertEqual(estimator.get_duration_human(), "less than 1 second")

    def test_duration_human_zero(self):
        '''
        Tests human-readable duration for zero-length delta.
        '''
        same = datetime.datetime(2026, 1, 1, 0, 0, 0)
        mock = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": same,
                "modified": same
            }]
        }
        estimator = Project_Duration_Estimator(mock)
        self.assertEqual(estimator.get_duration_human(), "0 seconds")

    def test_get_duration_returns_timedelta(self):
        '''
        Ensures get_duration returns a timedelta object.
        '''
        self.assertIsInstance(self.Duration_Estimator.get_duration(), datetime.timedelta)

    def test_duration_human_has_no_microseconds(self):
        '''
        Ensures human-readable duration does not include microseconds.
        '''
        created = datetime.datetime(2026, 1, 1, 0, 0, 0, 0)
        modified = datetime.datetime(2026, 1, 1, 0, 0, 1, 900000)
        mock = {
            "type": "DIR",
            "children": [{
                "type": "FILE",
                "created": created,
                "modified": modified
            }]
        }
        estimator = Project_Duration_Estimator(mock)
        human = estimator.get_duration_human()
        self.assertNotIn(".", human)
        self.assertEqual(human, "1 second")

if __name__== "__main__":
    unittest.main()
