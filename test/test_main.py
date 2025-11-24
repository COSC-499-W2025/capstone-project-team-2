import os.path
import shutil
import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import sys
import mysql.connector
from mysql.connector import Error
from src.Docker_finder import DockerFinder
from src.get_contributors_percentage_per_person import get_contributors_percentages_git
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
            return ""   # default to empty string for extra prompts

    return _fake_input

class TestMainModule(unittest.TestCase):

    def setUp(self):
        self.tempdir=tempfile.mkdtemp()

    """
    Verifies the setting menu correctly loads user config and launches configuration CLI
    """
    @patch.object(main_mod.ConfigurationForUsersUI, "run_configuration_cli")
    @patch.object(main_mod.ConfigLoader, "load", return_value={"ok": True})
    def test_settings_menu_calls_cli(self, _load, run_cli):
        main_mod.settings_menu()
        run_cli.assert_called_once()

    """
    Checks the "Zip" branch of the analyze projects menu retrieves ZIP path,
    extracts it, and calls analyze_project
    """
    @patch.object(main_mod, "analyze_project")
    @patch.object(main_mod, "extract_if_zip", return_value=Path("/tmp/temp"))
    @patch.object(main_mod, "_input_path", return_value=Path("/tmp/proj.zip"))
    @patch("builtins.input", side_effect=["2"])
    def test_analyze_menu_zip_calls_extract_and_analyze(self, _inp, _ipath, extract_if_zip, analyze_project):
        analyze_project.return_value = None  # <-- add this line
        result = main_mod.analyze_project_menu()
        analyze_project.assert_called_once_with(Path("/tmp/temp"))
        self.assertIsNone(result)

    """
    checks that selecting option 0 "Exit" in the analyze project menu correctly
    exits back to the man menu
    """
    @patch("builtins.input", side_effect=["0"])  # exit
    def test_analyze_menu_exit(self, _inp):
        self.assertIsNone(main_mod.analyze_project_menu())

    @patch.object(main_mod, "show_saved_summary")
    @patch.object(main_mod, "list_saved_projects", return_value=[Path("/tmp/a.json")])
    @patch("builtins.input", side_effect=make_input_fn([
        "1",  # choose first file
    ]))
    def test_saved_projects_displays_choice(self, _inp, _list, show):
        """
        Ensures saved_projects_menu calls show_saved_summary for the chosen file,
        and that the "Press Enter to continue" prompt is harmless.
        """
        main_mod.saved_projects_menu()
        show.assert_called_once_with(Path("/tmp/a.json"))

    """
    checks that analyze_project correctly orchestrates all its internal components:
    (reading file hierarchy, calculating duration, generating resume item, exporting results)
    """
    @patch.object(main_mod, "export_json")  # avoid prompting
    @patch.object(main_mod, "generate_resume_item")
    @patch.object(main_mod, "estimate_duration", return_value="5 days")
    @patch.object(main_mod, "FileMetadataExtractor")
    def test_analyze_project_wires_dependencies(self, FakeExtractor, est_duration, gen_resume, _export):
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
            framework_sources={}
        )

        root = Path("/tmp/project")
        main_mod.analyze_project(root)

        FakeExtractor.assert_called_once_with(root)
        est_duration.assert_called_once()
        gen_resume.assert_called_once_with(root, project_name="project")
        _export.assert_called_once()  # verify we reached the export step

    """
    checks that export_json function is correctly called when user chooses to save
    """
    @patch.object(main_mod.SaveFileAnalysisAsJSON, "saveAnalysis")
    @patch("builtins.input", side_effect=[
        "y",            # save JSON?
        "tests_out"     # output directory (relative is fine)
    ])
    def test_export_json_saves_when_yes(self, _inp, saveAnalysis):
        project = "Demo"
        analysis = {"ok": True}
        main_mod.export_json(project, analysis)
        # ensure directory created & saveAnalysis called correctly
        args, kwargs = saveAnalysis.call_args
        self.assertEqual(args[0], project)      # project_name
        self.assertEqual(args[1], analysis)     # analysis
        self.assertIsInstance(args[2], str)     # output dir path string

    """
    checks that the main program loop exits correctly when the user 
    tries to exit out of the program
    """
    @patch("builtins.input", side_effect=["0"])  # choose Exit immediately
    def test_main_returns_zero_on_exit(self, _inp):
        self.assertEqual(main_mod.main(), 0)
        
    @patch.object(main_mod, "delete_from_database_by_id", return_value=True)
    @patch.object(main_mod, "delete_file_from_disk", return_value=True)
    @patch.object(main_mod, "get_saved_projects_from_db", return_value=[(101, "to_delete.json", "{}", "2025-01-01 12:00")])
    @patch("builtins.input", side_effect=["1", "y", "n"])
    def test_delete_analysis_menu_deletes_selected(self, _inp, mock_delete_file, mock_delete_db, _get_projects):
            #create a fake file in temp dir
            temp_dir = Path(self.tempdir)
            temp_file = temp_dir / "to_delete.json"
            temp_file.write_text("{}")

            with patch.object(main_mod, "DEFAULT_SAVE_DIR", temp_dir):
                with patch.object(main_mod, "list_saved_projects", return_value=[temp_file]):
                    main_mod.delete_analysis_menu()

            main_mod.delete_from_database_by_id.assert_called_once_with(101)
            main_mod.delete_file_from_disk.assert_called_once_with("to_delete.json")


    @patch.object(main_mod, "get_saved_projects_from_db", return_value=[(202, "dont_delete.json", "{}", "2025-01-02 12:00:00")])
    @patch.object(main_mod, "delete_from_database_by_id", return_value=True)
    @patch.object(main_mod, "delete_file_from_disk", return_value=True)
    @patch("builtins.input", side_effect=["1", "n", "0"])
    def test_delete_analysis_menu_cancel_does_not_delete(self, _inp, mock_delete_file, mock_delete_db, _get_projects):
        """
        User selects an entry but cancels at confirmation; neither DB nor file delete should be invoked.
        """
        main_mod.delete_analysis_menu()

        mock_delete_db.assert_not_called()
        mock_delete_file.assert_not_called()

    def test_delete_file_from_disk_deletes_existing_file(self):
        """
        Ensure delete_file_from_disk removes an actual file in DEFAULT_SAVE_DIR.
        We patch DEFAULT_SAVE_DIR to a temporary directory from setUp.
        """
        # point DEFAULT_SAVE_DIR at the temporary directory created in setUp
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

    @patch.object(main_mod.store, "delete", return_value=True)
    def test_delete_from_database_by_id_calls_store_delete(self, mock_store_delete):
        """
        delete_from_database_by_id should call store.delete(record_id) and return its result.
        """
        result = main_mod.delete_from_database_by_id(555)
        mock_store_delete.assert_called_once_with(555)
        self.assertTrue(result)
    @patch("builtins.print")
    @patch.object(main_mod, "record_project_insight")
    @patch.object(main_mod, "export_json")  # avoid prompting
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
    @patch.object(main_mod, "export_json")  # avoid prompting
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
            self.fail(f"analyze_project should not raise when insight logging fails, but got: {e}")

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


    def tearDown(self):

        port_number, host_ip = DockerFinder().get_mysql_host_information()

        try:
            conn = mysql.connector.connect(
                host=host_ip,
                port=port_number,
                database="appdb",
                user="appuser",
                password="apppassword"
            )

            if conn.is_connected():
                print("✅ Connected to MySQL successfully!")
                cur = conn.cursor()

            # Delete ONLY the test artifact
            cur.execute("""
                        DELETE
                        FROM project_data
                        WHERE filename = %s;
                        """, ("Demo.json",))

            conn.commit()
            cur.close()
            conn.close()

        except Error as e:
            print(f"MySQL not ready yet: {e}")

    # Remove test folder
    BASE = Path(__file__).resolve().parent
    directory = BASE / "User_config_files"
    if directory.exists():
        shutil.rmtree(directory)


if __name__ == "__main__":
    unittest.main()
