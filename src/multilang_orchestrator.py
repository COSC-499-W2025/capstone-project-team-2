"""
Multi-Language OOP Orchestrator

Analyzes projects containing Python, Java, and C source files,
merging results into a single unified OOP metrics report.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.python_analyzer import PythonOOPAstAnalyzer, ClassInfo
from src.java_analyzer import analyze_source as analyze_java_source, per_file_to_classinfo_list
from src.c_oop_analyzer import analyze_source as analyze_c_source

class MultiLangOrchestrator:
    """Orchestrator for analyzing multi-language (Python + Java + C) projects.
    Merges analysis results into a unified OOP metrics report.
    """

    IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "env"}

    def __init__(self, project_root: str | Path):
        """Initialize with the project root directory."""
        self.root = Path(project_root).resolve()
        self.py_analyzer = PythonOOPAstAnalyzer(self.root)

    def discover_files(self) -> Tuple[List[Path], List[Path], List[Path]]:
        """Discover all Python, Java, and C files, skipping common ignore dirs."""
        py_files, java_files, c_files = [], [], []
        for p in self.root.rglob("*"):
            if any(part in self.IGNORE_DIRS for part in p.parts) or not p.is_file():
                continue
            if p.suffix == ".py":
                py_files.append(p)
            elif p.suffix == ".java":
                java_files.append(p)
            elif p.suffix in (".c", ".h"):
                c_files.append(p)
        return py_files, java_files, c_files

    def _merge_java_file(self, per_file: Dict[str, Any]) -> None:
        """Merge a single Java file's analysis into the Python analyzer."""
        # Merge class infos
        self.py_analyzer.class_infos.extend(
            per_file_to_classinfo_list(per_file, ClassInfo)
        )

        # Merge data structure counts
        ds = per_file.get("data_structures", {})
        for key in ("list_literals", "dict_literals", "set_literals"):
            self.py_analyzer.ds_counts[key] += ds.get(key, 0)
        for key in ("uses_heapq", "uses_sorted"):
            if ds.get(key):
                self.py_analyzer.alg_usage[key] = True

        # Merge complexity stats
        cx = per_file.get("complexity", {})
        self.py_analyzer.complexity_stats["total_functions"] += cx.get("total_functions", 0)
        self.py_analyzer.complexity_stats["functions_with_nested_loops"] += cx.get("functions_with_nested_loops", 0)
        self.py_analyzer.complexity_stats["max_loop_depth"] = max(
            self.py_analyzer.complexity_stats["max_loop_depth"],
            cx.get("max_loop_depth", 0)
        )

    def _merge_c_file(self, per_file: Dict[str, Any]) -> None:
        """Merge a single C file's analysis into the Python analyzer."""
        # Convert C structs to ClassInfo objects
        for struct in per_file.get("classes", []):
            # Count special methods as dunder_methods equivalent
            special_methods = struct.get("special_methods", [])
            class_info = ClassInfo(
                name=struct.get("name", "anonymous"),
                module=struct.get("module", "N/A"),
                file_path=Path(struct.get("file_path", "")),
                bases=struct.get("bases", []),
                methods=set(struct.get("methods", [])),
                has_init=struct.get("has_constructor", False),
                dunder_methods=len(special_methods),
                private_attrs=set(struct.get("private_attrs", [])),
                public_attrs=set(struct.get("public_attrs", [])),
            )
            self.py_analyzer.class_infos.append(class_info)

        # Merge data structure counts
        ds = per_file.get("data_structures", {})
        for key in ("list_literals", "dict_literals", "set_literals"):
            self.py_analyzer.ds_counts[key] += ds.get(key, 0)
        for key in ("uses_heapq", "uses_sorted", "uses_bisect"):
            if ds.get(key):
                self.py_analyzer.alg_usage[key] = True

        # Merge complexity stats
        cx = per_file.get("complexity", {})
        self.py_analyzer.complexity_stats["total_functions"] += cx.get("total_functions", 0)
        self.py_analyzer.complexity_stats["functions_with_nested_loops"] += cx.get("functions_with_nested_loops", 0)
        self.py_analyzer.complexity_stats["max_loop_depth"] = max(
            self.py_analyzer.complexity_stats["max_loop_depth"],
            cx.get("max_loop_depth", 0)
        )

    def analyze(self) -> Dict[str, Any]:
        """Analyze all Python, Java, and C files and return unified OOP metrics."""
        py_files, java_files, c_files = self.discover_files()
        self.py_analyzer.python_files = py_files

        # Analyze Python files
        for p in py_files:
            self.py_analyzer.analyze_file(p)

        # Analyze Java files and merge
        for jpath in java_files:
            try:
                src = jpath.read_text(encoding="utf-8")
            except Exception:
                continue
            per_file = analyze_java_source(src, jpath)
            if per_file.get("syntax_ok", True):
                self._merge_java_file(per_file)
            else:
                self.py_analyzer.syntax_errors.append(jpath)

        # Analyze C files and merge
        for cpath in c_files:
            try:
                src = cpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            per_file = analyze_c_source(src, cpath)
            if per_file.get("syntax_ok", True):
                self._merge_c_file(per_file)
            else:
                self.py_analyzer.syntax_errors.append(cpath)

        return self.py_analyzer.compute_metrics()

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
