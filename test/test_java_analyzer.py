import unittest
from pathlib import Path
import sys
import textwrap

sys.path.append(str(Path(__file__).parent.parent))
from src.java_analyzer import analyze_source
from src.oop_aggregator import aggregate_canonical_reports

class TestJavaAnalyzer(unittest.TestCase):

    def test_single_class_basic_stats(self):
        """One simple class with constructor and methods."""
        source = textwrap.dedent("""
            package com.example;

            public class Foo {
                private int x;
                public String name;

                public Foo() {
                    this.x = 0;
                }

                public void bar() {
                    System.out.println("bar");
                }

                public int getX() {
                    return x;
                }
            }
        """)
        result = analyze_source(source, Path("Foo.java"))

        self.assertTrue(result["syntax_ok"])
        self.assertEqual(result["module"], "com.example")
        self.assertEqual(len(result["classes"]), 1)

        cls = result["classes"][0]
        self.assertEqual(cls["name"], "Foo")
        self.assertTrue(cls["has_constructor"])
        self.assertEqual(len(cls["methods"]), 3)
        self.assertIn("x", cls["private_attrs"])
        self.assertIn("name", cls["public_attrs"])

    def test_inheritance_and_implements(self):
        """Class with extends and implements."""
        source = textwrap.dedent("""
            package org.test;

            public class Child extends Parent implements Runnable, Comparable {
                public Child() {}
                public void run() {}
                public int compareTo(Object o) { return 0; }
            }
        """)
        result = analyze_source(source, Path("Child.java"))

        self.assertTrue(result["syntax_ok"])
        cls = result["classes"][0]
        self.assertIn("Parent", cls["bases"])
        self.assertIn("Runnable", cls["bases"])
        self.assertIn("Comparable", cls["bases"])

    def test_special_methods_detection(self):
        """Detect toString, equals, hashCode as special methods."""
        source = textwrap.dedent("""
            public class WithSpecials {
                public String toString() { return "test"; }
                public boolean equals(Object o) { return true; }
                public int hashCode() { return 42; }
            }
        """)
        result = analyze_source(source, Path("WithSpecials.java"))

        cls = result["classes"][0]
        self.assertIn("toString", cls["special_methods"])
        self.assertIn("equals", cls["special_methods"])
        self.assertIn("hashCode", cls["special_methods"])

    def test_nested_loops_complexity(self):
        """Detect nested loops and max loop depth."""
        source = textwrap.dedent("""
            public class Loops {
                public void nested() {
                    for (int i = 0; i < 10; i++) {
                        for (int j = 0; j < 10; j++) {
                            System.out.println(i + j);
                        }
                    }
                }
            }
        """)
        result = analyze_source(source, Path("Loops.java"))

        cx = result["complexity"]
        self.assertEqual(cx["total_functions"], 1)
        self.assertEqual(cx["functions_with_nested_loops"], 1)
        self.assertEqual(cx["max_loop_depth"], 2)

    def test_syntax_error_handling(self):
        """Invalid Java syntax should return syntax_ok=False."""
        source = "public class Broken { void foo( }"

        result = analyze_source(source, Path("Broken.java"))

        self.assertFalse(result["syntax_ok"])
        self.assertIn("syntax_error", result)
        self.assertEqual(result["classes"], [])

if __name__ == "__main__":
    unittest.main()
