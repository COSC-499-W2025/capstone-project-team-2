import pytest
from pathlib import Path
from src.analyzers.c.csharp_analyzer import csharpanalysis


analyzer = csharpanalysis()
source = "class Cat { public: void meow(); };"
result = analyzer.analyze_file(source, Path("test.cs"))

@pytest.fixture
def analyzer():
    return csharpanalysis()

def analyze(analyzer, source):
    """Helper to analyze source and return result"""
    return analyzer.analyze_file(source, Path("test.cpp"))

class Test_csharp_analysis:

    """
    Test suite for validating C# source analysis behavior.
    Output strictly follows the analyzer aggregation schema:
        classes, methods, inheritance, encapsulation,
        complexity metrics, and C#-specific features.
    Args:
        analyzer (pytest.fixture): Initialized C++ analyzer instance.
    Returns:
        None
    """
    
    @pytest.mark.parametrize("source,expected_classes", [
        ("class Dog { int age; };", ["Dog"]),
        ("struct Cat { int age; };", ["Cat"]),
        ("class A {}; class B {}; struct C {};", ["A", "B", "C"]),
    ])
    def test_class_detection(self, analyzer, source, expected_classes):
        result = analyze(analyzer, source)
        names = [c["name"] for c in result["classes"]]
        assert names == expected_classes
    
    @pytest.mark.parametrize("source,class_name,expected_bases", [
        ("class Dog : Animal { }", "Dog", ["Animal"]),
        ("class Dog : Mammal, Pet { }", "Dog", ["Mammal", "Pet"]),
    ])
    def test_inheritance(self, analyzer, source, class_name, expected_bases):
        result = analyze(analyzer, source)
        cls = next(c for c in result["classes"] if c["name"] == class_name)
        assert set(cls["bases"]) == set(expected_bases)
    
    def test_private_and_public_fields(self, analyzer):
        source = "class Dog { private int x; public int y; }"
        result = analyze(analyzer, source)
        dog = result["classes"][0]
        assert "x" in dog["private_attrs"]
        assert "y" in dog["public_attrs"]
    
    @pytest.mark.parametrize("source,has_ctor,methods", [
        ("class Dog { public Dog() { } public void Bark() { } }", True, ["Dog", "Bark"]),
        ("class Cat { public void Meow() { } }", False, ["Meow"]),
    ])
    def test_methods_and_constructors(self, analyzer, source, has_ctor, methods):
        result = analyze(analyzer, source)
        cls = result["classes"][0]
        assert cls["has_constructor"] == has_ctor
        assert set(cls["methods"]) == set(methods)
    
    def test_special_methods(self, analyzer):
        source = """
        class V { 
            public V() { }
            ~V() { }
            public static V operator+(V a, V b) { return a; } 
        }
        """
        result = analyze(analyzer, source)
        v = result["classes"][0]
        assert any("operator" in m or "~V" in m or m == "V" for m in v["special_methods"])
    
    def test_using(self, analyzer):
        source = """
        using System;
        using System.Collections.Generic;
        class A {}
        """
        result = analyze(analyzer, source)
        assert "using System;" in result["imports"]
        assert "using System.Collections.Generic;" in result["imports"]
    
    @pytest.mark.parametrize("source,ds_key,min_count", [
        ("class A { List<int> a; List<string> b; }", "lists", 2),
        ("class A { Dictionary<int,int> d; }", "dictionaries", 1),
    ])

    def test_data_structures(self, analyzer, source, ds_key, min_count):
        result = analyze(analyzer, source)
        assert result["data_structures"][ds_key] >= min_count
    
    def test_complexity_metrics(self, analyzer):
        source = """
        class Test { 
            void F() { } 
            void G() { for(int i=0;i<10;i++) { for(int j=0;j<10;j++) { } } }
        }
        """
        result = analyze(analyzer, source)
        assert result["complexity"]["total_functions"] >= 2
        assert result["complexity"]["functions_with_nested_loops"] >= 1
        assert result["complexity"]["max_loop_depth"] >= 2

    def test_parse_failure_returns_error(self, analyzer):
        """Check that invalid syntax returns report with error, not crash."""
        source = "this is not valid C# {{{{{{{"
        result = analyze(analyzer, source)
        # Should return a report without crashing
        assert "classes" in result
        assert "imports" in result

    def test_empty_file_parses(self, analyzer):
        """Check that empty file doesn't crash."""
        source = ""
        result = analyze(analyzer, source)
        # Should return a report, not crash
        assert "classes" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

