"""
JavaScript OOP Analyzer Module 

Analyzes JavaScript source files for object-oriented programming usage,
data structure usage, and time complexity metrics using an AST-based approach
powered by Esprima.
"""

from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict
import esprima
from src.analyzers.class_info import ClassInfo
from src.aggregation.oop_aggregator import aggregate_canonical_reports
from src.aggregation.oop_aggregator import build_narrative

class JavaScriptOOPAnalyzer:
    """
    AST-based JavaScript OOP analyzer using Esprima.

    This analyzer performs static analysis on JavaScript projects to detect:
    - Class definitions and inheritance
    - Constructor usage
    - Method counts
    - Encapsulation via public and private fields
    - Data structure usage (arrays, objects)
    - Time-complexity indicators such as nested loops

    """

    def __init__(self, root: Path):
        """
        Initialize the JavaScript analyzer.
        Args:
            root (Path): Root directory of the JavaScript project to analyze.

        """
        self.root = root.resolve()
        self.js_files: List[Path] = []
        self.class_infos: List[ClassInfo] = []
        
        
        # Data structure usage counters 
        self.ds_counts = {
            "list_literals": 0,
            "dict_literals": 0,
            "set_literals": 0,
            "tuple_literals": 0,
            "list_comprehensions": 0,
            "dict_comprehensions": 0,
            "set_comprehensions": 0,
        }

        # Complexity metrics
        self.complexity_stats = {
            "total_functions": 0,
            "functions_with_nested_loops": 0,
            "max_loop_depth": 0,
        }

    def discover_js_files(self):
        """
        Discover JavaScript source files under the project root.

        Common directories such as node_modules, build outputs, and VCS metadata are ignored.
        """
        ignore = {"node_modules", ".git", "dist", "build"}
        self.js_files = [
            p for p in self.root.rglob("*.js")
            if not any(part in ignore for part in p.parts)
        ]

    def analyze(self) -> Dict[str, Any]:
        """
        Run JavaScript OOP analysis across the entire project.

        This method orchestrates file discovery, per-file analysis, aggregation of results, and narrative generation.

        Returns:
            Dict[str, Any]: Aggregated OOP, data-structure, and complexity metrics.
        """
        self.discover_js_files()

        for file in self.js_files:
            self._analyze_file(file)

        reports = self._to_canonical_reports()
        metrics = aggregate_canonical_reports(reports, total_files=len(self.js_files))
        
        # Inject JavaScript-specific metrics
        metrics["data_structures"] = self.ds_counts
        metrics["complexity"] = self.complexity_stats
        metrics["narrative"] = build_narrative(metrics)
        return metrics

    def _analyze_file(self, path: Path):
        """
        Analyze a single JavaScript source file.

        Parses the file into an AST, extracts class-based OOP constructs,
        and applies lightweight heuristics to estimate data structure usage.

        Args:
            path (Path): Path to the JavaScript file being analyzed.
        """
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = esprima.parseModule(source, tolerant=True)
        except Exception:
            # Skip files that cannot be parsed
            return

        # Analyze top-level AST nodes
        for node in tree.body:
            if node.type == "ClassDeclaration":
                self._handle_class(node, path)

        # Data-structure heuristics based on token stream
        for node in esprima.tokenize(source):
            if node.type == "Punctuator" and node.value == "[":
                self.ds_counts["list_literals"] += 1
            if node.type == "Punctuator" and node.value == "{":
                self.ds_counts["dict_literals"] += 1
                
        # Count top-level functions (non-class)
        for node in tree.body:
            if node.type in {"FunctionDeclaration"}:
                self.complexity_stats["total_functions"] += 1

    def _handle_class(self, node, path: Path):
        """
        Analyze a JavaScript class declaration node.

        Extracts:
        - Class name
        - Inheritance (extends)
        - Methods and constructors
        - Public and private fields
        - Loop-based complexity metrics

        Args:
            node: Esprima AST node representing a class declaration.
            path (Path): Path to the source file containing the class.
        """
        
        try:
            module = ".".join(path.relative_to(self.root).with_suffix("").parts)
        except ValueError:
            module = path.stem
            
        name = node.id.name if node.id else "<anonymous>"
        bases = []
        methods: Set[str] = set()
        private_attrs: Set[str] = set()
        public_attrs: Set[str] = set()
        has_constructor = False
        
        # Inheritance
        if node.superClass:
            bases.append(node.superClass.name)

        for element in node.body.body:
            if element.type == "MethodDefinition":
                method_name = element.key.name
                methods.add(method_name)
                self.complexity_stats["total_functions"] += 1

                if method_name == "constructor":
                    has_constructor = True

                depth = self._loop_depth(element.value.body)
                self.complexity_stats["max_loop_depth"] = max(
                    self.complexity_stats["max_loop_depth"], depth
                )
                if depth >= 2:
                    self.complexity_stats["functions_with_nested_loops"] += 1

            if element.type == "PropertyDefinition":
                key = element.key.name
                if key.startswith("#"):
                    private_attrs.add(key)
                else:
                    public_attrs.add(key)

        self.class_infos.append(
            ClassInfo(
                name=name,
                module=module,
                file_path=path,
                bases=bases,
                methods=methods,
                has_init=has_constructor,
                dunder_methods=0,
                private_attrs=private_attrs,
                public_attrs=public_attrs,
            )
        )

    def _loop_depth(self, node) -> int:
        """
        Compute maximum loop nesting depth within a method body.

        Args:
            node: AST node representing a method body.

        Returns:
            int: Maximum nesting depth of for/while loops.
        """
        
        max_depth = 0

        def visit(n, depth):
            nonlocal max_depth
            if n is None:
                return
            if isinstance(n, list):
                for x in n:
                    visit(x, depth)
                return

            if getattr(n, "type", None) in { "ForStatement", "WhileStatement", "ForOfStatement", "ForInStatement"}:
                depth += 1
                max_depth = max(max_depth, depth)

            for attr in vars(n).values():
                visit(attr, depth)

        visit(node, 0)
        return max_depth

    def _to_canonical_reports(self):
        """
        Convert collected ClassInfo objects into canonical per-file reports.

        Returns:
            List[Dict[str, Any]]: Canonical reports compatible with the OOP aggregator.
        """
        files = defaultdict(list)
        for ci in self.class_infos:
            files[str(ci.file_path)].append(ci)

        reports = []
        for file, classes in files.items():
            reports.append({
                "file": file,
                "module": classes[0].module if classes else "",
                "classes": [self._class_to_dict(ci) for ci in classes],
                "data_structures": {},
                "complexity": {},
                "syntax_ok": True,
            })
        return reports

    @staticmethod
    def _class_to_dict(ci: ClassInfo):
        """
        Convert a ClassInfo instance into a canonical class dictionary.

        Args:
            ci (ClassInfo): Class metadata object.

        Returns:
            Dict[str, Any]: Canonical representation of a class.
        """
        
        return {
            "name": ci.name,
            "bases": ci.bases,
            "methods": sorted(ci.methods),
            "has_constructor": ci.has_init,
            "special_methods": [],
            "private_attrs": sorted(ci.private_attrs),
            "public_attrs": sorted(ci.public_attrs),
        }
