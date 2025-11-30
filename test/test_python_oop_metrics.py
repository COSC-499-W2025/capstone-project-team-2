import unittest
import tempfile
from pathlib import Path
import sys
import textwrap
sys.path.append(str(Path(__file__).parent.parent))
from src.python_oop_metrics import analyze_python_project_oop

class TestPythonOOPAstAnalyzer(unittest.TestCase):

    def _write_file(self, root: Path, rel_path: str, content: str) -> Path:
        
        """Helper to write a file relative to root."""
        
        file_path = root / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_no_python_files(self):
        
        """Empty folder: no files, no classes, score 0, rating none."""
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            metrics = analyze_python_project_oop(root)

            self.assertEqual(metrics["files_analyzed"], 0)
            self.assertEqual(metrics["classes"]["count"], 0)
            self.assertEqual(metrics["score"]["oop_score"], 0.0)
            self.assertEqual(metrics["score"]["rating"], "none")

            # Data structures and complexity should be basically empty / zero.
            ds = metrics["data_structures"]
            cx = metrics["complexity"]
            self.assertEqual(ds["list_literals"], 0)
            self.assertEqual(cx["total_functions"], 0)

    def test_single_class_basic_stats(self):
        
        """One simple class with __init__ and methods."""
        
        code = textwrap.dedent("""
            class Foo:
                def __init__(self):
                    self.x = 1

                def bar(self):
                    return self.x

                def baz(self):
                    return self.x * 2
        """)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_file(root, "foo.py", code)

            metrics = analyze_python_project_oop(root)

            # File / class stats
            self.assertEqual(metrics["files_analyzed"], 1)
            self.assertEqual(metrics["classes"]["count"], 1)
            self.assertEqual(metrics["classes"]["avg_methods_per_class"], 3.0)
            self.assertEqual(metrics["classes"]["with_init"], 1)
            self.assertEqual(metrics["classes"]["with_inheritance"], 0)

            # Encapsulation: one class with private or public attrs
            self.assertEqual(
                metrics["encapsulation"]["classes_with_private_attrs"], 0
            )

            # Complexity: 3 functions, no nested loops
            cx = metrics["complexity"]
            self.assertEqual(cx["total_functions"], 3)
            self.assertEqual(cx["functions_with_nested_loops"], 0)
            self.assertEqual(cx["max_loop_depth"], 0)

    def test_inheritance_and_polymorphism(self):
        
        """Base/Child inheritance and override detection."""
        
        code = textwrap.dedent("""
            class Base:
                def foo(self):
                    return "base"

            class Child(Base):
                def foo(self):
                    return "child"

                def extra(self):
                    return "extra"
        """)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_file(root, "inherit.py", code)

            metrics = analyze_python_project_oop(root)

            self.assertEqual(metrics["classes"]["count"], 2)
            # One class (Child) uses inheritance
            self.assertEqual(metrics["classes"]["with_inheritance"], 1)
            # Polymorphism metrics
            self.assertEqual(
                metrics["polymorphism"]["classes_overriding_base_methods"], 1
            )
            self.assertEqual(
                metrics["polymorphism"]["override_method_count"], 1
            )

            # Complexity: at least 3 functions detected
            cx = metrics["complexity"]
            self.assertGreaterEqual(cx["total_functions"], 3)

    def test_private_attribute_detection(self):
        
        """self._attr style assignments counted as private attributes."""
        
        code = textwrap.dedent("""
            class Encapsulated:
                def __init__(self):
                    self._secret = 42
                    self.public = 1

                def method(self):
                    self._another_secret = 99
        """)
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_file(root, "encap.py", code)

            metrics = analyze_python_project_oop(root)

            self.assertEqual(metrics["classes"]["count"], 1)
            # At least one class with private attrs
            self.assertEqual(
                metrics["encapsulation"]["classes_with_private_attrs"], 1
            )

            # Data structures: none used
            ds = metrics["data_structures"]
            self.assertEqual(ds["list_literals"], 0)
            self.assertEqual(ds["dict_literals"], 0)

    def test_syntax_error_file_is_recorded_not_crashing(self):
        
        """Bad file should be listed in syntax_errors but not crash analysis."""
        
        good_code = textwrap.dedent("""
            class Good:
                def ok(self):
                    return 1
        """)
        bad_code = "class Broken(:\n    pass\n"  # invalid Python

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_file(root, "good.py", good_code)
            self._write_file(root, "broken.py", bad_code)

            metrics = analyze_python_project_oop(root)

            # Two .py files discovered
            self.assertEqual(metrics["files_analyzed"], 2)
            # Only the good file yields a class
            self.assertEqual(metrics["classes"]["count"], 1)
            # Syntax error should be recorded
            self.assertEqual(len(metrics["syntax_errors"]), 1)
            self.assertTrue(
                metrics["syntax_errors"][0].endswith("broken.py")
            )

if __name__ == "__main__":
    unittest.main()
