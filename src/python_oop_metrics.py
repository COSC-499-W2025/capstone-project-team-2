import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Any
import os

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

class _ClassVisitor(ast.NodeVisitor):
    
    """
    AST visitor that extracts OOP relevant info from a single module.
    """

    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.classes: List[ClassInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        bases: List[str] = []

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
                self._collect_attr_assignments(info, stmt)

        self.classes.append(info)
        # Continue visiting nested classes
        self.generic_visit(node)

    def _collect_attr_assignments(self, info: ClassInfo, func: ast.FunctionDef) -> None:
        
        """
        Look for `self.x = value` inside a method to approximate encapsulation and attribute design.
        """
        for node in ast.walk(func):
            # `self.foo = ...`
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    self._record_attr_target(info, target)
            elif isinstance(node, ast.AnnAssign):
                # `self.foo: int = 3`
                self._record_attr_target(info, node.target)

    def _record_attr_target(self, info: ClassInfo, target: ast.AST) -> None:
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            if target.value.id == "self":  # self.<attr>
                attr_name = target.attr
                if attr_name.startswith("_") and not attr_name.startswith("__"):
                    info.private_attrs.add(attr_name)
                else:
                    info.public_attrs.add(attr_name)

class PythonOOPAstAnalyzer:
    
    """
    Analyze Python OOP usage in a project directory using the built-in AST.
    Primary metrics:
      - Number of classes
      - Average methods per class
      - How many classes use inheritance
      - Encapsulation indicators (private attributes)
      - Polymorphism indicators (overrides of base methods)
      - Richness of special/dunder methods

    Produces a normalized OOP score in [0, 1] + short textual summary.
    """
    
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.python_files: List[Path] = []
        self.class_infos: List[ClassInfo] = []
        self.syntax_errors: List[Path] = []

    def _discover_python_files(self) -> None:
        """
        Collect all .py files under root, skipping some common noisy dirs.
        """
        ignore_dirs = {".git", "__pycache__", ".venv", "venv", "env"}

        for path in self.root.rglob("*.py"):
            if any(part in ignore_dirs for part in path.parts):
                continue
            self.python_files.append(path)
            
    def _analyze_file(self, path: Path) -> None:
        try:
            src = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError:
            self.syntax_errors.append(path)
            return

        # Derive module name from file path
        try:
            rel = path.relative_to(self.root)
            module_name = ".".join(rel.with_suffix("").parts)
        except ValueError:
            module_name = path.stem

        visitor = _ClassVisitor(path, module_name)
        visitor.visit(tree)
        self.class_infos.extend(visitor.classes)

    def _compute_metrics(self) -> Dict[str, Any]:
        n_files = len(self.python_files)
        n_classes = len(self.class_infos)

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

        # --- Basic class/method stats ---
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
                "There are some classes, but inheritance, encapsulation, and "
                "polymorphism are either absent or lightly used."
            )
        elif oop_score < 0.6:
            rating = "medium"
            comment = (
                "The project demonstrates moderate OOP usage. Classes and methods "
                "are present, with some inheritance or encapsulation, but there is "
                "still room to deepen abstraction and polymorphism."
            )
        else:
            rating = "high"
            comment = (
                "The project exhibits strong object-oriented design: classes are "
                "well-used, inheritance and method overriding appear, and there are "
                "signs of encapsulation and expressive interfaces."
            )

        return {
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
            "score": {
                "oop_score": round(oop_score, 2),  # 0–1
                "rating": rating,
                "comment": comment,
            },
            "syntax_errors": [str(p) for p in self.syntax_errors],
        }

    def analyze(self) -> Dict[str, Any]:
        """
        Run the analysis pipeline and return the metrics dictionary.
        """
        self._discover_python_files()
        for f in self.python_files:
            self._analyze_file(f)
        return self._compute_metrics()

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

    print(f"\n📄 Files analyzed: {metrics['files_analyzed']}")
    print("\n📦 Class Statistics")
    print("-"*60)
    print(f"• Total classes             : {metrics['classes']['count']}")
    print(f"• Avg methods per class     : {metrics['classes']['avg_methods_per_class']}")
    print(f"• Classes using inheritance : {metrics['classes']['with_inheritance']}")
    print(f"• Classes with __init__     : {metrics['classes']['with_init']}")

    print("\n🔐 Encapsulation")
    print("-"*60)
    print(f"• Classes with private attrs: {metrics['encapsulation']['classes_with_private_attrs']}")

    print("\n♻️ Polymorphism")
    print("-"*60)
    print(f"• Classes overriding methods: {metrics['polymorphism']['classes_overriding_base_methods']}")
    print(f"• Total overridden methods  : {metrics['polymorphism']['override_method_count']}")

    print("\n✨ Special Methods")
    print("-"*60)
    print(f"• Classes w/ multiple dunders: {metrics['special_methods']['classes_with_multiple_dunders']}")

    print("\n📊 OOP Score")
    print("-"*60)
    print(f"• Score   : {metrics['score']['oop_score']}")
    print(f"• Rating  : {metrics['score']['rating'].upper()}")
    print(f"• Comment : {metrics['score']['comment']}")

    if metrics["syntax_errors"]:
        print("\n⚠️ Syntax Errors")
        print("-"*60)
        for err in metrics["syntax_errors"]:
            print(f"• {err}")
    else:
        print("\n✅ No syntax errors found")

    print("="*60 + "\n")

