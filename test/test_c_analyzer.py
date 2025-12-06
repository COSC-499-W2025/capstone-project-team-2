from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).parent.parent))
from src.c_oop_analyzer import (analyze_source, analyze_c_project)



class TestCAnalyzer:

    def test_c_file_analysis(self):
        file_path = Path(__file__).parent / "small_test_scripts" / "c_sample.c"

        source = file_path.read_text()

        report = analyze_source(source, file_path)

        assert isinstance(report, dict)
        assert report.get("syntax_ok") is True


        assert report["imports"] == ["stdio.h", "myheader.h"]


        classes = {c["name"]: c for c in report["classes"]}

        # Foo struct
        assert "Foo" in classes
        assert classes["Foo"]["methods"] == ["bar"]

        # Base struct
        assert "Base" in classes

        # Derived struct
        assert "Derived" in classes
        assert classes["Derived"]["bases"] == ["Base"]

        # Foo_vtable
        assert "Foo_vtable" in classes
        assert classes["Foo_vtable"]["is_vtable"] is True
        assert len(classes["Foo_vtable"]["methods"]) == 2


        c_spec = report["c_spec"]

        assert c_spec["constructor_functions"] == 1
        assert c_spec["destructor_functions"] == 1
        #assert c_spec["static_functions"] == 1
        assert c_spec["opaque_pointers"] == 1


        complexity = report["complexity"]

        # At least two functions (test_loops + create/destroy)
        assert complexity["total_functions"] >= 2

        # The nested loop block should return 3
        assert complexity["max_loop_depth"] == 3

        # nested loop test
        assert complexity["functions_with_nested_loops"] == 1