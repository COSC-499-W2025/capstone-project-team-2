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

from src.reporting.project_insights import (
    group_project_histories,
    list_project_insights,
    list_skill_history,
    summarize_top_project_histories,
    summarize_project_evolution,
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

    def test_rank_projects_by_contribution_uses_git_percentage(self) -> None:
        """Git-based commit data should rank by percentage before raw commit volume."""
        self._announce("Ranking git projects using contribution percentages.")

        record_project_insight(
            _analysis_payload("HighPct"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 20, "percentage": "80.00%"}},
            insight_id="high-pct",
        )
        record_project_insight(
            _analysis_payload("LowPct"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 60, "percentage": "60.00%"}},
            insight_id="low-pct",
        )

        ranked = rank_projects_by_contribution(storage_path=self.storage, contributor="Alice")
        self.assertEqual([item.project_name for item in ranked], ["HighPct", "LowPct"])

        listed = list_project_insights(self.storage)
        stats_by_name = {item.project_name: item.stats for item in listed}
        self.assertEqual(stats_by_name["HighPct"]["contribution_metric"], "commits")
        self.assertEqual(stats_by_name["LowPct"]["contribution_metric"], "commits")

    def test_list_project_insights_preserves_git_commit_counts_on_reload(self) -> None:
        """Reloading stored insights should not overwrite commit-based contribution counts with file_count=0."""
        self._announce("Preserving git commit-based contribution metrics across reload.")

        record_project_insight(
            _analysis_payload("ReloadGit"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 20, "percentage": "80.00%"}},
            insight_id="reload-git",
        )

        loaded = list_project_insights(self.storage)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].contribution_count("Alice"), 20)
        self.assertEqual(loaded[0].contribution_metric("Alice"), "commits")
        self.assertEqual(loaded[0].contribution_score("Alice"), 80.0)

    def test_rank_projects_by_contribution_uses_git_commit_count_overall(self) -> None:
        """Overall git ranking should use top raw commit count when no contributor is selected."""
        self._announce("Ranking git projects overall using commit volume.")

        record_project_insight(
            _analysis_payload("MoreCommits"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 25, "percentage": "55.00%"}},
            insight_id="more-commits",
        )
        record_project_insight(
            _analysis_payload("FewerCommits"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 12, "percentage": "90.00%"}},
            insight_id="fewer-commits",
        )

        ranked = rank_projects_by_contribution(storage_path=self.storage)
        self.assertEqual([item.project_name for item in ranked], ["MoreCommits", "FewerCommits"])

    def test_rank_projects_by_contribution_falls_back_to_raw_count_without_percentage(self) -> None:
        """Contributor-specific ranking should fall back to raw counts when percentage is absent."""
        self._announce("Ranking contributor-specific projects without percentages.")

        record_project_insight(
            _analysis_payload("HigherCount"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 9}},
            insight_id="higher-count",
        )
        record_project_insight(
            _analysis_payload("LowerCount"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 4}},
            insight_id="lower-count",
        )

        ranked = rank_projects_by_contribution(storage_path=self.storage, contributor="Alice")
        self.assertEqual([item.project_name for item in ranked], ["HigherCount", "LowerCount"])

    def test_rank_projects_by_contribution_returns_zero_for_missing_contributor(self) -> None:
        """Contributor-filtered ranking should not fall back to unrelated top contributors."""
        self._announce("Excluding projects that do not contain the requested contributor.")

        record_project_insight(
            _analysis_payload("HasAlice"),
            storage_path=self.storage,
            contributors={"Alice": {"file_count": 5}},
            insight_id="has-alice",
        )
        record_project_insight(
            _analysis_payload("OnlyBob"),
            storage_path=self.storage,
            contributors={"Bob": {"file_count": 20}},
            insight_id="only-bob",
        )

        ranked = rank_projects_by_contribution(storage_path=self.storage, contributor="Alice")
        by_name = {item.project_name: item for item in ranked}

        self.assertEqual(by_name["HasAlice"].contribution_score("Alice"), 5.0)
        self.assertEqual(by_name["OnlyBob"].contribution_score("Alice"), 0.0)
        self.assertLess(by_name["OnlyBob"].contribution_score("Alice"), by_name["HasAlice"].contribution_score("Alice"))

    def test_rank_projects_by_contribution_breaks_equal_percentages_by_count(self) -> None:
        """Equal percentages should be ordered by higher raw contribution count."""
        self._announce("Breaking equal contribution percentages by count.")

        record_project_insight(
            _analysis_payload("LowerTieBreak"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 6, "percentage": "50.00%"}},
            insight_id="lower-tiebreak",
        )
        record_project_insight(
            _analysis_payload("HigherTieBreak"),
            storage_path=self.storage,
            contributors={"Alice": {"commit_count": 18, "percentage": "50.00%"}},
            insight_id="higher-tiebreak",
        )

        ranked = rank_projects_by_contribution(storage_path=self.storage, contributor="Alice")
        self.assertEqual([item.project_name for item in ranked], ["HigherTieBreak", "LowerTieBreak"])

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

    def test_summarize_project_evolution_single_snapshot(self) -> None:
        """Single-snapshot projects should produce a minimal evolution summary."""
        self._announce("Summarizing evolution for a single project snapshot.")

        record_project_insight(
            _analysis_payload("Solo", skills=["Python", "Testing"]),
            storage_path=self.storage,
            analyzed_at=datetime(2025, 5, 1, tzinfo=timezone.utc),
            insight_id="solo-1",
        )

        history = [item for item in list_project_insights(self.storage) if item.project_name == "Solo"]
        summary = summarize_project_evolution(history)

        self.assertEqual(summary["project_name"], "Solo")
        self.assertEqual(summary["snapshot_count"], 1)
        self.assertEqual(summary["new_skills"], [])
        self.assertEqual(summary["new_languages"], [])
        self.assertEqual(summary["file_count_delta"], 0)
        self.assertFalse(summary["summary_changed"])
        self.assertFalse(summary["project_type_changed"])

    def test_summarize_project_evolution_detects_growth_between_snapshots(self) -> None:
        """Later snapshots should surface added skills, languages, and file-count growth."""
        self._announce("Summarizing evolution across multiple project snapshots.")

        ts1 = datetime(2025, 5, 1, tzinfo=timezone.utc)
        ts2 = ts1 + timedelta(days=7)

        early_hierarchy = {
            "name": "Evolving",
            "type": "DIR",
            "children": [
                {
                    "name": "main.py",
                    "type": "PY",
                    "size": 256,
                    "created": "2024-01-01 00:00:00",
                    "modified": "2024-01-01 00:00:00",
                    "children": [],
                }
            ],
        }
        later_hierarchy = {
            "name": "Evolving",
            "type": "DIR",
            "children": [
                {
                    "name": "main.py",
                    "type": "PY",
                    "size": 256,
                    "created": "2024-01-01 00:00:00",
                    "modified": "2024-01-01 00:00:00",
                    "children": [],
                },
                {
                    "name": "worker.ts",
                    "type": "TS",
                    "size": 128,
                    "created": "2024-01-02 00:00:00",
                    "modified": "2024-01-02 00:00:00",
                    "children": [],
                },
                {
                    "name": "README.md",
                    "type": "MD",
                    "size": 64,
                    "created": "2024-01-03 00:00:00",
                    "modified": "2024-01-03 00:00:00",
                    "children": [],
                },
            ],
        }

        record_project_insight(
            _analysis_payload(
                "Evolving",
                summary="Initial prototype.",
                languages=["Python"],
                skills=["Python", "Testing"],
                hierarchy=early_hierarchy,
            ),
            storage_path=self.storage,
            analyzed_at=ts1,
            insight_id="evolving-1",
        )
        record_project_insight(
            _analysis_payload(
                "Evolving",
                summary="Expanded into a multi-language workflow.",
                languages=["Python", "TypeScript"],
                skills=["Python", "Testing", "CI/CD", "TypeScript"],
                hierarchy=later_hierarchy,
            ),
            storage_path=self.storage,
            analyzed_at=ts2,
            insight_id="evolving-2",
        )

        history = [item for item in list_project_insights(self.storage) if item.project_name == "Evolving"]
        summary = summarize_project_evolution(history)

        self.assertEqual(summary["snapshot_count"], 2)
        self.assertEqual(summary["first_analyzed_at"], ts1.isoformat())
        self.assertEqual(summary["latest_analyzed_at"], ts2.isoformat())
        self.assertEqual(summary["new_skills"], ["CI/CD", "TypeScript"])
        self.assertEqual(summary["new_languages"], ["TypeScript"])
        self.assertEqual(summary["file_count_delta"], 2)
        self.assertTrue(summary["summary_changed"])
        self.assertFalse(summary["project_type_changed"])

    def test_group_project_histories_groups_snapshots_by_name(self) -> None:
        """Snapshots with the same project name should be grouped together chronologically."""
        self._announce("Grouping snapshots into per-project histories.")

        ts1 = datetime(2025, 5, 1, tzinfo=timezone.utc)
        ts2 = ts1 + timedelta(days=1)
        ts3 = ts1 + timedelta(days=2)

        record_project_insight(
            _analysis_payload("Alpha", summary="First alpha snapshot."),
            storage_path=self.storage,
            analyzed_at=ts2,
            insight_id="alpha-2",
        )
        record_project_insight(
            _analysis_payload("Beta", summary="Only beta snapshot."),
            storage_path=self.storage,
            analyzed_at=ts3,
            insight_id="beta-1",
        )
        record_project_insight(
            _analysis_payload("Alpha", summary="Initial alpha snapshot."),
            storage_path=self.storage,
            analyzed_at=ts1,
            insight_id="alpha-1",
        )

        grouped = group_project_histories(storage_path=self.storage)

        self.assertEqual(sorted(grouped.keys()), ["Alpha", "Beta"])
        self.assertEqual([item.id for item in grouped["Alpha"]], ["alpha-1", "alpha-2"])
        self.assertEqual([item.id for item in grouped["Beta"]], ["beta-1"])

    def test_group_project_histories_returns_empty_mapping_for_empty_storage(self) -> None:
        """Grouping should return an empty dict when there are no stored insights."""
        self._announce("Grouping histories from empty storage.")

        grouped = group_project_histories(storage_path=self.storage)
        self.assertEqual(grouped, {})

    def test_summarize_top_project_histories_returns_unique_projects(self) -> None:
        """Top-project summaries should collapse multiple snapshots into one card per project."""
        self._announce("Summarizing top unique projects with evolution evidence.")

        ts1 = datetime(2025, 5, 1, tzinfo=timezone.utc)
        ts2 = ts1 + timedelta(days=1)
        ts3 = ts1 + timedelta(days=2)

        record_project_insight(
            _analysis_payload(
                "Alpha",
                summary="Alpha first snapshot.",
                languages=["Python"],
                skills=["Python"],
            ),
            storage_path=self.storage,
            analyzed_at=ts1,
            contributors={"Lead": {"file_count": 3}},
            insight_id="alpha-1",
        )
        record_project_insight(
            _analysis_payload(
                "Alpha",
                summary="Alpha evolved snapshot.",
                languages=["Python", "TypeScript"],
                skills=["Python", "TypeScript"],
            ),
            storage_path=self.storage,
            analyzed_at=ts2,
            contributors={"Lead": {"file_count": 9}},
            insight_id="alpha-2",
        )
        record_project_insight(
            _analysis_payload(
                "Beta",
                summary="Beta only snapshot.",
                languages=["Go"],
                skills=["Go", "Docker"],
            ),
            storage_path=self.storage,
            analyzed_at=ts3,
            contributors={"Lead": {"file_count": 5}},
            insight_id="beta-1",
        )

        summaries = summarize_top_project_histories(storage_path=self.storage, top_n=2)

        self.assertEqual(len(summaries), 2)
        self.assertEqual([item["project_name"] for item in summaries], ["Alpha", "Beta"])
        self.assertEqual(summaries[0]["snapshot_count"], 2)
        self.assertEqual(summaries[0]["evolution"]["new_languages"], ["TypeScript"])
        self.assertEqual(summaries[0]["latest"]["summary"], "Alpha evolved snapshot.")
        self.assertEqual(summaries[1]["snapshot_count"], 1)

    def test_summarize_top_project_histories_respects_top_n_and_empty(self) -> None:
        """Top unique project summaries should handle empty storage and top_n limits."""
        self._announce("Constraining top unique project summaries.")

        self.assertEqual(summarize_top_project_histories(storage_path=self.storage, top_n=3), [])

        record_project_insight(
            _analysis_payload("One"),
            storage_path=self.storage,
            contributors={"Lead": {"file_count": 10}},
            insight_id="one-1",
        )
        record_project_insight(
            _analysis_payload("Two"),
            storage_path=self.storage,
            contributors={"Lead": {"file_count": 2}},
            insight_id="two-1",
        )

        summaries = summarize_top_project_histories(storage_path=self.storage, top_n=1)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["project_name"], "One")

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

    def test_entry_to_dataclass_loads_thumbnail_field(self) -> None:
        """Verify that thumbnail data in JSON is loaded into ProjectInsight dataclass."""
        self._announce("Testing thumbnail field loading from JSON entry.")

        thumbnail_data = {
            "path": "User_config_files/thumbnails/abc-123.jpg",
            "filename": "abc-123.jpg",
            "exists": True,
            "added_at": "2026-01-10T19:17:10.199176+00:00",
        }

        record_project_insight(
            _analysis_payload("ThumbnailTest"),
            storage_path=self.storage,
            insight_id="thumb-test",
        )

        disk_data = json.loads(self.storage.read_text(encoding="utf-8"))
        disk_data[0]["thumbnail"] = thumbnail_data
        self.storage.write_text(json.dumps(disk_data, indent=2), encoding="utf-8")

        loaded = list_project_insights(self.storage)
        self.assertEqual(len(loaded), 1)
        self.assertIsNotNone(loaded[0].thumbnail)
        self.assertEqual(loaded[0].thumbnail["path"], thumbnail_data["path"])
        self.assertEqual(loaded[0].thumbnail["filename"], thumbnail_data["filename"])
        self.assertTrue(loaded[0].thumbnail["exists"])

if __name__ == "__main__":
    unittest.main()
