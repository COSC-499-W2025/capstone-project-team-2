import pytest
from pathlib import Path
from src.c_oop_analyzer import (
    analyze_source,
    calc_loop_depth,
    num_opaque_pointers,
    analyze_c_project_oop,
)

class test_c_analyzer:
    def test_detect_basic_struct():
        src = """
            struct Foo {
                int x;
                void (*bar)(int);
        };
        """
        report = analyze_source(src, Path("foo.c"))
        classes = report["classes"]

        assert len(classes) == 1
        assert classes[0]["name"] == "Foo"
        assert classes[0]["methods"] == ["bar"]  # function pointer
        assert classes[0]["is_vtable"] is False

