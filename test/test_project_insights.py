"""
Test Suite: Project Insights

Covers:
- Recording insights from analysis dictionaries
- Chronological listing for projects
- Contribution-based ranking (global and per contributor)
"""

import gc
import json
import logging
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.project_insights import (
    list_project_insights,
    list_skill_history,
    rank_projects_by_contribution,
    record_project_insight,
    summaries_for_top_ranked_projects,
)

logger = logging.getLogger("ProjectInsightsTests")
logger.addHandler(logging.NullHandler())
logger.propagate = False


def _analysis_payload(
    project_name: str = "Demo",
    *,
    summary: str = "Built Demo.",
    languages=None,
    frameworks=None,
    skills=None,
    hierarchy=None,
) -> dict:
    """
    Helper for building realistic, but fake, analysis payloads.
    Makes it easier to write clean tests.
    """
    languages = languages or ["Python"]
    frameworks = frameworks or ["Flask"]
    skills = skills or ["Python", "Flask"]
    hierarchy = hierarchy or {
        "name": project_name,
        "type": "DIR",
        "children": [
            {
                "name": f"{project_name}.py",
                "type": "PY",
                "size": 512,
                "created": "2024-01-01 00:00:00",
                "modified": "2024-01-01 00:00:00",
                "children": [],
            }
        ],
    }
    return {
        "project_root": f"/tmp/{project_name}",
        "hierarchy": hierarchy,
        "duration_estimate": "5 days",
        "resume_item": {
            "project_name": project_name,
            "summary": summary,
            "languages": languages,
            "frameworks": frameworks,
            "skills": skills,
            "project_type": "collaborative",
            "detection_mode": "git",
        },
    }


class TestProjectInsights(unittest.TestCase):
    """Exercise persistence, timelines, and ranking for project insights."""

    def setUp(self) -> None:
        logger.info("Setting up temporary storage...")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "insights.json"

    def tearDown(self) -> None:
        logger.info("Tearing down temporary storage.")
        gc.collect()
        time.sleep(0.05)
        self.temp_dir.cleanup()

    def _announce(self, message: str) -> None:
        """Tiny helper for readable logs."""
        logger.info(message)

    def test_record_and_list_project_insights(self) -> None:
        """Record an insight and verify it is persisted and loadable."""
        self._announce("Recording a single insight and listing stored entries.")

        contributors = {
            "Alice": {"file_count": 4},
            "Bob": {"files_owned": ["a.py", "b.py"]},
        }

        insight = record_project_insight(
            _analysis_payload(
                "Alpha",
                languages=["Python", "C"],
                frameworks=["Flask", "Django"],
            ),
            storage_path=self.storage,
            contributors=contributors,
            insight_id="alpha-1",
        )

        # Basic checks to make sure persistence and normalization happened correctly
        self.assertEqual(insight.project_name, "Alpha")
        self.assertTrue(self.storage.exists())

        # Verify the JSON file was written with correct structure
        disk_data = json.loads(self.storage.read_text(encoding="utf-8"))
        self.assertEqual(len(disk_data), 1)

        # Verify file analysis fields were computed
        self.assertGreaterEqual(insight.file_analysis["file_count"], 1)
        self.assertIn("total_size_bytes", insight.file_analysis)
        self.assertIn("largest_file", insight.file_analysis)

        # Verify loaded insights have sorted/normalized data
        listed = list_project_insights(self.storage)
        self.assertEqual(listed[0].skills, ["Flask", "Python"])
        self.assertEqual(listed[0].languages, ["C", "Python"])
        self.assertEqual(listed[0].frameworks, ["Django", "Flask"])
        self.assertEqual(len(listed), 1)

        # Verify contributor data was normalized correctly
        self.assertEqual(listed[0].contributors["Bob"]["file_count"], 2)
        self.assertEqual(listed[0].stats["total_file_contributions"], 6)

    def test_list_project_insights_returns_chronological_records(self) -> None:
        """Ensure projects are ordered by analyzed_at timestamp."""
        self._announce("Building a chronological project list.")

        ts1 = datetime(2025, 2, 10, tzinfo=timezone.utc)
        ts2 = ts1 + timedelta(hours=1)

        record_project_insight(
            _analysis_payload("Alpha", skills=["Python"]),
            storage_path=self.storage,
            analyzed_at=ts2,
            insight_id="alpha",
        )
        record_project_insight(
            _analysis_payload("Beta", skills=["Go"]),
            storage_path=self.storage,
            analyzed_at=ts1,
            insight_id="beta",
        )

        projects = list_project_insights(self.storage)
        self.assertEqual(len(projects), 2)

        # Beta should appear first since it has the earlier timestamp
        self.assertEqual(projects[0].project_name, "Beta")
        self.assertEqual(projects[1].project_name, "Alpha")

    def test_rank_projects_by_contribution(self) -> None:
        """Rank projects by total contributor impact."""
        self._announce("Ranking projects by contribution strength.")

        record_project_insight(
            _analysis_payload("Gamma"),
            storage_path=self.storage,
            contributors={"User": {"file_count": 10}},
            insight_id="gamma",
        )
        record_project_insight(
            _analysis_payload("Delta"),
            storage_path=self.storage,
            contributors={"User": {"file_count": 3}, "Peer": {"file_count": 20}},
            insight_id="delta",
        )

        # Global ranking should favor Delta (Peer's 20 > User's 10 in Gamma)
        ranked = rank_projects_by_contribution(storage_path=self.storage)
        self.assertEqual([item.project_name for item in ranked], ["Delta", "Gamma"])

        # When ranking by specific contributor (User), Gamma wins (10 > 3)
        ranked_user = rank_projects_by_contribution(
            storage_path=self.storage,
            contributor="User",
        )
        self.assertEqual([item.project_name for item in ranked_user], ["Gamma", "Delta"])

    def test_rank_projects_by_contribution_top_n_zero(self) -> None:
        """top_n=0 should yield an empty result instead of all items."""
        self._announce("Verifying top_n=0 returns an empty ranking.")

        record_project_insight(
            _analysis_payload("Theta"),
            storage_path=self.storage,
            contributors={"User": {"file_count": 1}},
            insight_id="theta",
        )
        record_project_insight(
            _analysis_payload("Iota"),
            storage_path=self.storage,
            contributors={"User": {"file_count": 2}},
            insight_id="iota",
        )

        ranked_none = rank_projects_by_contribution(storage_path=self.storage, top_n=None)
        ranked_zero = rank_projects_by_contribution(storage_path=self.storage, top_n=0)
        ranked_negative = rank_projects_by_contribution(storage_path=self.storage, top_n=-5)

        # None should return all, but 0 or negative should return empty list
        self.assertEqual(len(ranked_none), 2)
        self.assertEqual(len(ranked_zero), 0)
        self.assertEqual(len(ranked_negative), 0)

    def test_list_skill_history_returns_chronological_skills(self) -> None:
        """Check that skill history is ordered and contains correct info."""
        self._announce("Building chronological skill history.")

        ts1 = datetime(2025, 5, 1, tzinfo=timezone.utc)
        ts2 = ts1 + timedelta(days=1)

        record_project_insight(
            _analysis_payload("SkillA", skills=["Python"]),
            storage_path=self.storage,
            analyzed_at=ts2,
            insight_id="skill-a",
        )
        record_project_insight(
            _analysis_payload("SkillB", skills=["Go", "Docker"]),
            storage_path=self.storage,
            analyzed_at=ts1,
            insight_id="skill-b",
        )

        history = list_skill_history(self.storage)

        # Should be ordered chronologically (SkillB first, then SkillA)
        self.assertEqual([entry["project_name"] for entry in history], ["SkillB", "SkillA"])
        # Skills should be sorted alphabetically
        self.assertEqual(history[0]["skills"], ["Docker", "Go"])
        # skill_count should match the number of skills
        self.assertEqual(history[1]["skill_count"], 1)

    def test_summaries_for_top_ranked_projects(self) -> None:
        """Validate summary extraction for top-ranked projects."""
        self._announce("Retrieving top project summaries.")

        record_project_insight(
            _analysis_payload("TopDog", summary="Did great things."),
            storage_path=self.storage,
            contributors={"Lead": {"file_count": 12}},
            insight_id="topdog",
        )
        record_project_insight(
            _analysis_payload("RunnerUp", summary="Also solid."),
            storage_path=self.storage,
            contributors={"Lead": {"file_count": 2}},
            insight_id="runner",
        )

        summaries = summaries_for_top_ranked_projects(
            storage_path=self.storage,
            top_n=1,
        )

        # Only the top project should be returned
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["project_name"], "TopDog")
        self.assertEqual(summaries[0]["summary"], "Did great things.")

        # Verify all expected fields are present
        self.assertIn("top_contribution_count", summaries[0])
        self.assertIn("contributors", summaries[0])
        self.assertIn("score", summaries[0])
        self.assertGreater(summaries[0]["score"], 0)

    def test_corrupted_storage_is_preserved_before_rewrite(self) -> None:
        """Ensure corrupted logs get saved aside before being replaced."""
        self._announce("Preserving corrupted insight logs before rewriting.")

        record_project_insight(
            _analysis_payload("Omega"),
            storage_path=self.storage,
            insight_id="omega-1",
        )

        # Force corruption by writing invalid JSON
        self.storage.write_text("not-json", encoding="utf-8")

        record_project_insight(
            _analysis_payload("Omega 2"),
            storage_path=self.storage,
            insight_id="omega-2",
        )

        # Corrupted file should have been stashed with a timestamped backup name
        backups = list(self.storage.parent.glob("insights.json.corrupt-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "not-json")

        # Fresh log should contain only the new record
        disk_data = json.loads(self.storage.read_text(encoding="utf-8"))
        self.assertEqual(len(disk_data), 1)
        self.assertEqual(disk_data[0]["id"], "omega-2")

    def test_non_list_storage_is_stashed(self) -> None:
        """Valid JSON but wrong shape should still be treated as corrupted."""
        self._announce("Stashing non-list JSON payloads.")

        # Write valid JSON that isn't a list
        self.storage.write_text(json.dumps({"unexpected": "data"}), encoding="utf-8")

        # Should return empty list and stash the corrupted file
        projects = list_project_insights(self.storage)
        self.assertEqual(projects, [])

        # Verify backup was created
        backups = list(self.storage.parent.glob("insights.json.corrupt-*"))
        self.assertEqual(len(backups), 1)


if __name__ == "__main__":
    unittest.main()
