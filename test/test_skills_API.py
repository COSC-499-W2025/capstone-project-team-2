"""Unit tests for the skills FastAPI endpoint."""

import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.API.general_API import app

class TestSkillsAPI(unittest.TestCase):
    """
    Validate /skills output for summary and detailed modes.

    Returns:
        None
    """

    def setUp(self) -> None:
        """
        Initialize a test client for API requests.

        Returns:
            None
        """
        self.client = TestClient(app)

    def test_list_skills_unique_sorted(self) -> None:
        """
        Return de-duplicated, sorted skills by default.

        Returns:
            None
        """
        sample_history = [
            {"project_name": "A", "skills": ["Python", "FastAPI"]},
            {"project_name": "B", "skills": ["FastAPI", "Docker"]},
            {"project_name": "C", "skills": []},
        ]

        with patch("src.API.skills_API.list_skill_history") as mock_history:
            mock_history.return_value = sample_history
            response = self.client.get("/skills")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["Docker", "FastAPI", "Python"])

    def test_list_skills_detailed(self) -> None:
        """
        Return the full skill history when detailed is requested.

        Returns:
            None
        """
        sample_history = [
            {"project_name": "A", "skills": ["Python"]},
        ]

        with patch("src.API.skills_API.list_skill_history") as mock_history:
            mock_history.return_value = sample_history
            response = self.client.get("/skills?detailed=true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sample_history)

if __name__ == "__main__":
    unittest.main()
