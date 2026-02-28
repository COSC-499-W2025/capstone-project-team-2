import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
from src.core.multi_project_handler import single_project_run, multi_project_handler


class TestFilePassing:

    def test_zip_path_extracted_first(self):
        """ZIP paths should be passed to extract_if_zip before analysis"""
        mock_extract = MagicMock(return_value=Path("/tmp/extracted"))
        mock_analyze = MagicMock(return_value={"dedup": None, "snapshots": []})

        with patch("src.core.multi_project_handler.extract_if_zip", mock_extract), \
             patch("src.core.multi_project_handler.analyze_project", mock_analyze):
            single_project_run(("/projects/archive.zip", False))

        mock_extract.assert_called_once_with(Path("/projects/archive.zip"))

    def test_directory_skips_extraction(self):
        """Directory paths should skip extract_if_zip entirely"""
        mock_extract = MagicMock()
        mock_analyze = MagicMock(return_value={"dedup": None, "snapshots": []})

        with patch("src.core.multi_project_handler.extract_if_zip", mock_extract), \
             patch("src.core.multi_project_handler.analyze_project", mock_analyze):
            single_project_run(("/projects/my_app", False))

        mock_extract.assert_not_called()
        
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

    def test_concurrent_writes_are_serialized(self):
        """record_project_insight and export_json should never be called concurrently"""
        import threading
        paths = ["/proj/a", "/proj/b", "/proj/c"]
        active_count = []
        max_concurrent = [0]
        lock = threading.Lock()

        def mock_export(project_name, analysis):
            with lock:
                active_count.append(1)
                max_concurrent[0] = max(max_concurrent[0], len(active_count))
            import time
            time.sleep(0.05)
            with lock:
                active_count.pop()
            return {"skipped": False, "snapshots": []}

        with patch("src.core.analysis_service.export_json", side_effect=mock_export), \
            patch("src.core.multi_project_handler.extract_if_zip", MagicMock(side_effect=lambda p: p)), \
            patch("src.core.analysis_service.record_project_insight", MagicMock(return_value=None)), \
            patch("src.core.analysis_service.deduplicate_project", MagicMock(return_value=MagicMock(
             unique_files=0, duplicate_files=0, duplicates=[], index_size=0, removed=0
            ))):
            multi_project_handler.multi_project_runner(paths)

        assert max_concurrent[0] == 1, f"Expected max 1 concurrent write, got {max_concurrent[0]}"
