"""
Test Suite: Resume Item Generator

Covers:
- Python + Flask project detection
- Git-based collaboration classification
- Fallback behavior for empty projects
- Deterministic skill ordering

Print statements are included to provide clear progress messages in terminal logs.
"""

import gc
import tempfile
import time
import unittest
from pathlib import Path

from git import Actor, Repo

from src.resume_item_generator import ResumeItem, generate_resume_item


class TestResumeItemGenerator(unittest.TestCase):
    """Exercise résumé item generation across representative scenarios."""

    def setUp(self) -> None:
        print("\n[ResumeItem Tests] Setting up temporary project root...", flush=True)
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        print("[ResumeItem Tests] Tearing down temporary project root.\n", flush=True)
        gc.collect()
        time.sleep(0.05)
        self.temp_dir.cleanup()

    def _write(self, relative_path: str, content: str) -> Path:
        """Helper: write a file within the temporary project root."""
        path = self.project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def _announce(self, message: str) -> None:
        """Helper: print readable progress banners to terminal output."""
        print(f"[ResumeItem Tests] {message}", flush=True)

    def test_generates_python_resume_item(self) -> None:
        """Validate summary/highlights for a simple Python + Flask project."""
        self._announce("Generating résumé item for Python + Flask project.")
        # Minimal Flask project to trigger language/framework detection.
        self._write("app.py", "print('hello')")
        self._write("requirements.txt", "Flask==2.3.2\nrequests==2.32.0\n")

        # Generate résumé item for the synthetic project.
        resume_item = generate_resume_item(self.project_root, project_name="Portfolio Dashboard")

        self.assertIsInstance(resume_item, ResumeItem)
        self.assertEqual(resume_item.project_name, "Portfolio Dashboard")

        # Languages/frameworks are sorted and detected.
        self.assertEqual(resume_item.languages, ["Python"])
        self.assertEqual(resume_item.frameworks, ["Flask"])

        # Summary contains persona verb and project name.
        self.assertIn("Built Portfolio Dashboard", resume_item.summary)

        # Highlight order: stack note, then skills.
        self.assertTrue(resume_item.highlights[0].startswith("Implemented core functionality"))
        self.assertTrue(resume_item.highlights[1].startswith("Demonstrated skills"))

        # Technologies and skills appear as expected.
        self.assertTrue(any("Flask" in highlight for highlight in resume_item.highlights))
        self.assertIn("Python", resume_item.skills)
        self.assertIn("Flask", resume_item.skills)
        self.assertIn("Web Development", resume_item.skills)

        # Non-Git projects should end the highlight list with the skills call-out.
        self.assertTrue(resume_item.highlights[-1].startswith("Demonstrated skills"))

    def test_collaborative_highlight_and_git_context(self) -> None:
        """Ensure Git history with multiple authors sets collaboration cues."""
        self._announce("Detecting collaborative signals from Git commit history.")
        repo = Repo.init(self.project_root)
        self.addCleanup(repo.close)

        # Two commits with unique authors to produce a collaborative Git history.
        file_path = self._write("main.py", "print('v1')")
        relative_path = file_path.relative_to(self.project_root)
        repo.index.add([str(relative_path)])

        author1 = Actor("Alice", "alice@example.com")
        author2 = Actor("Bob", "bob@example.com")

        repo.index.commit("Initial commit", author=author1, committer=author1)
        file_path.write_text("print('v2')", encoding="utf-8")
        repo.index.add([str(relative_path)])
        repo.index.commit("Second commit", author=author2, committer=author2)

        # Detect résumé item directly from the Git repo root.
        resume_item = generate_resume_item(self.project_root)

        self.assertEqual(resume_item.project_type, "collaborative")
        self.assertEqual(resume_item.detection_mode, "git")
        self.assertTrue(resume_item.summary.startswith("Collaborated"))
        self.assertTrue(any("Git" in highlight for highlight in resume_item.highlights))
        self.assertIn("Python", resume_item.languages)

        # Git note should be last highlight (after stack + skills).
        self.assertTrue(resume_item.highlights[-1].endswith("in Git."))

    def test_no_stack_no_skills_fallback(self) -> None:
        """Graceful fallback when no detectable signals are present."""
        self._announce("Falling back when no languages/frameworks/skills detected.")
        # Empty directory should fall back to boilerplate messaging.
        resume_item = generate_resume_item(self.project_root, project_name="EmptyProject")

        # Summary verb can be "Built" (individual) or "Developed" (unknown),
        # depending on project type inference. Accept either to avoid flakiness.
        self.assertIn(resume_item.summary, {"Developed EmptyProject.", "Built EmptyProject."})

        self.assertEqual(
            resume_item.highlights,
            ["Documented project insights ready for résumé inclusion."],
        )

    def test_skills_are_sorted_for_determinism(self) -> None:
        """
        Whatever identify_skills() returns, generator should sort it for stability.
        """
        self._announce("Ensuring skills list remains sorted for determinism.")
        self._write("script.py", "print('ok')")

        # Ensure sorted output regardless of identify_skills ordering.
        resume_item = generate_resume_item(self.project_root, project_name="Sorter")
        self.assertEqual(resume_item.skills, sorted(resume_item.skills))


if __name__ == "__main__":
    unittest.main()
