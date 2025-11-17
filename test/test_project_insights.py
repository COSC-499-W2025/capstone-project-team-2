"""
Test Suite: Project Insights

Covers:
- Recording insights from analysis dictionaries
- Chronological listing for projects
- Contribution-based ranking (global and per contributor)
"""

import gc
import json
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.project_insights import (
    list_project_insights,
    rank_projects_by_contribution,
    record_project_insight,
)


def _analysis_payload(
    project_name: str = "Demo",
    *,
    summary: str = "Built Demo.",
    languages=None,
    frameworks=None,
    skills=None,
) -> dict:
    """
    Build a synthetic analysis payload shaped like analyze_project() output
    so we can exercise record_project_insight() in isolation.
    """
    languages = languages or ["Python"]
    frameworks = frameworks or ["Flask"]
    skills = skills or ["Python", "Flask"]
    hierarchy = {"name": project_name, "children": []}
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
        print("\n[ProjectInsights Tests] Setting up temporary storage...", flush=True)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = Path(self.temp_dir.name) / "insights.json"

    def tearDown(self) -> None:
        print("[ProjectInsights Tests] Tearing down temporary storage.\n", flush=True)
        gc.collect()
        time.sleep(0.05)
        self.temp_dir.cleanup()

    def _announce(self, message: str) -> None:
        """Helper: print readable progress banners to terminal output."""
        print(f"[ProjectInsights Tests] {message}", flush=True)

    def test_record_and_list_project_insights(self) -> None:
        """Record an insight and verify it is persisted and loadable."""
        self._announce("Recording a single insight and listing stored entries.")

        contributors = {
            "Alice": {"file_count": 4},
            "Bob": {"files_owned": ["a.py", "b.py"]},
        }

        insight = record_project_insight(
            _analysis_payload("Alpha"),
            storage_path=self.storage,
            contributors=contributors,
            insight_id="alpha-1",
        )

        self.assertEqual(insight.project_name, "Alpha")
        self.assertTrue(self.storage.exists())

        disk_data = json.loads(self.storage.read_text(encoding="utf-8"))
        self.assertEqual(len(disk_data), 1)

        listed = list_project_insights(self.storage)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].contributors["Bob"]["file_count"], 2)
        self.assertEqual(listed[0].stats["total_file_contributions"], 6)

    def test_list_project_insights_returns_chronological_records(self) -> None:
        """Ensure projects are ordered by analyzed_at, not insertion order."""
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

        # Chronological ordering should place Beta first because ts1 < ts2
        self.assertEqual(projects[0].project_name, "Beta")
        self.assertEqual(projects[1].project_name, "Alpha")

    def test_rank_projects_by_contribution(self) -> None:
        """Rank projects globally and per contributor based on file_count."""
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

        ranked = rank_projects_by_contribution(storage_path=self.storage)
        self.assertEqual([item.project_name for item in ranked], ["Delta", "Gamma"])

        ranked_user = rank_projects_by_contribution(
            storage_path=self.storage,
            contributor="User",
        )
        self.assertEqual([item.project_name for item in ranked_user], ["Gamma", "Delta"])

    def test_rank_projects_by_contribution_top_n_zero(self) -> None:
        """Ensure top_n=0 returns an empty list instead of all entries."""
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

        # With None we should see all entries.
        self.assertEqual(len(ranked_none), 2)
        # With 0 or negative, we should see no entries.
        self.assertEqual(len(ranked_zero), 0)
        self.assertEqual(len(ranked_negative), 0)

    def test_corrupted_storage_is_preserved_before_rewrite(self) -> None:
        """If the JSON log is corrupted, stash it before writing new data."""
        self._announce("Preserving corrupted insight logs before rewriting.")

        record_project_insight(
            _analysis_payload("Omega"),
            storage_path=self.storage,
            insight_id="omega-1",
        )

        # Corrupt the JSON file between writes.
        self.storage.write_text("not-json", encoding="utf-8")

        record_project_insight(
            _analysis_payload("Omega 2"),
            storage_path=self.storage,
            insight_id="omega-2",
        )

        backups = list(self.storage.parent.glob("insights.json.corrupt-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "not-json")

        disk_data = json.loads(self.storage.read_text(encoding="utf-8"))
        self.assertEqual(len(disk_data), 1)
        self.assertEqual(disk_data[0]["id"], "omega-2")


if __name__ == "__main__":
    unittest.main()
