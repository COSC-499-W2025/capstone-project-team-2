from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).parent.parent))
from src.analyzers.c.c_oop_analyzer import (analyze_source, analyze_c_project)


@pytest.fixture
def sample_c_file():
    """
    Returns (file_path, source) for the main sample C file.
    """
    file_path = Path(__file__).parent / "small_test_scripts" / "c_sample.c"
    return file_path, file_path.read_text()

class TestCAnalyzer:

    def test_c_file_analysis_basic(self, sample_c_file):
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        assert isinstance(report, dict)
        assert report.get("syntax_ok") is True

    def test_import_detection(self, sample_c_file):
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        assert report["imports"] == ["stdio.h", "myheader.h"]

    def test_struct_and_class_detection(self, sample_c_file):
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        classes = {c["name"]: c for c in report["classes"]}

        assert "Foo" in classes
        assert classes["Foo"]["methods"] == ["bar"]

        assert "Base" in classes
        assert "Derived" in classes
        assert classes["Derived"]["bases"] == ["Base"]

    def test_vtable_detection(self, sample_c_file):
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        classes = {c["name"]: c for c in report["classes"]}

        assert "Foo_vtable" in classes
        assert classes["Foo_vtable"]["is_vtable"] is True
        assert len(classes["Foo_vtable"]["methods"]) == 2

    def test_c_specific_metrics(self, sample_c_file):
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        c_spec = report["c_spec"]

        assert c_spec["constructor_functions"] == 1
        assert c_spec["destructor_functions"] == 1
        assert c_spec["opaque_pointers"] == 1

    def test_complexity_metrics(self, sample_c_file):
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        complexity = report["complexity"]

        assert complexity["total_functions"] >= 2
        assert complexity["max_loop_depth"] == 3
        assert complexity["functions_with_nested_loops"] >= 1