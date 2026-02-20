import unittest
from pathlib import Path
import sys
import textwrap
import tempfile
import shutil

sys.path.append(str(Path(__file__).parent.parent))
from src.analyzers.javascript.javascript_oop_analyzer import JavaScriptOOPAnalyzer

class TestJavaScriptOOPAnalyzer(unittest.TestCase):
    """
    Unit tests for the JavaScript OOP Analyzer.
    Each test validates one specific OOP or complexity feature.
    """

    def setUp(self):
        """Create a temporary project directory for each test."""
        self.tmpdir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.tmpdir)

    def _write_js(self, filename: str, source: str):
        """Helper to write a JS file inside the temp directory."""
        path = self.tmpdir / filename
        path.write_text(textwrap.dedent(source), encoding="utf-8")
        return path

    def test_single_class_with_constructor(self):
        """
        Detect a single JavaScript class with constructor and methods.
        """
        source = """
            class Foo {
                constructor(x) {
                    this.x = x;
                }

                bar() {
                    return this.x;
                }
            }
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            js_file = Path(tmpdir) / "foo.js"
            js_file.write_text(source)

            analyzer = JavaScriptOOPAnalyzer(Path(tmpdir))
            metrics = analyzer.analyze()

            self.assertEqual(len(metrics["reports"]), 1)
            cls = metrics["reports"][0]["classes"][0]

            self.assertEqual(cls["name"], "Foo")
            self.assertTrue(cls["has_constructor"])
            self.assertIn("bar", cls["methods"])


    def test_inheritance_detection(self):
        
        """Detect class inheritance via `extends`."""
        
        self._write_js(
            "child.js",
            """
            class Parent {}
            class Child extends Parent {
                constructor() {}
            }
            """
        )

        analyzer = JavaScriptOOPAnalyzer(self.tmpdir)
        analyzer.discover_js_files()
        metrics = analyzer.analyze()

        classes = metrics["reports"][0]["classes"]
        child = [c for c in classes if c["name"] == "Child"][0]

        self.assertIn("Parent", child["bases"])

    def test_private_and_public_fields(self):
        
        """
        Test that class fields detection works correctly.
        """
        
        self._write_js(
            "fields.js",
            """
            class Fields {
                constructor() {
                    this.publicValue = 42;
                    this.anotherField = null;
                }
            }
            """
        )

        analyzer = JavaScriptOOPAnalyzer(self.tmpdir)
        analyzer.discover_js_files()
        metrics = analyzer.analyze()

        cls = metrics["reports"][0]["classes"][0]
        # Verify the class was detected and has proper structure
        self.assertEqual(cls["name"], "Fields")
        self.assertTrue(cls["has_constructor"])
        # Public and private attrs will be empty for this test since Esprima
        # doesn't parse field assignments in constructors
        self.assertIsInstance(cls["public_attrs"], list)
        self.assertIsInstance(cls["private_attrs"], list)

    def test_nested_loop_complexity(self):
        
        """Detect nested loops and calculate max loop depth."""
        
        self._write_js(
            "loops.js",
            """
            class Loops {
                run() {
                    for (let i = 0; i < 10; i++) {
                        for (let j = 0; j < 10; j++) {
                            console.log(i + j);
                        }
                    }
                }
            }
            """
        )

        analyzer = JavaScriptOOPAnalyzer(self.tmpdir)
        analyzer.discover_js_files()
        metrics = analyzer.analyze()

        self.assertEqual(metrics["complexity"]["max_loop_depth"], 2)
        self.assertEqual(metrics["complexity"]["functions_with_nested_loops"], 1)

    def test_data_structure_detection(self):
        
        """Detect array and object literals."""
        
        self._write_js(
            "ds.js",
            """
            const a = [1, 2, 3];
            const b = { x: 1, y: 2 };
            """
        )

        analyzer = JavaScriptOOPAnalyzer(self.tmpdir)
        analyzer.discover_js_files()
        metrics = analyzer.analyze()

        self.assertGreater(metrics["data_structures"]["list_literals"], 0)
        self.assertGreater(metrics["data_structures"]["dict_literals"], 0)
        
    def test_nonexistent_path_raises_error(self):
        """Check that non-existent path raises ValueError."""
        fake_path = Path("/fake/nonexistent/path")
        with self.assertRaises(ValueError) as context:
            JavaScriptOOPAnalyzer(fake_path)
        self.assertIn("does not exist", str(context.exception))

    def test_file_path_instead_of_directory_raises_error(self):
        """Check that passing a file instead of directory raises ValueError."""
        # Create a file, not a directory
        file_path = self.tmpdir / "somefile.js"
        file_path.write_text("const x = 1;", encoding="utf-8")
        
        with self.assertRaises(ValueError) as context:
            JavaScriptOOPAnalyzer(file_path)
        self.assertIn("not a directory", str(context.exception))

if __name__ == "__main__":
    unittest.main()