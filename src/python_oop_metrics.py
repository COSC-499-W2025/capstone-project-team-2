import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any

@dataclass
class ClassInfo:
    
    """Holds OOP-related information for a single Python class."""
    
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
    """Collects class definitions and basic OOP signals."""

    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.classes: List[ClassInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
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
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            if target.value.id == "self":  # self.<attr>
                attr_name = target.attr
                if attr_name.startswith("_") and not attr_name.startswith("__"):
                    info.private_attrs.add(attr_name)
                else:
                    info.public_attrs.add(attr_name)
                    
class _DataStructureAndComplexityVisitor(ast.NodeVisitor):
    """
    Collects data structure usage and rough complexity signals.
    """
    
    def __init__(self) -> None:
        
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
    Produces a normalized OOP score in [0, 1] + short textual summary.
    """
    
    def __init__(self, root: Path):
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

        for path in self.root.rglob("*.py"):
            if any(part in ignore_dirs for part in path.parts):
                continue
            self.python_files.append(path)
            
    def analyze_file(self, path: Path) -> None:
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
        
    # Accumulate data structure and complexity stats
    def _accumulate_ds_and_complexity(self, v: _DataStructureAndComplexityVisitor) -> None:
        
        self.ds_counts["list_literals"] += v.list_literals
        self.ds_counts["dict_literals"] += v.dict_literals
        self.ds_counts["set_literals"] += v.set_literals
        self.ds_counts["tuple_literals"] += v.tuple_literals
        self.ds_counts["list_comprehensions"] += v.list_comprehensions
        self.ds_counts["dict_comprehensions"] += v.dict_comprehensions
        self.ds_counts["set_comprehensions"] += v.set_comprehensions

        for key in self.alg_usage:
            self.alg_usage[key] = self.alg_usage[key] or getattr(v, key)

        # Complexity aggregation
        self.complexity_stats["total_functions"] += v.total_functions
        self.complexity_stats["functions_with_nested_loops"] += v.functions_with_nested_loops
        self.complexity_stats["max_loop_depth"] = max(
            self.complexity_stats["max_loop_depth"],
            v.max_loop_depth_overall,
        )

    def compute_metrics(self) -> Dict[str, Any]:
        n_files = len(self.python_files)
        n_classes = len(self.class_infos)
        
        # Complexity ratios
        total_funcs = self.complexity_stats["total_functions"]
        nested = self.complexity_stats["functions_with_nested_loops"]
        nested_ratio = (nested / total_funcs) if total_funcs > 0 else 0.0
        
        # Helper to build DS + complexity sections
        data_structures_section = {
            "list_literals": self.ds_counts["list_literals"],
            "dict_literals": self.ds_counts["dict_literals"],
            "set_literals": self.ds_counts["set_literals"],
            "tuple_literals": self.ds_counts["tuple_literals"],
            "list_comprehensions": self.ds_counts["list_comprehensions"],
            "dict_comprehensions": self.ds_counts["dict_comprehensions"],
            "set_comprehensions": self.ds_counts["set_comprehensions"],
            "uses_defaultdict": self.alg_usage["uses_defaultdict"],
            "uses_counter": self.alg_usage["uses_counter"],
        }
        
        complexity_section = {
            "total_functions": total_funcs,
            "functions_with_nested_loops": nested,
            "nested_loop_ratio": round(nested_ratio, 2),
            "max_loop_depth": self.complexity_stats["max_loop_depth"],
            "uses_sorted": self.alg_usage["uses_sorted"],
            "uses_heapq": self.alg_usage["uses_heapq"],
            "uses_bisect": self.alg_usage["uses_bisect"],
        }

        if n_classes == 0:
            return {
                "files_analyzed": n_files,
                "classes": {
                    "count": 0,
                    "avg_methods_per_class": 0.0,
                    "with_inheritance": 0,
                    "with_init": 0,
                },
                "encapsulation": {
                    "classes_with_private_attrs": 0,
                },
                "polymorphism": {
                    "classes_overriding_base_methods": 0,
                    "override_method_count": 0,
                },
                "special_methods": {
                    "classes_with_multiple_dunders": 0,
                },
                "data_structures": data_structures_section,   # data structures
                "complexity": complexity_section,              # complexity
                "score": {
                    "oop_score": 0.0,
                    "rating": "none",
                    "comment": (
                        "No Python classes were found in this project, so OOP "
                        "usage appears minimal or absent."
                    ),
                },
                "syntax_errors": [str(p) for p in self.syntax_errors],
            }

        # Basic class/method stats 
        total_methods = sum(len(ci.methods) for ci in self.class_infos)
        avg_methods = total_methods / n_classes if n_classes else 0.0

        inheritance_classes = 0
        classes_with_init = 0
        dunder_rich = 0
        private_attr_classes = 0

        # First pass: compute per-class basics 
        for ci in self.class_infos:
            # Inheritance usage 
            if ci.bases and not (len(ci.bases) == 1 and ci.bases[0] in {"object", "<expr>"}):
                inheritance_classes += 1

            if ci.has_init:
                classes_with_init += 1

            if ci.dunder_methods >= 2:
                dunder_rich += 1

            if ci.private_attrs:
                private_attr_classes += 1

        # Polymorphism: method overrides 
        methods_by_class: Dict[str, Set[str]] = {}
        for ci in self.class_infos:
            # Key by simple class name; if duplicates exist across modules, merge methods by name
            methods_by_class.setdefault(ci.name, set()).update(ci.methods)

        override_classes = 0
        override_method_count = 0

        for ci in self.class_infos:
            base_method_union: Set[str] = set()
            for base in ci.bases:
                if base in methods_by_class:
                    base_method_union |= methods_by_class[base]

            overrides = ci.methods & base_method_union
            if overrides:
                override_classes += 1
                override_method_count += len(overrides)

        # Score calculation (0–1)

        # 1. richness: up to 5 methods/class - 1.0
        richness = min(avg_methods / 5.0, 1.0)

        # 2. inheritance usage
        inheritance_ratio = inheritance_classes / n_classes if n_classes else 0.0

        # 3. encapsulation: private attrs per class
        encapsulation_ratio = private_attr_classes / n_classes if n_classes else 0.0

        # 4. polymorphism: overrides per inheritance-using class
        if inheritance_classes > 0:
            polymorphism_ratio = override_classes / inheritance_classes
        else:
            polymorphism_ratio = 0.0

        # 5. dunder richness
        dunder_ratio = dunder_rich / n_classes if n_classes else 0.0

        # Weighted combination
        oop_score = (
            0.30 * richness +
            0.20 * inheritance_ratio +
            0.20 * encapsulation_ratio +
            0.20 * polymorphism_ratio +
            0.10 * dunder_ratio
        )

        oop_score = max(0.0, min(1.0, oop_score))

        # Textual rating and comment
        if oop_score < 0.3:
            rating = "low"
            comment = (
                "The project shows limited use of object-oriented design. "
                "There are some classes, but inheritance, encapsulation, and polymorphism are either absent or lightly used."
            )
        elif oop_score < 0.6:
            rating = "medium"
            comment = (
                "The project demonstrates moderate OOP usage. Classes and methods "
                "are present, with some inheritance or encapsulation, but there is still room to deepen abstraction and polymorphism."
            )
        else:
            rating = "high"
            comment = (
                "The project exhibits strong object-oriented design: classes are well-used, inheritance and method overriding appear, and there are "
                "signs of encapsulation and expressive interfaces."
            )

        metrics = {
            "files_analyzed": n_files,
            "classes": {
                "count": n_classes,
                "avg_methods_per_class": round(avg_methods, 2),
                "with_inheritance": inheritance_classes,
                "with_init": classes_with_init,
            },
            "encapsulation": {
                "classes_with_private_attrs": private_attr_classes,
            },
            "polymorphism": {
                "classes_overriding_base_methods": override_classes,
                "override_method_count": override_method_count,
            },
            "special_methods": {
                "classes_with_multiple_dunders": dunder_rich,
            },
            "data_structures": data_structures_section,   
            "complexity": complexity_section,   
            "score": {
                "oop_score": round(oop_score, 2),  # 0–1
                "rating": rating,
                "comment": comment,
            },
            "syntax_errors": [str(p) for p in self.syntax_errors],
        }
        
        metrics["narrative"] = build_narrative(metrics)
        return metrics

    def analyze(self) -> Dict[str, Any]:
        """
        Run the analysis pipeline and return the metrics dictionary.
        """
        self.discover_python_files()
        for f in self.python_files:
            self.analyze_file(f)
        return self.compute_metrics()
    
def build_narrative(metrics: Dict[str, Any]) -> Dict[str, str]:

    """
    Build human-readable narrative insights from the raw metrics.
    """
    classes = metrics["classes"]
    encaps = metrics["encapsulation"]
    poly = metrics["polymorphism"]
    special = metrics["special_methods"]
    ds = metrics.get("data_structures", {})
    cx = metrics.get("complexity", {})
    score = metrics["score"]["oop_score"]

    # OOP narrative 
    n_classes = classes["count"]
    oop_lines: List[str] = []

    if n_classes == 0:
        oop_lines.append(
            "No classes were detected in the repository, so the codebase is primarily procedural "
            "and does not demonstrate object-oriented abstraction in this artifact."
        )
    else:
        oop_lines.append(
            f"The project defines {n_classes} class(es) with an average of "
            f"{classes['avg_methods_per_class']} method(s) per class."
        )

        if classes["with_inheritance"] == 0:
            oop_lines.append(
                "None of the classes use inheritance, so the author is not relying on subclassing "
                "for code reuse or specialization in this codebase."
            )
        else:
            oop_lines.append(
                f"{classes['with_inheritance']} class(es) use inheritance, indicating some use "
                "of hierarchical relationships between types."
            )

        if classes["with_init"] == 0:
            oop_lines.append(
                "No classes define their own __init__ methods, which suggests limited custom "
                "initialization or stateful objects in this artifact."
            )

        if encaps["classes_with_private_attrs"] == 0:
            oop_lines.append(
                "There is no evidence of encapsulation via private attributes (self._name style), "
                "so information hiding is not a major focus here."
            )
        else:
            oop_lines.append(
                f"Encapsulation is present: {encaps['classes_with_private_attrs']} class(es) use "
                "private attributes to hide internal state."
            )

        if poly["classes_overriding_base_methods"] == 0:
            oop_lines.append(
                "None of the classes override methods from their base classes, indicating little "
                "use of polymorphism in this code."
            )
        else:
            oop_lines.append(
                f"{poly['classes_overriding_base_methods']} class(es) override "
                f"{poly['override_method_count']} inherited method(s), which is direct evidence of "
                "polymorphism."
            )

        if special["classes_with_multiple_dunders"] > 0:
            oop_lines.append(
                f"{special['classes_with_multiple_dunders']} class(es) implement multiple "
                "special/dunder methods, suggesting more expressive class interfaces."
            )

        # overall OOP interpretation based on score
        if score < 0.3:
            oop_lines.append(
                "Overall, the OOP score is low, so this artifact shows only limited use of object-oriented design beyond basic class definitions."
            )
        elif score < 0.6:
            oop_lines.append(
                "Overall, the OOP score is moderate, indicating some use of object-oriented ideas but still with room for deeper abstraction and polymorphism."
            )
        else:
            oop_lines.append(
                "The high OOP score indicates strong, deliberate use of object-oriented design in this artifact."
            )

    oop_narrative = " ".join(oop_lines)

    # Data structure narrative 
    ds_lines: List[str] = []
    list_count = ds.get("list_literals", 0)
    dict_count = ds.get("dict_literals", 0)
    set_count = ds.get("set_literals", 0)
    tuple_count = ds.get("tuple_literals", 0)
    list_comps = ds.get("list_comprehensions", 0)
    dict_comps = ds.get("dict_comprehensions", 0)
    set_comps = ds.get("set_comprehensions", 0)

    total_literal_collections = list_count + dict_count + set_count + tuple_count

    if total_literal_collections == 0:
        ds_lines.append(
            "The analysis did not detect any collection literals, so data structure usage is minimal in this artifact."
        )
    else:
        ds_lines.append(
            f"The code uses {total_literal_collections} collection literal(s): "
            f"{list_count} list(s), {dict_count} dict(s), {set_count} set(s), "
            f"and {tuple_count} tuple(s)."
        )

        if list_count > 0 and dict_count == 0 and set_count == 0:
            ds_lines.append(
                "Lists are used exclusively for collections, which suggests the author primarily "
                "relies on sequential data rather than hash-based lookups or set semantics."
            )
        elif dict_count > 0 or set_count > 0:
            ds_lines.append(
                "The presence of dictionaries and/or sets indicates some awareness of using hash "
                "maps or sets when appropriate for key-based access or membership tests."
            )

        if list_comps + dict_comps + set_comps > 0:
            ds_lines.append(
                f"The author uses {list_comps} list comprehension(s), {dict_comps} dict "
                f"comprehension(s), and {set_comps} set comprehension(s), which shows familiarity "
                "with Python's concise, functional-style collection construction."
            )

        if ds.get("uses_defaultdict", False) or ds.get("uses_counter", False):
            parts = []
            if ds.get("uses_defaultdict", False):
                parts.append("defaultdict")
            if ds.get("uses_counter", False):
                parts.append("Counter")
            ds_lines.append(
                "Use of collections." + " and ".join(parts) +
                " suggests the author is comfortable choosing specialized data structures for "
                "counting or grouping tasks."
            )
        else:
            ds_lines.append(
                "No usage of collections.defaultdict or collections.Counter was detected, so the "
                "code stays with more basic built-in structures rather than specialized helpers."
            )

    ds_narrative = " ".join(ds_lines)

    # Complexity / algorithm narrative 
    cx_lines: List[str] = []
    total_funcs = cx.get("total_functions", 0)
    nested_funcs = cx.get("functions_with_nested_loops", 0)
    nested_ratio = cx.get("nested_loop_ratio", 0.0)
    max_depth = cx.get("max_loop_depth", 0)

    if total_funcs == 0:
        cx_lines.append(
            "No functions were detected for complexity analysis, so we cannot infer much about algorithmic design from this artifact."
        )
    else:
        cx_lines.append(
            f"The analyzer examined {total_funcs} function(s); {nested_funcs} of them contain "
            f"nested loops (nested loop ratio {nested_ratio:.2f}, max depth {max_depth})."
        )

        if nested_funcs == 0:
            cx_lines.append(
                "The absence of nested loops suggests most operations are at most linear in the "
                "size of their inputs, with no obvious O(n²) patterns."
            )
        elif nested_ratio <= 0.25:
            cx_lines.append(
                "Only a small fraction of functions use nested loops, indicating that potentially "
                "quadratic behavior is limited to a few focused areas."
            )
        else:
            cx_lines.append(
                "A substantial fraction of functions use nested loops, which may indicate "
                "performance hot spots or opportunities to reduce quadratic behavior."
            )

        algo_bits = []
        if cx.get("uses_sorted", False):
            algo_bits.append("sorted()")
        if cx.get("uses_heapq", False):
            algo_bits.append("heapq")
        if cx.get("uses_bisect", False):
            algo_bits.append("bisect")

        if algo_bits:
            cx_lines.append(
                "The use of " + ", ".join(algo_bits) +
                " suggests some awareness of algorithmic tools for more efficient querying or "
                "ordering (e.g., O(n log n) sorting or priority queues)."
            )
        else:
            cx_lines.append(
                "No use of sorted(), heapq, or bisect was detected, so the code does not rely on "
                "more advanced algorithmic utilities in this artifact."
            )

    cx_narrative = " ".join(cx_lines)

    return {
        "oop": oop_narrative,
        "data_structures": ds_narrative,
        "complexity": cx_narrative,
    }
    
def analyze_python_project_oop(root: str | Path) -> Dict[str, Any]:
    """
    function added to simplify integration with other modules.
    """
    analyzer = PythonOOPAstAnalyzer(Path(root))
    return analyzer.analyze()

def pretty_print_oop_report(metrics: dict):
    print("\n" + "="*60)
    print("         PYTHON OOP ANALYSIS REPORT")
    print("="*60)

    print(f"\n Files analyzed: {metrics['files_analyzed']}")
    print("\n Class Statistics")
    print("-"*60)
    print(f"• Total classes             : {metrics['classes']['count']}")
    print(f"• Avg methods per class     : {metrics['classes']['avg_methods_per_class']}")
    print(f"• Classes using inheritance : {metrics['classes']['with_inheritance']}")
    print(f"• Classes with __init__     : {metrics['classes']['with_init']}")

    print("\n Encapsulation")
    print("-"*60)
    print(f"• Classes with private attrs: {metrics['encapsulation']['classes_with_private_attrs']}")

    print("\n Polymorphism")
    print("-"*60)
    print(f"• Classes overriding methods: {metrics['polymorphism']['classes_overriding_base_methods']}")
    print(f"• Total overridden methods  : {metrics['polymorphism']['override_method_count']}")

    print("\n Special Methods")
    print("-"*60)
    print(f"• Classes w/ multiple dunders: {metrics['special_methods']['classes_with_multiple_dunders']}")
    
    ds = metrics.get("data_structures", {})
    print("\n Data Structures")
    print("-"*60)
    print(f"• List literals             : {ds.get('list_literals', 0)}")
    print(f"• Dict literals             : {ds.get('dict_literals', 0)}")
    print(f"• Set literals              : {ds.get('set_literals', 0)}")
    print(f"• Tuple literals            : {ds.get('tuple_literals', 0)}")
    print(f"• List comprehensions       : {ds.get('list_comprehensions', 0)}")
    print(f"• Dict comprehensions       : {ds.get('dict_comprehensions', 0)}")
    print(f"• Set comprehensions        : {ds.get('set_comprehensions', 0)}")
    print(f"• Uses collections.defaultdict: {ds.get('uses_defaultdict', False)}")
    print(f"• Uses collections.Counter    : {ds.get('uses_counter', False)}")
    
    cx = metrics.get("complexity", {})
    print("\n  Complexity & Algorithms")
    print("-"*60)
    print(f"• Total functions           : {cx.get('total_functions', 0)}")
    print(f"• Funcs with nested loops   : {cx.get('functions_with_nested_loops', 0)}")
    print(f"• Nested loop ratio         : {cx.get('nested_loop_ratio', 0.0)}")
    print(f"• Max loop depth            : {cx.get('max_loop_depth', 0)}")
    print(f"• Uses sorted()             : {cx.get('uses_sorted', False)}")
    print(f"• Uses heapq                : {cx.get('uses_heapq', False)}")
    print(f"• Uses bisect               : {cx.get('uses_bisect', False)}")

    print("\n OOP Score")
    print("-"*60)
    print(f"• Score   : {metrics['score']['oop_score']}")
    print(f"• Rating  : {metrics['score']['rating'].upper()}")
    print(f"• Comment : {metrics['score']['comment']}")

    if metrics["syntax_errors"]:
        print("\n Syntax Errors")
        print("-"*60)
        for err in metrics["syntax_errors"]:
            print(f"• {err}")
    else:
        print("\n No syntax errors found")

    narrative = metrics.get("narrative", {})
    print("\n Narrative Insights")
    print("-"*60)
    if "oop" in narrative:
        print("\n[OOP]")
        print(narrative["oop"])
    if "data_structures" in narrative:
        print("\n[Data Structures]")
        print(narrative["data_structures"])
    if "complexity" in narrative:
        print("\n[Complexity & Algorithms]")
        print(narrative["complexity"])

    print("\n" + "="*60 + "\n")
