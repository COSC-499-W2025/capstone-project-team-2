import pytest
from pathlib import Path
from src.analyzers.c.csharp_analyzer import csharpanalysis


analyzer = csharpanalysis()
source = "class Cat { public: void meow(); };"
result = analyzer.analyze_file(source, Path("test.cpp"))

@pytest.fixture
def analyzer():
    return csharpanalysis()

def analyze(analyzer, source):
    """Helper to analyze source and return result"""
    return analyzer.analyze_file(source, Path("test.cpp"))

class Test_cpp_analysis:

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
        ("class Dog : public Animal { };", "Dog", ["Animal"]),
        ("class Dog : public Mammal, public Pet { };", "Dog", ["Mammal", "Pet"]),
    ])
    def test_inheritance(self, analyzer, source, class_name, expected_bases):
        result = analyze(analyzer, source)
        cls = next(c for c in result["classes"] if c["name"] == class_name)
        assert set(cls["bases"]) == set(expected_bases)
    
    def test_private_attrs_in_class(self, analyzer):
        result = analyze(analyzer, "class Dog { int x; public: int y; };")
        dog = result["classes"][0]
        assert "x" in dog["private_attrs"]
        assert "y" in dog["public_attrs"]
    
    @pytest.mark.parametrize("source,has_ctor,methods", [
        ("class Dog { public: Dog(); void bark(); };", True, ["Dog", "bark"]),
        ("class Cat { public: void meow(); };", False, ["meow"]),
    ])
    def test_methods_and_constructors(self, analyzer, source, has_ctor, methods):
        result = analyze(analyzer, source)
        cls = result["classes"][0]
        assert cls["has_constructor"] == has_ctor
        assert set(cls["methods"]) == set(methods)
    
    def test_special_methods(self, analyzer):
        source = """
        class V {
            public static V operator +(V a, V b) => a;
            ~V() {}
        }
        """
        result = analyze(analyzer, source)
        v = result["classes"][0]

        assert any("operator" in m for m in v["special_methods"])
        assert "~V" in v["special_methods"]
    
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
        ("class A { List<int> a; List<string> b; }", "arrays", 2),
        ("class A { Dictionary<int,int> d; }", "hash_tables", 1),
        ("class A { void F() { var x = new int(); } }", "dynamic_memory", 1),
    ])

    def test_data_structures(self, analyzer, source, ds_key, min_count):
        result = analyze(analyzer, source)
        assert result["data_structures"][ds_key] >= min_count
    
    def test_complexity_metrics(self, analyzer):
        source = """
        class A {
            void F() {}
            void G() {
                for(int i=0;i<10;i++) {
                    for(int j=0;j<10;j++) {}
                }
            }
        }
        """
        result = analyze(analyzer, source)
        assert result["complexity"]["total_functions"] >= 2
        assert result["complexity"]["functions_with_nested_loops"] >= 1
        assert result["complexity"]["max_loop_depth"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

