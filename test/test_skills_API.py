"""Unit tests for the skills FastAPI endpoint."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.API import skills_API
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

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "project_insights.json"
            storage_path.write_text("[]", encoding="utf-8")
            with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", Path(tmpdir)):
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

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "project_insights.json"
            storage_path.write_text("[]", encoding="utf-8")
            with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", Path(tmpdir)):
                with patch("src.API.skills_API.list_skill_history") as mock_history:
                    mock_history.return_value = sample_history
                    response = self.client.get("/skills?detailed=true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sample_history)

    def test_list_skills_missing_insights_returns_404(self) -> None:
        """
        Return 404 when the insights file does not exist.

        Returns:
            None
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", Path(tmpdir)):
                response = self.client.get("/skills")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json().get("detail"),
            "No project insights have been recorded yet.",
        )

    def test_list_skills_empty_history_returns_404(self) -> None:
        """
        Return 404 when insights exist but have no history.

        Returns:
            None
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "project_insights.json"
            storage_path.write_text("[]", encoding="utf-8")
            with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", Path(tmpdir)):
                with patch("src.API.skills_API.list_skill_history") as mock_history:
                    mock_history.return_value = []
                    response = self.client.get("/skills")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json().get("detail"),
            "No project insights have been recorded yet.",
        )

    def test_list_skills_filters_empty_and_none(self) -> None:
        """
        Ignore empty and None skill entries when summarizing skills.

        Returns:
            None
        """
        sample_history = [
            {"project_name": "A", "skills": ["Python", "", None]},
            {"project_name": "B", "skills": [None, "FastAPI"]},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "project_insights.json"
            storage_path.write_text("[]", encoding="utf-8")
            with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", Path(tmpdir)):
                with patch("src.API.skills_API.list_skill_history") as mock_history:
                    mock_history.return_value = sample_history
                    response = self.client.get("/skills")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["FastAPI", "Python"])

    def test_list_skills_type_error_returns_500(self) -> None:
        """
        Return 500 when legacy_save_dir is invalid (TypeError).

        Returns:
            None
        """
        client = TestClient(app, raise_server_exceptions=False)
        with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", None):
            response = client.get("/skills")

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to retrieve skills:", response.json().get("detail", ""))

    def test_list_skills_oserror_returns_500(self) -> None:
        """
        Return 500 when list_skill_history raises an OSError.

        Returns:
            None
        """
        client = TestClient(app, raise_server_exceptions=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "project_insights.json"
            storage_path.write_text("[]", encoding="utf-8")
            with patch.object(skills_API.runtimeAppContext, "legacy_save_dir", Path(tmpdir)):
                with patch("src.API.skills_API.list_skill_history") as mock_history:
                    mock_history.side_effect = OSError("boom")
                    response = client.get("/skills")

        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to retrieve skills:", response.json().get("detail", ""))

if __name__ == "__main__":
    unittest.main()
