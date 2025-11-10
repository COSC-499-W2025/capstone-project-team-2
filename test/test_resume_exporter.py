"""
Test Suite: Resume Exporter

Covers high-level behavior of the resume exporter:
- Discovery of project directories
- Construction of ResumeItem dataclasses
- Writing a JSON export to disk and validating content

This suite focuses on functional behavior; for schema and determinism checks,
see `test_resume_exporter_json_validation.py`.

Print statements included for clarity during test runs.
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.resume_exporter import (
    build_resume_items,
    discover_projects,
    export_resume_items,
)
from src.resume_item_generator import ResumeItem


class TestResumeExporter(unittest.TestCase):
    """End-to-end checks for project discovery and résumé export JSON."""

    def setUp(self) -> None:
        print("\n[Resume Exporter Tests] Setting up test workspace...", flush=True)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        print("[Resume Exporter Tests] Cleaning up test workspace.\n", flush=True)
        self.temp_dir.cleanup()

    def _create_project(self, name: str) -> Path:
        """Helper to create a directory representing a project."""
        project_dir = self.root / name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def _announce(self, message: str) -> None:
        """Print a test step for clarity."""
        print(f"[Resume Exporter Tests] {message}", flush=True)

    def test_discover_projects_skips_hidden_and_files(self) -> None:
        """Only non-hidden directories should be treated as projects."""
        self._announce("Discovering visible project directories...")

        self._create_project("alpha")
        self._create_project("beta")
        hidden = self._create_project(".git")
        hidden.touch(exist_ok=True)   # Ensure no failure if dir exists as a file
        (self.root / "notes.txt").write_text("hello", encoding="utf-8")

        discovered = discover_projects(self.root)
        self.assertEqual([p.name for p in discovered], ["alpha", "beta"])

    def test_export_resume_items_writes_json_payload(self) -> None:
        """JSON export should include expected project data."""
        self._announce("Exporting projects to JSON...")

        alpha = self._create_project("alpha")
        (alpha / "app.py").write_text("print('hello')", encoding="utf-8")
        (alpha / "requirements.txt").write_text("Flask==2.3.2\n", encoding="utf-8")

        self._create_project("beta")

        output_path = self.root / "resume.json"
        written_path = export_resume_items(self.root, output_path)

        self.assertEqual(written_path, output_path.resolve())
        payload = json.loads(written_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["root"], str(self.root.resolve()))
        self.assertEqual(len(payload["projects"]), 2)

        names = [project["project_name"] for project in payload["projects"]]
        self.assertEqual(names, ["alpha", "beta"])

        alpha_payload = payload["projects"][0]
        self.assertIn("Flask", alpha_payload["frameworks"])
        self.assertTrue(any("Flask" in h for h in alpha_payload["highlights"]))

        beta_payload = payload["projects"][1]
        self.assertEqual(
            beta_payload["highlights"],
            ["Documented project insights ready for résumé inclusion."],
        )

    def test_build_resume_items_returns_dataclasses(self) -> None:
        """Resume items should be instances of the ResumeItem dataclass."""
        self._announce("Building ResumeItem dataclasses...")

        alpha = self._create_project("alpha")
        (alpha / "main.py").write_text("print('hi')", encoding="utf-8")

        items = build_resume_items(self.root)
        self.assertTrue(items)
        self.assertIsInstance(items[0], ResumeItem)


if __name__ == "__main__":
    unittest.main()
