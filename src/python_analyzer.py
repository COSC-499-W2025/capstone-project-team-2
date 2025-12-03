"""
Python OOP Analyzer Module

Analyzes Python source files for object-oriented programming patterns, data structure usage, and code complexity metrics using the AST module.
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any
import sys
from collections import defaultdict

# Add parent to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.oop_aggregator import aggregate_canonical_reports
from src.oop_aggregator import build_narrative

@dataclass
class ClassInfo:
    """
    Holds OOP-related information for a single Python class.
    
    Attributes:
        name: Class name.
        module: Module path 
        file_path: Path to the source file.
        bases: List of base class names.
        methods: Set of method names defined in the class.
        has_init: Whether the class has an __init__ method.
        dunder_methods: Count of dunder methods 
        private_attrs: Set of private attributes 
        public_attrs: Set of public attributes.
    """
    
    name: str
    module: str
    file_path: Path
    bases: List[str] = field(default_factory=list)
    methods: Set[str] = field(default_factory=set)
    has_init: bool = False
    dunder_methods: int = 0
    private_attrs: Set[str] = field(default_factory=set)
    public_attrs: Set[str] = field(default_factory=set)

class ClassVisitor(ast.NodeVisitor):
    """
    AST visitor that collects class definitions and OOP signals.
    
    Walks the AST to find class definitions, extract inheritance info,
    method names, and attribute assignments.
    """

    def __init__(self, file_path: Path, module_name: str):
        """Initialize the visitor with file path and module name."""
        self.file_path = file_path
        self.module_name = module_name
        self.classes: List[ClassInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        """Process a class definition node and extract OOP information."""
        bases = []
        for b in node.bases:
            # Handle simple cases: BaseClass, module.BaseClass
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                # something.BaseClass - take the attr name
                bases.append(b.attr)
            else:
                # For complex expressions
                bases.append("<expr>")

        info = ClassInfo(
            name=node.name,
            module=self.module_name,
            file_path=self.file_path,
            bases=bases,
        )

        for stmt in node.body:
            # Methods
            if isinstance(stmt, ast.FunctionDef):
                info.methods.add(stmt.name)
                if stmt.name == "__init__":
                    info.has_init = True
                if stmt.name.startswith("__") and stmt.name.endswith("__"):
                    info.dunder_methods += 1

                # look for attribute assignments to self inside methods
                self.collect_attr_assignments(info, stmt)

        self.classes.append(info)
        # Continue visiting nested classes
        self.generic_visit(node)

    def collect_attr_assignments(self, info: ClassInfo, func: ast.FunctionDef) -> None:
        
        """
        Look for `self.x = value` inside a method to approximate encapsulation and attribute design.
        """
        for node in ast.walk(func):
            # `self.foo = ...`
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    self.record_attr_target(info, target)
            elif isinstance(node, ast.AnnAssign):
                # `self.foo: int = 3`
                self.record_attr_target(info, node.target)

    def record_attr_target(self, info: ClassInfo, target: ast.AST) -> None:
        """Record an attribute assignment to self as private or public."""
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            if target.value.id == "self":  # self.<attr>
                attr_name = target.attr
                if attr_name.startswith("_") and not attr_name.startswith("__"):
                    info.private_attrs.add(attr_name)
                else:
                    info.public_attrs.add(attr_name)
                    
class _DataStructureAndComplexityVisitor(ast.NodeVisitor):
    """
    AST visitor that collects data structure usage and complexity metrics.
    
    Tracks:
        - Literal counts: lists, dicts, sets, tuples
        - Comprehension counts: list/dict/set comprehensions
        - Advanced structures: defaultdict, Counter, heapq, bisect
        - Complexity: nested loop depth, function counts
    """
    
    def __init__(self) -> None:
        """Initialize counters and flags for data structure tracking."""
        
        # Data structure counts
        self.list_literals = 0
        self.dict_literals = 0
        self.set_literals = 0
        self.tuple_literals = 0
        self.list_comprehensions = 0
        self.dict_comprehensions = 0
        self.set_comprehensions = 0

        # Advanced structures / algorithms
        self.uses_defaultdict = False
        self.uses_counter = False
        self.uses_heapq = False
        self.uses_bisect = False
        self.uses_sorted = False

        # Complexity signals
        self.total_functions = 0
        self.functions_with_nested_loops = 0
        self.max_loop_depth_overall = 0

    # Data structure 
    def visit_List(self, node: ast.List) -> Any:
        self.list_literals += 1
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> Any:
        self.dict_literals += 1
        self.generic_visit(node)

    def visit_Set(self, node: ast.Set) -> Any:
        self.set_literals += 1
        self.generic_visit(node)

    def visit_Tuple(self, node: ast.Tuple) -> Any:
        self.tuple_literals += 1
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> Any:
        self.list_comprehensions += 1
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> Any:
        self.dict_comprehensions += 1
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> Any:
        self.set_comprehensions += 1
        self.generic_visit(node)

    # Imports 
    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = node.module or ""
        if module.startswith("collections"):
            for alias in node.names:
                if alias.name == "defaultdict":
                    self.uses_defaultdict = True
                if alias.name == "Counter":
                    self.uses_counter = True
        if module == "heapq":
            self.uses_heapq = True
        if module == "bisect":
            self.uses_bisect = True
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            name = alias.name
            if name == "heapq":
                self.uses_heapq = True
            if name == "bisect":
                self.uses_bisect = True
            if name.startswith("collections"):
                # generic collections usage, could be collections.defaultdict, collections.Counter, etc.
                pass
        self.generic_visit(node)

    # complexity 
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.total_functions += 1
        max_depth = self._max_loop_depth(node)
        self.max_loop_depth_overall = max(self.max_loop_depth_overall, max_depth)
        if max_depth >= 2:
            self.functions_with_nested_loops += 1
        self.generic_visit(node)

    def _max_loop_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        
        """
        measure max nesting of for/while loops inside a function.
        """
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                depth = self._max_loop_depth(child, current_depth + 1)
            else:
                depth = self._max_loop_depth(child, current_depth)
            if depth > max_depth:
                max_depth = depth
        return max_depth

    # Advanced algorithms usage
    def visit_Call(self, node: ast.Call) -> Any:
        func = node.func
        # sorted(...)
        if isinstance(func, ast.Name) and func.id == "sorted":
            self.uses_sorted = True

        # heapq.*(...)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "heapq":
                self.uses_heapq = True
        self.generic_visit(node)
        
class PythonOOPAstAnalyzer:
    """
    Analyze Python OOP usage in a project directory using the built-in AST.
    
    Produces a normalized OOP score in [0, 1] plus a textual summary.
    Also tracks data structure usage and code complexity metrics.
    
    Usage:
        analyzer = PythonOOPAstAnalyzer(Path('/path/to/project'))
        metrics = analyzer.analyze()
    """
    
    def __init__(self, root: Path):
        """Initialize the analyzer with a project root directory."""
        self.root = Path(root).resolve()
        self.python_files: List[Path] = []
        self.class_infos: List[ClassInfo] = []
        self.syntax_errors: List[Path] = []
        
        self.ds_counts: Dict[str, int] = {
            "list_literals": 0,
            "dict_literals": 0,
            "set_literals": 0,
            "tuple_literals": 0,
            "list_comprehensions": 0,
            "dict_comprehensions": 0,
            "set_comprehensions": 0,
        }
        self.alg_usage: Dict[str, bool] = {
            "uses_defaultdict": False,
            "uses_counter": False,
            "uses_heapq": False,
            "uses_bisect": False,
            "uses_sorted": False,
        }
        self.complexity_stats: Dict[str, Any] = {
            "total_functions": 0,
            "functions_with_nested_loops": 0,
            "max_loop_depth": 0,
        }

    def discover_python_files(self) -> None:
        """
        Collect all .py files under root, skipping some common dirs.
        """
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", "env"}
        self.python_files = []

        for path in self.root.rglob("*.py"):
            if any(part in ignore_dirs for part in path.parts):
                continue
            self.python_files.append(path)

    def analyze_file(self, path: Path) -> None:
        """
        Parse and analyze a single Python file.
        
        Extracts class info, data structure usage, and complexity metrics.
        Files with syntax errors are recorded but not analyzed.
        """
        try:
            src = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError:
            self.syntax_errors.append(path)
            return

        try:
            rel = path.relative_to(self.root)
            module_name = ".".join(rel.with_suffix("").parts)
        except ValueError:
            module_name = path.stem

        visitor = ClassVisitor(path, module_name)
        visitor.visit(tree)
        self.class_infos.extend(visitor.classes)
        
        ds_visitor = _DataStructureAndComplexityVisitor()
        ds_visitor.visit(tree)
        self._accumulate_ds_and_complexity(ds_visitor)
        
    def _accumulate_ds_and_complexity(self, v: _DataStructureAndComplexityVisitor) -> None:
        """Accumulate data structure and complexity stats from a visitor."""
        # Data structure counts
        for key in self.ds_counts:
            self.ds_counts[key] += getattr(v, key)

        # Algorithm usage flags (OR them together)
        for key in self.alg_usage:
            self.alg_usage[key] = self.alg_usage[key] or getattr(v, key)

        # Complexity aggregation
        self.complexity_stats["total_functions"] += v.total_functions
        self.complexity_stats["functions_with_nested_loops"] += v.functions_with_nested_loops
        self.complexity_stats["max_loop_depth"] = max(
            self.complexity_stats["max_loop_depth"],
            v.max_loop_depth_overall,
        )
        
    def to_canonical_reports(self) -> List[Dict[str, Any]]:
        """Convert class_infos into canonical per-file reports for the aggregator."""
        files_map = defaultdict(list)
        for ci in self.class_infos:
            files_map[str(ci.file_path)].append(ci)

        reports = []
        for file_path, class_list in files_map.items():
            reports.append({
                "file": file_path,
                "module": class_list[0].module if class_list else "",
                "classes": [_classinfo_to_canonical_class(ci) for ci in class_list],
                "data_structures": {},
                "complexity": {},
                "syntax_ok": True,
            })
        return reports
    
    def compute_metrics(self) -> Dict[str, Any]:
        """Delegate scoring to aggregator, then inject project-level stats."""
        canonical_reports = self.to_canonical_reports()
        metrics = aggregate_canonical_reports(canonical_reports, total_files=len(self.python_files))

        # Inject project-level data structures
        metrics["data_structures"] = {
            **self.ds_counts,
            "uses_defaultdict": self.alg_usage["uses_defaultdict"],
            "uses_counter": self.alg_usage["uses_counter"],
        }

        # Inject project-level complexity
        total_funcs = self.complexity_stats["total_functions"]
        nested = self.complexity_stats["functions_with_nested_loops"]
        metrics["complexity"] = {
            "total_functions": total_funcs,
            "functions_with_nested_loops": nested,
            "nested_loop_ratio": round(nested / total_funcs, 2) if total_funcs else 0.0,
            "max_loop_depth": self.complexity_stats["max_loop_depth"],
            "uses_sorted": self.alg_usage["uses_sorted"],
            "uses_heapq": self.alg_usage["uses_heapq"],
            "uses_bisect": self.alg_usage["uses_bisect"],
        }

        # Add syntax errors
        metrics.setdefault("syntax_errors", []).extend(str(p) for p in self.syntax_errors)
        
        # Rebuild narrative with updated data_structures and complexity
        metrics["narrative"] = build_narrative(metrics)
        
        return metrics
    
    def analyze(self) -> Dict[str, Any]:
        """Run the analysis pipeline and return computed metrics."""
        if not self.python_files:
            self.discover_python_files()
        
        # Reset state
        self.class_infos = []
        self.syntax_errors = []
        self.ds_counts = {k: 0 for k in self.ds_counts}
        self.alg_usage = {k: False for k in self.alg_usage}
        self.complexity_stats = {k: 0 for k in self.complexity_stats}

        # Analyze each file
        for f in self.python_files:
            self.analyze_file(f)

        return self.compute_metrics()
    
def analyze_python_project_oop(root: str | Path) -> Dict[str, Any]:
    """
    Analyze a Python project for OOP usage and return metrics.
    
    Args:
        root: Path to the project root directory.
        
    Returns:
        Dict containing OOP score, rating, class details, data structures,
        complexity stats, and any syntax errors found.
    """
    analyzer = PythonOOPAstAnalyzer(Path(root))
    return analyzer.analyze()

def _classinfo_to_canonical_class(ci: ClassInfo) -> Dict[str, Any]:
    """
    Convert a ClassInfo dataclass to a canonical class dictionary.
    
    Args:
        ci: ClassInfo object containing class metadata.
        
    Returns:
        Dict with standardized keys for class name, bases, methods, etc.
    """
    # special_methods: for Python collect dunder method names present in methods set
    special_methods = [m for m in ci.methods if m.startswith("__") and m.endswith("__")]
    return {
        "name": ci.name,
        "bases": list(ci.bases),
        "methods": sorted(list(ci.methods)),
        "has_constructor": ci.has_init,
        "special_methods": special_methods,
        "private_attrs": sorted(list(ci.private_attrs)),
        "public_attrs": sorted(list(ci.public_attrs)),
    }

