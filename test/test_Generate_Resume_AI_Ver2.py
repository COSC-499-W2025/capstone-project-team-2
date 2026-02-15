"""Unit tests for the AI Resume Generator Version 2 module."""
import unittest
from unittest.mock import patch, MagicMock

from src.reporting.Generate_Resume_AI_Ver2 import (
    ResumeProjectInfo, AIResumeEntry, GenerateResumeAI_Ver2,
)

SAMPLE_DATA = {
    "duration_estimate": "3 months",
    "resume_item": {
        "project_name": "Demo App",
        "summary": "A web app for tasks.",
        "highlights": ["Built REST API", "Implemented auth"],
        "project_type": "collaborative",
        "detection_mode": "git",
        "languages": ["Python", "JavaScript"],
        "frameworks": ["Flask", "React"],
        "skills": ["Python", "REST APIs", "React"],
        "framework_sources": {"Flask": ["requirements.txt"]},
    },
    "project_type": {"project_type": "collaborative", "mode": "git"},
    "oop_analysis": {"score": {"oop_score": 0.72, "rating": "high"}},
}

LLM_RESPONSE = {
    "project_title": "Task Manager",
    "one_sentence_summary": "Built a full-stack task app.",
    "detailed_summary": "Developed a task manager with Flask and React.",
    "key_responsibilities": ["Designed API", "Implemented auth"],
    "key_skills_used": ["Python", "Flask"],
    "tech_stack": "Python, Flask, React",
    "impact": "Streamlined tracking for 10+ users.",
}

MODULE = "src.reporting.Generate_Resume_AI_Ver2"


class TestResumeProjectInfo(unittest.TestCase):
    """Tests for ResumeProjectInfo.from_project_data."""

    def test_populates_all_fields(self):
        """Verify all fields are correctly extracted from project data."""
        info = ResumeProjectInfo.from_project_data(SAMPLE_DATA)
        self.assertEqual(info.project_name, "Demo App")
        self.assertEqual(info.languages, ["Python", "JavaScript"])
        self.assertEqual(info.oop_score, 0.72)
        self.assertEqual(info.oop_rating, "high")
        self.assertEqual(info.duration_estimate, "3 months")

    def test_empty_dict_returns_defaults(self):
        """Ensure default values are returned when given empty input."""
        info = ResumeProjectInfo.from_project_data({})
        self.assertEqual(info.project_name, "")
        self.assertEqual(info.project_type, "unknown")
        self.assertEqual(info.languages, [])
        self.assertEqual(info.oop_score, 0.0)

    def test_missing_oop_analysis_defaults(self):
        """Handle missing OOP analysis section gracefully with defaults."""
        data = {"resume_item": {"project_name": "Script", "languages": ["Python"],
                "skills": [], "frameworks": [], "summary": "", "highlights": [],
                "framework_sources": {}},
                "project_type": {"project_type": "individual"},
                "duration_estimate": "1 week"}
        info = ResumeProjectInfo.from_project_data(data)
        self.assertEqual(info.project_name, "Script")
        self.assertEqual(info.oop_score, 0.0)


class TestAIResumeEntry(unittest.TestCase):
    """Tests for AIResumeEntry dataclass."""

    def test_all_fields_stored(self):
        """Verify dataclass stores all provided fields correctly."""
        entry = AIResumeEntry("Proj", "Summary.", "Detail.", ["Task"], ["Python"], "Flask", "Impact.")
        self.assertEqual(entry.project_title, "Proj")
        self.assertEqual(entry.key_responsibilities, ["Task"])

    def test_optional_defaults(self):
        """Confirm optional fields default to empty list or string."""
        entry = AIResumeEntry("Proj", "Summary.", "Detail.")
        self.assertEqual(entry.key_responsibilities, [])
        self.assertEqual(entry.tech_stack, "")


@patch(f"{MODULE}.runtimeAppContext")
class TestGenerateResumeAI_Ver2(unittest.TestCase):
    """Tests for GenerateResumeAI_Ver2 constructor and methods."""

    def test_init_stores_name_and_checks_db(self, mock_ctx):
        """Constructor stores project name and checks database for existence."""
        mock_ctx.store.project_exists.return_value = True
        gen = GenerateResumeAI_Ver2("test.json")
        self.assertEqual(gen.project_name, "test.json")
        self.assertTrue(gen.project_exists)
        self.assertIsNone(gen._chain)
        mock_ctx.store.project_exists.assert_called_once_with("test.json")

    def test_init_project_not_found(self, mock_ctx):
        """Handle non-existent projects by setting project_exists to False."""
        mock_ctx.store.project_exists.return_value = False
        gen = GenerateResumeAI_Ver2("missing.json")
        self.assertFalse(gen.project_exists)

    def test_init_no_api_key_required(self, mock_ctx):
        """API key is not required until generation is actually requested."""
        mock_ctx.store.project_exists.return_value = True
        with patch.dict("os.environ", {}, clear=True):
            gen = GenerateResumeAI_Ver2("test.json")
        self.assertIsNone(gen._chain)

    def test_get_info_returns_dataclass(self, mock_ctx):
        """Return properly populated ResumeProjectInfo from database."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = SAMPLE_DATA
        gen = GenerateResumeAI_Ver2("demo.json")
        result = gen.get_info_about_project()
        self.assertIsInstance(result, ResumeProjectInfo)
        self.assertEqual(result.project_name, "Demo App")
        self.assertEqual(gen.raw_project_data, SAMPLE_DATA)

    def test_get_info_returns_none_when_missing(self, mock_ctx):
        """Return None when project data is missing from database."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = None
        gen = GenerateResumeAI_Ver2("missing.json")
        self.assertIsNone(gen.get_info_about_project())

    def test_build_context_contains_fields(self, mock_ctx):
        """Context string includes all relevant project fields for LLM."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = SAMPLE_DATA
        gen = GenerateResumeAI_Ver2("demo.json")
        gen.get_info_about_project()
        context = gen._build_context_for_ai()
        for expected in ["Demo App", "Python", "Flask", "0.72", "high", "3 months", "Built REST API"]:
            self.assertIn(expected, context)

    def test_build_context_empty_when_no_data(self, mock_ctx):
        """Return empty string when no project data is available."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = None
        gen = GenerateResumeAI_Ver2("missing.json")
        self.assertEqual(gen._build_context_for_ai(), "")

    def test_build_context_not_detected_for_empty_lists(self, mock_ctx):
        """Show 'Not detected' for empty language/framework/skills lists."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = {
            "resume_item": {"project_name": "E", "languages": [], "frameworks": [],
                            "skills": [], "summary": "", "highlights": [],
                            "framework_sources": {}},
            "project_type": {"project_type": "individual"}, "duration_estimate": ""}
        gen = GenerateResumeAI_Ver2("empty.json")
        gen.get_info_about_project()
        self.assertIn("Not detected", gen._build_context_for_ai())

    def test_generate_returns_none_project_missing(self, mock_ctx):
        """Return None when project does not exist in database."""
        mock_ctx.store.project_exists.return_value = False
        gen = GenerateResumeAI_Ver2("missing.json")
        self.assertIsNone(gen.generate_AI_Resume_entry())

    def test_generate_returns_none_no_data(self, mock_ctx):
        """Return None when no analysis data is available."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = None
        gen = GenerateResumeAI_Ver2("empty.json")
        self.assertIsNone(gen.generate_AI_Resume_entry())

    def test_generate_returns_entry_on_success(self, mock_ctx):
        """Return AIResumeEntry with correct fields on successful generation."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = SAMPLE_DATA
        gen = GenerateResumeAI_Ver2("demo.json")
        gen._chain = MagicMock(invoke=MagicMock(return_value=LLM_RESPONSE))
        result = gen.generate_AI_Resume_entry()
        self.assertIsInstance(result, AIResumeEntry)
        self.assertEqual(result.project_title, "Task Manager")
        self.assertEqual(result.key_responsibilities, ["Designed API", "Implemented auth", "Tech Stack: Python, Flask, React"])
        self.assertEqual(result.tech_stack, "Python, Flask, React")

    def test_generate_passes_context_to_chain(self, mock_ctx):
        """Verify project context is passed to the LLM chain."""
        mock_ctx.store.project_exists.return_value = True
        mock_ctx.store.fetch_by_name.return_value = SAMPLE_DATA
        mock_chain = MagicMock(invoke=MagicMock(return_value=LLM_RESPONSE))
        gen = GenerateResumeAI_Ver2("demo.json")
        gen._chain = mock_chain
        gen.generate_AI_Resume_entry()
        call_args = mock_chain.invoke.call_args[0][0]
        self.assertIn("Demo App", call_args["project_data"])

    @patch(f"{MODULE}.ChatGoogleGenerativeAI")
    @patch(f"{MODULE}.os.getenv", return_value="fake-key")
    def test_chain_cached_after_first_call(self, _getenv, _llm, mock_ctx):
        """LLM chain is lazily initialized and cached after first call."""
        mock_ctx.store.project_exists.return_value = True
        gen = GenerateResumeAI_Ver2("demo.json")
        self.assertIs(gen._get_chain(), gen._get_chain())
        self.assertEqual(_llm.call_count, 1)

    def test_chain_raises_without_api_key(self, mock_ctx):
        """Raise RuntimeError when GOOGLE_API_KEY is missing."""
        mock_ctx.store.project_exists.return_value = True
        gen = GenerateResumeAI_Ver2("demo.json")
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                gen._get_chain()


if __name__ == "__main__":
    unittest.main()
