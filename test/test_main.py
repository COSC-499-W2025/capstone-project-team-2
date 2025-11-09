import unittest
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock,call
import src.main as main_mod


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

    """
    checks that previous projects menu correctly enters a folder and selects a 
    saved JSON file and calls show_saved_summary correctly on the selected file
    """
    @patch.object(main_mod, "show_saved_summary")
    @patch.object(main_mod, "list_saved_projects", return_value=[Path("/tmp/a.json")])
    @patch("builtins.input", side_effect=[
        "C:/some/folder",  # folder prompt
        "1"                # choose first file
    ])
    def test_previous_projects_displays_choice(self, _inp, _list, show):
        main_mod.previous_projects_menu()
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


if __name__ == "__main__":
    unittest.main()
