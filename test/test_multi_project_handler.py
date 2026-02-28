import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
from src.core.multi_project_handler import single_project_run, multi_project_handler


class TestFilePassing:

    def test_path_set_on_context(self):
        """Path should be assigned to runtimeAppContext before API is called"""
        mock_context = MagicMock()
        mock_api = MagicMock(return_value={"status": "Analysis Finished and Saved"})

        with patch("src.core.multi_project_handler.runtimeAppContext", mock_context), \
             patch("src.core.multi_project_handler.perform_analysis_API", mock_api):
            single_project_run(("/projects/my_app", False))

        assert mock_context.currently_uploaded_file == Path("/projects/my_app")

    def test_string_path_converted_to_path_object(self):
        """String paths should be converted to Path objects before context assignment"""
        mock_context = MagicMock()

        with patch("src.core.multi_project_handler.runtimeAppContext", mock_context), \
             patch("src.core.multi_project_handler.perform_analysis_API", MagicMock(return_value={})):
            single_project_run(("/string/path", False))

        assert isinstance(mock_context.currently_uploaded_file, Path)

    def test_zip_path_passed_correctly(self):
        """ZIP file paths should be passed through as-is for the API to handle"""
        mock_context = MagicMock()

        with patch("src.core.multi_project_handler.runtimeAppContext", mock_context), \
             patch("src.core.multi_project_handler.perform_analysis_API", MagicMock(return_value={})):
            single_project_run(("/projects/archive.zip", False))

        assert mock_context.currently_uploaded_file == Path("/projects/archive.zip")

    def test_all_paths_submitted(self):
        """Every path in the list should be submitted for analysis"""
        paths = ["/proj/a", "/proj/b", "/proj/c"]
        mock_run = MagicMock(return_value={"status": "Analysis Finished and Saved", "dedup": None})

        with patch("src.core.multi_project_handler.single_project_run", mock_run):
            multi_project_handler.multi_project_runner(paths)

        assert mock_run.call_count == 3

    def test_each_path_passed_as_arg(self):
        """Each path should be passed individually to single_project_run"""
        paths = ["/proj/a", "/proj/b"]
        captured = []

        def mock_run(args):
            captured.append(args[0])
            return {"status": "Analysis Finished and Saved", "dedup": None}

        with patch("src.core.multi_project_handler.single_project_run", side_effect=mock_run):
            multi_project_handler.multi_project_runner(paths)

        assert set(captured) == set(paths)

    def test_use_ai_forwarded_with_path(self):
        """use_ai flag should be bundled with each path in the args tuple"""
        captured = []

        def mock_run(args):
            captured.append(args)
            return {"status": "Analysis Finished and Saved", "dedup": None}

        with patch("src.core.multi_project_handler.single_project_run", side_effect=mock_run):
            multi_project_handler.multi_project_runner(["/proj/a"], use_ai=True)

        _, use_ai = captured[0]
        assert use_ai is True

    def test_failed_project_does_not_block_others(self):
        """One bad path should not prevent other projects from being analyzed"""
        paths = ["/proj/good", "/proj/bad", "/proj/also_good"]
        success_count = []

        def mock_run(args):
            path, _ = args
            if "bad" in path:
                raise Exception("analysis failed")
            success_count.append(path)
            return {"status": "Analysis Finished and Saved", "dedup": None}

        with patch("src.core.multi_project_handler.single_project_run", side_effect=mock_run):
            multi_project_handler.multi_project_runner(paths)

        assert len(success_count) == 2