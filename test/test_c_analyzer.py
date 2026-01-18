from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).parent.parent))
from src.analyzers.c.c_oop_analyzer import (analyze_source, analyze_c_project)


@pytest.fixture
def sample_c_file():
    """
    Provide a sample C source file and its contents for analyzer tests.

    Args:
        None: This fixture does not take any parameters.

    Returns:
        tuple: A tuple containing the Path to the sample C file and the file
        contents as a string.
    """
    file_path = Path(__file__).parent / "small_test_scripts" / "c_sample.c"
    return file_path, file_path.read_text()

class TestCAnalyzer:
    """
    Test suite for validating the C object-oriented analyzer, including
    import detection, struct-to-class mapping, inheritance patterns,
    vtable detection, and complexity metrics.
    """

    def test_c_file_analysis_basic(self, sample_c_file):
        """
        Verify that analyzing a valid C file produces a dictionary report
        and that syntax is marked as valid.

        Args:
            sample_c_file: Fixture providing the C file path and source code.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        assert isinstance(report, dict)
        assert report.get("syntax_ok") is True

    def test_import_detection(self, sample_c_file):
        """
        Verify that C include directives are correctly detected and reported
        as imports.

        Args:
            sample_c_file: Fixture providing the C file path and source code.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        assert report["imports"] == ["stdio.h", "myheader.h"]

    def test_struct_and_class_detection(self, sample_c_file):
        """
        Verify that C structs are correctly identified as classes, including
        detection of methods via function pointers and inheritance through
        struct composition.

        Args:
            sample_c_file: Fixture providing the C file path and source code.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        classes = {c["name"]: c for c in report["classes"]}

        assert "Foo" in classes
        assert classes["Foo"]["methods"] == ["bar"]

        assert "Base" in classes
        assert "Derived" in classes
        assert classes["Derived"]["bases"] == ["Base"]

    def test_vtable_detection(self, sample_c_file):
        """
        Verify that virtual table patterns are correctly detected based on
        struct naming conventions and function pointer usage.

        Args:
            sample_c_file: Fixture providing the C file path and source code.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        classes = {c["name"]: c for c in report["classes"]}

        assert "Foo_vtable" in classes
        assert classes["Foo_vtable"]["is_vtable"] is True
        assert len(classes["Foo_vtable"]["methods"]) == 2

    def test_c_specific_metrics(self, sample_c_file):
        """
        Verify that C-specific object-oriented metrics such as constructor
        functions, destructor functions, and opaque pointer usage are
        correctly reported.

        Args:
            sample_c_file: Fixture providing the C file path and source code.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        c_spec = report["c_spec"]

        assert c_spec["constructor_functions"] == 1
        assert c_spec["destructor_functions"] == 1
        assert c_spec["opaque_pointers"] == 1

    def test_complexity_metrics(self, sample_c_file):
        """
        Verify that code complexity metrics such as total function count,
        maximum loop nesting depth, and nested loop detection are correctly
        computed.

        Args:
            sample_c_file: Fixture providing the C file path and source code.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        file_path, source = sample_c_file
        report = analyze_source(source, file_path)

        complexity = report["complexity"]

        assert complexity["total_functions"] >= 2
        assert complexity["max_loop_depth"] == 3
        assert complexity["functions_with_nested_loops"] >= 1