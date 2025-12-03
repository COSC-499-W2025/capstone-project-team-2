from pathlib import Path
from typing import Dict, Any
import json
import sys

# Add parent to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.python_analyzer import PythonOOPAstAnalyzer, ClassInfo   
from src.java_analyzer import analyze_source as analyze_java_source, per_file_to_classinfo_list

def merge_java_ds_into_python(ds: Dict[str, Any], py_analyzer: PythonOOPAstAnalyzer) -> None:
    """
    Map Java analyzer data_structures -> py_analyzer.ds_counts and alg_usage conservatively.
    Modify py_analyzer in-place.
    """
    if not ds:
        return

    # basic mappings: increment python counters where appropriate
    if ds.get("list_literals", 0):
        py_analyzer.ds_counts["list_literals"] += ds.get("list_literals", 0)
    if ds.get("dict_literals", 0):
        py_analyzer.ds_counts["dict_literals"] += ds.get("dict_literals", 0)
    if ds.get("set_literals", 0):
        py_analyzer.ds_counts["set_literals"] += ds.get("set_literals", 0)

    # advanced flags: alg_usage keys where it makes sense
    if ds.get("uses_heapq", False):
        py_analyzer.alg_usage["uses_heapq"] = True
    if ds.get("uses_sorted", False):
        py_analyzer.alg_usage["uses_sorted"] = True
        
    # bisect/defaultdict/counter not directly applicable to Java, but keeping keys untouched.

def merge_java_complexity_into_python(cx: Dict[str, Any], py_analyzer: PythonOOPAstAnalyzer) -> None:
    """
    Merge complexity signals from Java analyzer into the Python analyzer's complexity_stats.
    """
    if not cx:
        return

    py_analyzer.complexity_stats["total_functions"] += cx.get("total_functions", 0)
    py_analyzer.complexity_stats["functions_with_nested_loops"] += cx.get("functions_with_nested_loops", 0)
    py_analyzer.complexity_stats["max_loop_depth"] = max(
        py_analyzer.complexity_stats.get("max_loop_depth", 0),
        cx.get("max_loop_depth", 0),
    )

def merge_java_classinfos_into_python(per_file_metrics: Dict[str, Any], py_analyzer: PythonOOPAstAnalyzer) -> None:
    """
    Convert Java per-file metrics to ClassInfo dataclass instances and append to py_analyzer.class_infos.
    Uses per_file_to_classinfo_list helper from java analyzer which returns ClassInfo-like objects.
    """
    try:
        cis = per_file_to_classinfo_list(per_file_metrics, ClassInfo)
    except Exception:
        # Fallback: manual conversion if helper fails
        cis = []
        for ci in per_file_metrics.get("class_infos", []):
            cis.append(ClassInfo(
                name=ci.get("name", "<anon>"),
                module=ci.get("module", ""),
                file_path=Path(ci.get("file_path", per_file_metrics.get("file", "<unknown>"))),
                bases=ci.get("bases", []),
                methods=set(ci.get("methods", [])),
                has_init=ci.get("has_init", False),
                dunder_methods=ci.get("dunder_count", 0),
                private_attrs=set(ci.get("private_attrs", [])),
                public_attrs=set(ci.get("public_attrs", [])),
            ))
    py_analyzer.class_infos.extend(cis)

class MultiLangOrchestrator:
    """
    Orchestrator that runs the Python AST analyzer + Java analyzer, merges signals, and returns metrics in the same format as PythonOOPAstAnalyzer.compute_metrics().
    """

    def __init__(self, project_root: str | Path):
        self.root = Path(project_root).resolve()
        self.py_analyzer = PythonOOPAstAnalyzer(self.root)

    def discover_files(self):
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", "env"}
        py_files = []
        java_files = []
        for p in self.root.rglob("*"):
            if any(part in ignore_dirs for part in p.parts):
                continue
            if p.is_file():
                if p.suffix == ".py":
                    py_files.append(p)
                elif p.suffix == ".java":
                    java_files.append(p)
        return py_files, java_files

    def analyze(self) -> Dict[str, Any]:
        py_files, java_files = self.discover_files()

        # Set python files for the python analyzer
        self.py_analyzer.python_files = py_files

        # Analyze Python files
        for p in py_files:
            self.py_analyzer.analyze_file(p)

        # Analyze Java files and merge signals
        for jpath in java_files:
            try:
                src = jpath.read_text(encoding="utf8")
            except Exception:
                continue
            per_file = analyze_java_source(src, jpath)
            # Merge ClassInfo objects
            merge_java_classinfos_into_python(per_file, self.py_analyzer)
            # Merge DS heuristics
            merge_java_ds_into_python(per_file.get("data_structures", {}), self.py_analyzer)
            # Merge complexity stats
            merge_java_complexity_into_python(per_file.get("complexity", {}), self.py_analyzer)
            # Track syntax errors
            if not per_file.get("syntax_ok", True):
                self.py_analyzer.syntax_errors.append(jpath)

        # Compute metrics using the python analyzer's existing compute_metrics method
        metrics = self.py_analyzer.compute_metrics()
        return metrics

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", help="Project root folder to analyze")
    parser.add_argument("--out", help="Write metrics JSON to this file", default=None)
    args = parser.parse_args()

    orch = MultiLangOrchestrator(args.project_root)
    metrics = orch.analyze()
    print(json.dumps(metrics, indent=2))

    if args.out:
        Path(args.out).write_text(json.dumps(metrics, indent=2), encoding="utf8")
