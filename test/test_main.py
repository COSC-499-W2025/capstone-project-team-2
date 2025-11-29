import unittest
import tempfile
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import sys
import json

sys.path.append(str(Path(__file__).resolve().parents[1]))
import src.main as main_mod


def make_input_fn(values):
    """
    Return a callable suitable for patch(..., side_effect=...) that yields
    each value from `values` in order, and returns "" for any further calls.
    """
    it = iter(values)

    def _fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            return ""  # default to empty string for extra prompts

    return _fake_input


class TestMainModule(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory for each test"""
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directories created during tests"""
        if hasattr(self, "tempdir") and Path(self.tempdir).exists():
            shutil.rmtree(self.tempdir, ignore_errors=True)

    @patch.object(main_mod.ConfigurationForUsersUI, "run_configuration_cli")
    @patch.object(main_mod.ConfigLoader, "load", return_value={"ok": True})
    def test_settings_menu_calls_cli(self, _load, run_cli):
        """Verifies the setting menu correctly loads user config and launches configuration CLI"""
        main_mod.settings_menu()
        run_cli.assert_called_once()

    @patch.object(main_mod, "analyze_project")
    @patch.object(main_mod, "extract_if_zip", return_value=Path("/tmp/temp"))
    @patch.object(main_mod, "_input_path", return_value=Path("/tmp/proj.zip"))
    @patch("builtins.input", side_effect=["2"])
    def test_analyze_menu_zip_calls_extract_and_analyze(
        self, _inp, _ipath, extract_if_zip, analyze_project
    ):
        """Checks the "Zip" branch of the analyze projects menu retrieves ZIP path,
        extracts it, and calls analyze_project"""
        analyze_project.return_value = None
        result = main_mod.analyze_project_menu()
        analyze_project.assert_called_once_with(Path("/tmp/temp"))
        self.assertIsNone(result)

    @patch("builtins.input", side_effect=["0"])
    def test_analyze_menu_exit(self, _inp):
        """Checks that selecting option 0 "Exit" in the analyze project menu correctly
        exits back to the main menu"""
        self.assertIsNone(main_mod.analyze_project_menu())

    @patch.object(main_mod, "show_saved_summary")
    @patch.object(main_mod, "list_saved_projects", return_value=[Path("/tmp/a.json")])
    @patch("builtins.input", side_effect=make_input_fn(["1"]))
    def test_saved_projects_displays_choice(self, _inp, _list, show):
        """Ensures saved_projects_menu calls show_saved_summary for the chosen file,
        and that the "Press Enter to continue" prompt is harmless"""
        main_mod.saved_projects_menu()
        show.assert_called_once_with(Path("/tmp/a.json"))

    @patch.object(main_mod, "record_project_insight")
    @patch.object(main_mod, "export_json")
    @patch.object(main_mod, "generate_resume_item")
    @patch.object(main_mod, "estimate_duration", return_value="5 days")
    @patch.object(main_mod, "FileMetadataExtractor")
    def test_analyze_project_wires_dependencies(
        self, FakeExtractor, est_duration, gen_resume, _export, _record
    ):
        """Checks that analyze_project correctly orchestrates all its internal components:
        (reading file hierarchy, calculating duration, generating resume item, exporting results)"""
        # Fake extractor returns an object with .file_hierarchy()
        fake_inst = MagicMock()
        fake_inst.file_hierarchy.return_value = {"type": "DIR", "children": []}
        FakeExtractor.return_value = fake_inst

        # Fake résumé result object with required attributes
        gen_resume.return_value = SimpleNamespace(
            project_name="DemoProj",
            summary="Built DemoProj.",
            highlights=["Implemented core functionality", "Demonstrated skills: Python"],
            project_type="individual",
            detection_mode="local",
            languages=["Python"],
            frameworks=[],
            skills=["Python"],
            framework_sources={},
        )

        # Mock record_project_insight to return a fake insight
        _record.return_value = SimpleNamespace(id=1, project_name="DemoProj")

        root = Path("/tmp/project")
        main_mod.analyze_project(root)

        FakeExtractor.assert_called_once_with(root)
        est_duration.assert_called_once()
        gen_resume.assert_called_once_with(root, project_name="project")
        _export.assert_called_once()  # verify we reached the export step

    @patch.object(main_mod.store, "insert_json", return_value=123)
    @patch.object(main_mod.SaveFileAnalysisAsJSON, "saveAnalysis")
    @patch("builtins.input", side_effect=["y"])
    def test_export_json_saves_when_yes(self, _inp, saveAnalysis, mock_insert_json):
        """Checks that export_json function is correctly called when user chooses to save"""
        # Use the test's temp directory
        temp_save_dir = Path(self.tempdir) / "export_test"

        with patch.object(main_mod, "DEFAULT_SAVE_DIR", temp_save_dir):
            project = "Demo"
            analysis = {"ok": True}
            main_mod.export_json(project, analysis)

        # ensure saveAnalysis called correctly
        args, kwargs = saveAnalysis.call_args
        self.assertEqual(args[0], project)  # project_name
        self.assertEqual(args[1], analysis)  # analysis (deepcopy, but equal)
        self.assertIsInstance(args[2], str)  # output dir path string

        # ensure DB insert is invoked with the generated filename
        mock_insert_json.assert_called_once()
        insert_args, insert_kwargs = mock_insert_json.call_args
        self.assertEqual(insert_args[0], project + ".json")

    @patch("builtins.input", side_effect=["0"])
    def test_main_returns_zero_on_exit(self, _inp):
        """Checks that the main program loop exits correctly when the user
        tries to exit out of the program"""
        self.assertEqual(main_mod.main(), 0)

    @patch.object(main_mod.store, "count_file_references", return_value=0)
    @patch.object(
        main_mod,
        "get_saved_projects_from_db",
        return_value=[(101, "to_delete.json", "{}", "2025-01-01 12:00")],
    )
    @patch.object(main_mod.store, "delete", return_value=True)
    @patch("builtins.input", side_effect=["1", "y", "n"])
    def test_delete_analysis_menu_deletes_selected(
        self, _inp, mock_store_delete, _get_projects, _mock_count_refs
    ):
        """Tests that delete_analysis_menu correctly deletes from both filesystem and database"""
        # create a fake file in temp dir
        temp_dir = Path(self.tempdir)
        temp_file = temp_dir / "to_delete.json"
        temp_file.write_text("{}")

        with patch.object(main_mod, "DEFAULT_SAVE_DIR", temp_dir):
            with patch.object(main_mod, "list_saved_projects", return_value=[temp_file]):
                main_mod.delete_analysis_menu()

        # Verify database delete was called
        mock_store_delete.assert_called_once_with(101)
        # Verify file was deleted from disk
        self.assertFalse(temp_file.exists())

    @patch.object(
        main_mod,
        "get_saved_projects_from_db",
        return_value=[(202, "dont_delete.json", "{}", "2025-01-02 12:00:00")],
    )
    @patch.object(main_mod.store, "delete", return_value=True)
    @patch("builtins.input", side_effect=["1", "n", "0"])
    def test_delete_analysis_menu_cancel_does_not_delete(
        self, _inp, mock_delete_db, _get_projects
    ):
        """User selects an entry but cancels at confirmation; neither DB nor file delete should be invoked"""
        temp_dir = Path(self.tempdir)
        temp_file = temp_dir / "dont_delete.json"
        temp_file.write_text("{}")

        with patch.object(main_mod, "DEFAULT_SAVE_DIR", temp_dir):
            with patch.object(main_mod, "list_saved_projects", return_value=[temp_file]):
                main_mod.delete_analysis_menu()

        mock_delete_db.assert_not_called()
        # File should still exist
        self.assertTrue(temp_file.exists())

    @patch.object(main_mod.store, "count_file_references", return_value=0)
    def test_delete_file_from_disk_deletes_existing_file(self, mock_count_refs):
        """Ensure delete_file_from_disk removes an actual file in DEFAULT_SAVE_DIR"""
        temp_dir = Path(self.tempdir)
        filename = "temp_analysis.json"
        file_path = temp_dir / filename

        # create the file
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path.write_text("{}", encoding="utf-8")
        self.assertTrue(file_path.exists())

        with patch.object(main_mod, "DEFAULT_SAVE_DIR", temp_dir):
            deleted = main_mod.delete_file_from_disk(filename)

        self.assertTrue(deleted)
        self.assertFalse(file_path.exists())
        mock_count_refs.assert_called_once_with(filename)

    @patch.object(main_mod.store, "delete", return_value=True)
    def test_delete_from_database_by_id_calls_store_delete(self, mock_store_delete):
        """delete_from_database_by_id should call store.delete(record_id) and return its result"""
        result = main_mod.delete_from_database_by_id(555)
        mock_store_delete.assert_called_once_with(555)
        self.assertTrue(result)

    @patch("builtins.print")
    @patch.object(main_mod, "record_project_insight")
    @patch.object(main_mod, "export_json")
    @patch.object(main_mod, "generate_resume_item")
    @patch.object(main_mod, "estimate_duration", return_value="5 days")
    @patch.object(main_mod, "FileMetadataExtractor")
    def test_analyze_project_logs_info_when_insight_recording_succeeds(
        self,
        FakeExtractor,
        est_duration,
        gen_resume,
        _export,
        mock_record_insight,
        mock_print,
    ):
        """Tests that analyze_project logs an INFO message when insight recording succeeds"""
        # Fake extractor returns an object with .file_hierarchy()
        fake_inst = MagicMock()
        fake_inst.file_hierarchy.return_value = {"type": "DIR", "children": []}
        FakeExtractor.return_value = fake_inst

        # Fake résumé result object with required attributes
        gen_resume.return_value = SimpleNamespace(
            project_name="DemoProj",
            summary="Built DemoProj.",
            highlights=["Implemented core functionality"],
            project_type="individual",
            detection_mode="local",
            languages=["Python"],
            frameworks=[],
            skills=["Python"],
            framework_sources={},
        )

        # record_project_insight returns an object with id + project_name
        mock_record_insight.return_value = SimpleNamespace(
            id=123,
            project_name="DemoProj",
        )

        root = Path("/tmp/project")
        # This should run without error and log an INFO message
        main_mod.analyze_project(root)

        mock_record_insight.assert_called_once()
        # Check that at least one print call starts with the INFO prefix
        info_calls = [
            args[0]
            for args, _ in mock_print.call_args_list
            if args and isinstance(args[0], str)
        ]
        self.assertTrue(
            any(msg.startswith("[INFO] Insight recorded for project") for msg in info_calls),
            msg=f"Expected an [INFO] log about insight, got: {info_calls}",
        )

    @patch("builtins.print")
    @patch.object(main_mod, "record_project_insight", side_effect=Exception("boom"))
    @patch.object(main_mod, "export_json")
    @patch.object(main_mod, "generate_resume_item")
    @patch.object(main_mod, "estimate_duration", return_value="5 days")
    @patch.object(main_mod, "FileMetadataExtractor")
    def test_analyze_project_logs_warning_when_insight_recording_fails(
        self,
        FakeExtractor,
        est_duration,
        gen_resume,
        _export,
        _mock_record_insight,
        mock_print,
    ):
        """Tests that analyze_project logs a WARNING and doesn't crash when insight recording fails"""
        # Fake extractor
        fake_inst = MagicMock()
        fake_inst.file_hierarchy.return_value = {"type": "DIR", "children": []}
        FakeExtractor.return_value = fake_inst

        gen_resume.return_value = SimpleNamespace(
            project_name="DemoProj",
            summary="Built DemoProj.",
            highlights=["Implemented core functionality"],
            project_type="individual",
            detection_mode="local",
            languages=["Python"],
            frameworks=[],
            skills=["Python"],
            framework_sources={},
        )

        root = Path("/tmp/project")

        # analyze_project should NOT propagate the exception.
        try:
            main_mod.analyze_project(root)
        except Exception as e:  # pragma: no cover
            self.fail(
                f"analyze_project should not raise when insight logging fails, but got: {e}"
            )

        # Verify we logged a WARN message containing the exception text
        printed = [
            args[0]
            for args, _ in mock_print.call_args_list
            if args and isinstance(args[0], str)
        ]
        self.assertTrue(
            any("[WARN] Failed to record project insight: boom" in msg for msg in printed),
            msg=f"Expected a [WARN] log about failed insight, got: {printed}",
        )

    def test_list_saved_projects_includes_legacy_files(self):
        """Verify that list_saved_projects finds files in both new and legacy locations"""
        temp_dir = Path(self.tempdir)
        
        # Create new location with one file
        new_dir = temp_dir / "project_insights"
        new_dir.mkdir(parents=True)
        (new_dir / "new_project.json").write_text("{}")
        
        # Create legacy location with another file
        (temp_dir / "old_project.json").write_text("{}")
        
        with patch.object(main_mod, "DEFAULT_SAVE_DIR", new_dir):
            projects = main_mod.list_saved_projects(new_dir)
        
        # Should find both files
        self.assertEqual(len(projects), 2)
        names = {p.name for p in projects}
        self.assertIn("new_project.json", names)
        self.assertIn("old_project.json", names)

    @patch("builtins.print")
    def test_show_saved_summary_uses_contribution_summary(self, mock_print):
        """show_saved_summary should print contributors from contribution_summary and ignore 0-count noise."""
        temp_file = Path(self.tempdir) / "analysis.json"

        data = {
            "analysis": {
                "project_root": "/tmp/demo",
                "resume_item": {
                    "project_type": "collaborative",
                    "detection_mode": "git",
                    "languages": ["Python"],
                    "frameworks": [],
                    "skills": ["Python"],
                    "summary": "Built Demo.",
                },
                "duration_estimate": "2 days",
                "contribution_summary": {
                    "metric": "files",
                    "contributors": {
                        "Alice": {"file_count": 3, "percentage": "60%"},
                        "Bob": {"file_count": 2, "percentage": "40%"},
                        "Noise": {"file_count": 0, "percentage": "0%"},
                        "<unattributed>": {"file_count": 0, "percentage": "0%"},
                    },
                },
            }
        }
        temp_file.write_text(json.dumps(data), encoding="utf-8")

        main_mod.show_saved_summary(temp_file)

        printed = [
            args[0]
            for args, _ in mock_print.call_args_list
            if args and isinstance(args[0], str)
        ]

        # contributors header
        self.assertTrue(any("Contributors :" in line for line in printed))

        # Alice/Bob lines with percentages + "files" metric
        self.assertTrue(
            any("Alice" in line and "3 files" in line and "(60%" in line for line in printed),
            msg=f"No Alice line in: {printed}",
        )
        self.assertTrue(
            any("Bob" in line and "2 files" in line and "(40%" in line for line in printed),
            msg=f"No Bob line in: {printed}",
        )

        # Noise should be filtered out
        self.assertFalse(
            any("Noise" in line for line in printed),
            msg=f"'Noise' contributor should have been filtered out: {printed}",
        )

        # <unattributed> kept even with 0 files
        self.assertTrue(
            any("<unattributed>" in line for line in printed),
            msg=f'<unattributed> missing from contributors: {printed}',
        )

        # résumé line printed
        self.assertTrue(
            any("Résumé line" in line and "Built Demo." in line for line in printed),
            msg=f"No résumé line in saved-summary output: {printed}",
        )

if __name__ == "__main__":
    unittest.main()
