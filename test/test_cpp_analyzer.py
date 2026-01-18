import pytest
from pathlib import Path
from src.analyzers.c.cpp_analyzer import cppanalysis

analyzer = cppanalysis()
source = "class Cat { public: void meow(); };"
result = analyzer.analyze_file(source, Path("test.cpp"))

@pytest.fixture
def analyzer():
    return cppanalysis()

def analyze(analyzer, source):
    """Helper to analyze source and return result"""
    return analyzer.analyze_file(source, Path("test.cpp"))

class Test_cpp_analysis:

    """
    Test suite for validating C++ source analysis behavior.
    Output strictly follows the analyzer aggregation schema:
        classes, methods, inheritance, encapsulation,
        complexity metrics, and C++-specific features.
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
    
    def test_public_attrs_in_struct(self, analyzer):
        result = analyze(analyzer, "struct Cat { int x; private: int y; };")
        cat = result["classes"][0]
        assert "x" in cat["public_attrs"]
        assert "y" in cat["private_attrs"]
    
    @pytest.mark.parametrize("source,has_ctor,methods", [
        ("class Dog { public: Dog(); void bark(); };", True, ["Dog", "bark"]),
        ("class Cat { public: void meow(); };", False, ["meow"]),
    ])
    def test_methods_and_constructors(self, analyzer, source, has_ctor, methods):
        result = analyze(analyzer, source)
        cls = result["classes"][0]
        assert cls["has_constructor"] == has_ctor
        assert set(cls["methods"]) == set(methods)
    
    def test_virtual_methods(self, analyzer):
        result = analyze(analyzer, "class A { public: virtual void f(); void g(); };")
        assert "f" in result["classes"][0]["virtual_methods"]
        assert "g" not in result["classes"][0]["virtual_methods"]
    
    def test_override_methods(self, analyzer):
        source = "class A { virtual void f(); }; class B : public A { void f() override; };"
        result = analyze(analyzer, source)
        b_class = next(c for c in result["classes"] if c["name"] == "B")
        assert "f" in b_class["override_methods"]
    
    def test_special_methods(self, analyzer):
        result = analyze(analyzer, "class V { public: V operator+(V& o); ~V(); };")
        v = result["classes"][0]
        print(f"Methods: {v['methods']}")
        print(f"Special methods: {v['special_methods']}")
        assert any("operator" in m for m in v["special_methods"])
        assert "~V" in v["special_methods"]
    
    def test_includes(self, analyzer):
        source = '#include <iostream>\n#include "test.h"\nclass A {};'
        result = analyze(analyzer, source)
        assert "#include <iostream>" in result["imports"]
        assert '#include "test.h"' in result["imports"]
    
    @pytest.mark.parametrize("source,ds_key,min_count", [
        ("class A { std::vector<int> v; std::vector<string> s; };", "arrays", 2),
        ("class A { std::map<int,int> m; std::unordered_map<int,int> u; };", "hash_tables", 2),
        ("class A { void f() { int* p = new int; delete p; } };", "dynamic_memory", 2),
    ])
    def test_data_structures(self, analyzer, source, ds_key, min_count):
        result = analyze(analyzer, source)
        assert result["data_structures"][ds_key] >= min_count
    
    def test_complexity_metrics(self, analyzer):
        source = "void f() {} void g() { for(int i=0;i<10;i++) { for(int j=0;j<10;j++) {} } }"
        result = analyze(analyzer, source)
        assert result["complexity"]["total_functions"] >= 2
        assert result["complexity"]["functions_with_nested_loops"] >= 1
        assert result["complexity"]["max_loop_depth"] >= 2
    
    @pytest.mark.parametrize("source,spec_key,min_count", [
        ("template<typename T> class C { T data; };", "template_classes", 1),
        ("namespace A {} namespace B {}", "namespaces", 2),
        ("class A { std::unique_ptr<int> p; std::shared_ptr<int> s; };", "smart_pointers", 2),
        ("class A { virtual void f() = 0; };", "abstract_classes", 1),
        ("class A { ~A(); }; class B { ~B(); };", "raii_classes", 2),
    ])
    def test_cpp_specific_features(self, analyzer, source, spec_key, min_count):
        result = analyze(analyzer, source)
        assert result["cpp_spec"][spec_key] >= min_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

