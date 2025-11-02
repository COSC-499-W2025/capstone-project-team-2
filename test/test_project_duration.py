import unittest
import datetime

from src.project_duration_estimation import Project_Duration_Estimator

class TestDurationEstimator(unittest.TestCase):

    mock_dictionary = {
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

    correct_end_date = datetime.datetime(2025, 11, 22) 
    correct_start_date = datetime.datetime(2000, 1, 1)
    correct_duration = correct_end_date - correct_start_date

    def setUp(self):
        self.Duration_Estimator = Project_Duration_Estimator(self.mock_dictionary)

    def test_correct_end_date(self):
        self.assertEqual(self.Duration_Estimator.end_estimate, self.correct_end_date)

    def test_correct_start_date(self):
        self.assertEqual(self.Duration_Estimator.start_estimate, self.correct_start_date)

    def test_correct_duration(self):
        self.assertEqual(self.Duration_Estimator.get_duration(), self.correct_duration)

if __name__== "__main__":
    unittest.main()