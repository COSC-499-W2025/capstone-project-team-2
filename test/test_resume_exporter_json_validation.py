"""
Test Suite: Resume Exporter JSON Validation

This suite ensures that resume export functionality:
- Generates valid JSON
- Contains required fields for each project
- Produces deterministic results across runs (except timestamp)
- Works via the CLI entry point
- Optionally validates against JSON schema if the library is installed

These tests verify data stability and correctness for automated résumé generation.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from subprocess import run, PIPE

from src.resume_exporter import export_resume_items


def _is_iso8601_with_tz(value: str) -> bool:
    """Return True if value is an ISO8601 timestamp including timezone info."""
    try:
        dt = datetime.fromisoformat(value)
        return dt.tzinfo is not None
    except ValueError:
        return False


def _sorted_copy(seq):
    """Utility: return sorted list copy if input is a list."""
    return sorted(seq) if isinstance(seq, list) else seq


class TestResumeExporterJSONValidation(unittest.TestCase):
    """End-to-end validation of JSON output integrity and format."""

    def setUp(self) -> None:
        print("\n[Resume JSON Test] Setting up temporary test workspace...", flush=True)

        # Create a temporary workspace simulating multiple project folders
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Simulated Python + Flask project
        alpha = self.root / "alpha"
        alpha.mkdir(parents=True, exist_ok=True)
        (alpha / "app.py").write_text("print('hello')", encoding="utf-8")
        (alpha / "requirements.txt").write_text("Flask==2.3.2\n", encoding="utf-8")

        # Empty project to trigger fallback behavior
        (self.root / "beta").mkdir(parents=True, exist_ok=True)

        # Output JSON path
        self.output_path = self.root / "resume_items.json"

    def tearDown(self) -> None:
        print("[Resume JSON Test] Cleaning up temporary workspace.\n", flush=True)
        self.temp_dir.cleanup()

    def test_json_structure_and_content(self) -> None:
        """Verify JSON contains required fields and correct project details."""
        print("[Resume JSON Test] Validating JSON structure and content...", flush=True)

        exported = export_resume_items(self.root, self.output_path)
        payload = json.loads(exported.read_text())

        # Validate top-level keys
        self.assertIn("generated_at", payload)
        self.assertTrue(_is_iso8601_with_tz(payload["generated_at"]))
        self.assertEqual(payload["root"], str(self.root.resolve()))
        self.assertEqual(len(payload["projects"]), 2)

        # Identify entries
        alpha = next(p for p in payload["projects"] if p["project_name"] == "alpha")
        beta = next(p for p in payload["projects"] if p["project_name"] == "beta")

        # Alpha expected to show Flask
        self.assertIn("Flask", alpha["frameworks"])
        self.assertTrue(any("Flask" in h for h in alpha["highlights"]))

        # Beta expected to have fallback messaging
        self.assertIn(
            "Documented project insights ready for résumé inclusion.",
            beta["highlights"],
        )

    def test_deterministic_output(self) -> None:
        """Ensure repeated runs produce the same JSON content except timestamp."""
        print("[Resume JSON Test] Checking deterministic JSON output...", flush=True)

        first = json.loads(export_resume_items(self.root, self.output_path).read_text())
        second = json.loads(export_resume_items(self.root, self.output_path).read_text())

        first.pop("generated_at", None)
        second.pop("generated_at", None)
        self.assertEqual(first, second)

    def test_cli_behavior(self) -> None:
        """Ensure CLI invocation writes valid JSON file."""
        print("[Resume JSON Test] Verifying CLI export functionality...", flush=True)

        cmd = [sys.executable, "-m", "src.resume_exporter", str(self.root), "-o", str(self.output_path)]
        proc = run(cmd, stdout=PIPE, stderr=PIPE, text=True)

        self.assertEqual(proc.returncode, 0, f"CLI failed: {proc.stderr}")
        payload = json.loads(self.output_path.read_text())
        self.assertIn("projects", payload)

    def test_dataclass_field_compatibility(self) -> None:
        """Ensure JSON contains expected ResumeItem-like structure."""
        print("[Resume JSON Test] Checking field compatibility with resume data model...", flush=True)

        export_resume_items(self.root, self.output_path)
        payload = json.loads(self.output_path.read_text())

        self.assertIsInstance(payload["projects"], list)
        for project in payload["projects"]:
            self.assertIn("project_name", project)
            self.assertIn("highlights", project)
            self.assertIn("framework_sources", project)

    def test_optional_jsonschema(self) -> None:
        """
        If jsonschema is installed, validate structure against a minimal schema.
        This test is optional and skipped if jsonschema is not available.
        """
        print("[Resume JSON Test] Checking optional JSON Schema validation...", flush=True)

        try:
            import jsonschema
        except ModuleNotFoundError:
            print("[Resume JSON Test] jsonschema not installed — skipping schema validation.", flush=True)
            self.skipTest("jsonschema not installed")

        export_resume_items(self.root, self.output_path)
        payload = json.loads(self.output_path.read_text())

        schema = {
            "type": "object",
            "required": ["generated_at", "root", "projects"]
        }

        jsonschema.validate(payload, schema)
        print("[Resume JSON Test] Schema validation successful.", flush=True)


if __name__ == "__main__":
    unittest.main()
