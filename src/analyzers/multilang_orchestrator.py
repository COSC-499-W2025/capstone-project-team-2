"""
Multi-Language OOP Orchestrator

Analyzes projects containing Python, Java, Javascript, C, C++ and C# source files,
merging results into a single unified OOP metrics report.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import json

from src.analyzers.c.c_oop_analyzer import analyze_source as analyze_c_source
from src.analyzers.c.cpp_analyzer import cppanalysis
from src.analyzers.c.csharp_analyzer import csharpanalysis
from src.analyzers.python.python_oop_analyzer import PythonOOPAstAnalyzer
from src.analyzers.java.java_analyzer import analyze_source as analyze_java_source, per_file_to_classinfo_list
from src.analyzers.javascript.javascript_oop_analyzer import JavaScriptOOPAnalyzer
from src.aggregation.oop_aggregator import aggregate_canonical_reports, combine_language_metrics

class MultiLangOrchestrator:
    """Orchestrator for analyzing multi-language (Python + Java + C + Javascript + C# + C++) projects.
    Merges analysis results into a unified OOP metrics report.
    """

    IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "env"}

    def __init__(self, project_root: str | Path):
        """Initialize with the project root directory."""
        self.root = Path(project_root).resolve()
        self.py_analyzer = PythonOOPAstAnalyzer(self.root)
        self.js_analyzer = JavaScriptOOPAnalyzer(self.root)

    def discover_files(self) -> Tuple[List[Path], List[Path], List[Path], List[Path], List[Path], List[Path]]:
        """
        Discover all Python, Java, JavaScript, C, C++, and C# files, skipping common ignore dirs.

        Args:
            None

        Returns:
            Tuple[List[Path], List[Path], List[Path], List[Path], List[Path], List[Path]]:
                Six lists containing discovered Python, Java, JavaScript,
                C/C header files, C++ files, and C# files, respectively.
        """
        
        py_files, java_files, js_files, c_files, cpp_files, cs_files = [], [], [], [], [], []

        for p in self.root.rglob("*"):
            if any(part in self.IGNORE_DIRS for part in p.parts) or not p.is_file():
                continue
            if p.suffix == ".py":
                py_files.append(p)
            elif p.suffix == ".java":
                java_files.append(p)
            elif p.suffix == ".js":
                js_files.append(p)
            elif p.suffix in (".c", ".h"):
                c_files.append(p)
            elif p.suffix in (".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"):
                cpp_files.append(p)
            elif p.suffix == ".cs":
                cs_files.append(p)

        return py_files, java_files, js_files, c_files, cpp_files, cs_files

    def analyze(self) -> Dict[str, Any]:
        """Analyze all Python, Java, Javascript, C, C++, and C# files and return unified OOP metrics.
        
        Args:
            None

        Returns:
            Dict[str, Any]: A dictionary containing unified object-oriented
                programming metrics computed across all analyzed source files.
        """
        py_files, java_files, js_files, c_files, cpp_files, cs_files = self.discover_files()

        language_metrics: Dict[str, Dict[str, Any]] = {}
        total_files = (
            len(py_files)
            + len(java_files)
            + len(js_files)
            + len(c_files)
            + len(cpp_files)
            + len(cs_files)
        )

        # Analyze Python files
        self.py_analyzer.python_files = py_files
        for p in py_files:
            self.py_analyzer.analyze_file(p)
        if py_files:
            py_metrics = self.py_analyzer.compute_metrics()
            py_metrics["language"] = "Python"
            language_metrics["Python"] = py_metrics

        # Analyze Java files
        if java_files:
            java_reports = []
            for jpath in java_files:
                try:
                    src = jpath.read_text(encoding="utf-8")
                except Exception:
                    continue
                per_file = analyze_java_source(src, jpath)
                java_reports.append(per_file)
            java_metrics = aggregate_canonical_reports(java_reports, total_files=len(java_files))
            java_metrics["language"] = "Java"
            language_metrics["Java"] = java_metrics

        # Analyze JavaScript files
        if js_files:
            js_metrics = self.js_analyzer.analyze()
            js_metrics["language"] = "JavaScript"
            language_metrics["JavaScript"] = js_metrics

        # Analyze C files
        if c_files:
            c_reports = []
            for cpath in c_files:
                try:
                    src = cpath.read_text(encoding="utf-8", errors="ignore")
                    per_file = analyze_c_source(src, cpath)
                    c_reports.append(per_file)
                except Exception as e:
                    c_reports.append({
                        "file": str(cpath),
                        "module": "",
                        "classes": [],
                        "imports": [],
                        "data_structures": {},
                        "complexity": {},
                        "syntax_ok": False,
                        "syntax_error": str(e),
                        "c_spec": {},
                    })
            c_metrics = aggregate_canonical_reports(c_reports, total_files=len(c_files))
            c_metrics["language"] = "C"
            language_metrics["C"] = c_metrics

        # Analyze C++ files
        if cpp_files:
            cpp_reports = []
            cpp_analyzer = cppanalysis()
            for cpp_path in cpp_files:
                try:
                    src = cpp_path.read_text(encoding="utf-8", errors="ignore")
                    cpp_reports.append(cpp_analyzer.analyze_file(src, cpp_path))
                except Exception as e:
                    cpp_reports.append({
                        "file": str(cpp_path),
                        "module": "",
                        "classes": [],
                        "imports": [],
                        "data_structures": {},
                        "complexity": {},
                        "cpp_spec": {},
                        "syntax_ok": False,
                        "error": str(e),
                    })
            cpp_metrics = aggregate_canonical_reports(cpp_reports, total_files=len(cpp_files))
            cpp_metrics["language"] = "C++"
            language_metrics["C++"] = cpp_metrics

        # Analyze C# files
        if cs_files:
            cs_reports = []
            cs_analyzer = csharpanalysis()
            for cs_path in cs_files:
                try:
                    src = cs_path.read_text(encoding="utf-8", errors="ignore")
                    cs_reports.append(cs_analyzer.analyze_file(src, cs_path))
                except Exception as e:
                    cs_reports.append({
                        "file": str(cs_path),
                        "module": "",
                        "classes": [],
                        "imports": [],
                        "data_structures": {},
                        "complexity": {},
                        "syntax_ok": False,
                        "error": str(e),
                    })
            cs_metrics = aggregate_canonical_reports(cs_reports, total_files=len(cs_files))
            cs_metrics["language"] = "C#"
            language_metrics["C#"] = cs_metrics

        if not language_metrics:
            return aggregate_canonical_reports([], total_files=0)
        if len(language_metrics) == 1:
            return next(iter(language_metrics.values()))
        return combine_language_metrics(language_metrics, total_files=total_files)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze Python + Java projects")
    parser.add_argument("project_root", help="Project root folder to analyze")
    parser.add_argument("--out", help="Write metrics JSON to this file")
    args = parser.parse_args()

    metrics = MultiLangOrchestrator(args.project_root).analyze()
    print(json.dumps(metrics, indent=2))

    if args.out:
        Path(args.out).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
