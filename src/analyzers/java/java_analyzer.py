"""
Java OOP Analyzer Module

Analyzes Java source files for object-oriented programming patterns,
data structure usage, and code complexity metrics using the javalang parser.
Produces canonical reports compatible with oop_aggregator.
"""

from pathlib import Path
from typing import Dict, Any, List, Set
import javalang

from javalang.tree import (
    ClassDeclaration, MethodDeclaration, ConstructorDeclaration,
    VariableDeclarator, MemberReference, Assignment, ClassCreator,
    ForStatement, WhileStatement, DoStatement
)

def iter_nodes(node):
    """
    Iterate all nodes in the AST starting from 'node' in depth-first manner.
    
    Args:
        node: The root AST node to start iteration from.
        
    Yields:
        Each node in the AST tree.
    """
    if node is None:
        return
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        # explore children
        for attr_name in getattr(n, '__dict__', {}):
            attr = getattr(n, attr_name)
            if isinstance(attr, list):
                for item in reversed(attr):
                    if hasattr(item, '__dict__'):
                        stack.append(item)
            elif hasattr(attr, '__dict__'):
                stack.append(attr)

# loop node kinds for depth calc
LOOP_NODE_TYPES = (ForStatement, WhileStatement, DoStatement)

def max_loop_depth(node) -> int:
    """
    Compute maximum loop nesting depth under a node.
    Counts nested for/while/do loops to estimate algorithmic complexity.
    
    Args:
        node: AST node to analyze.
        
    Returns:
        Maximum nesting depth of loops (0 if no loops).
    """
    def helper(n, depth=0):
        maxd = depth
        for ch in getattr(n, '__dict__', {}).values():
            if isinstance(ch, list):
                for item in ch:
                    if item is None:
                        continue
                    if isinstance(item, LOOP_NODE_TYPES):
                        maxd = max(maxd, helper(item, depth + 1))
                    else:
                        maxd = max(maxd, helper(item, depth))
            elif hasattr(ch, '__dict__'):
                if isinstance(ch, LOOP_NODE_TYPES):
                    maxd = max(maxd, helper(ch, depth + 1))
                else:
                    maxd = max(maxd, helper(ch, depth))
        return maxd
    return helper(node, 0)

def find_this_assignments(method_node) -> Set[str]:
    """
    Find attribute names assigned via 'this' in a method/constructor.
    
    Args:
        method_node: A method or constructor AST node.
        
    Returns:
        Set of attribute names assigned through 'this'.
    """
    attrs = set()
    for n in iter_nodes(method_node):
        if isinstance(n, Assignment):
            lhs = n.expressionl
            try:
                if isinstance(lhs, MemberReference) and lhs.qualifier == 'this' and lhs.member:
                    attrs.add(lhs.member)
            except Exception:
                pass
    return attrs

def detect_class_creations(root) -> List[str]:
    """
    Find 'new TypeName(...)' occurrences in the AST.
    Used to detect data structure usage like ArrayList, HashMap, etc.
    
    Args:
        root: Root AST node to search.
        
    Returns:
        List of simple type names being instantiated.
    """
    names = []
    for n in iter_nodes(root):
        if isinstance(n, ClassCreator):
            # n.type is a Type object
            try:
                t = n.type.name if hasattr(n.type, 'name') else str(n.type)
                if t:
                    names.append(t)
            except Exception:
                pass
    return names

def analyze_source(source: str, path: Path) -> Dict[str, Any]:
    """
    Parse a Java source string and produce per-file metrics.
    Extracts OOP information including classes, inheritance, methods,
    fields, data structure usage, and code complexity metrics.
    
    Args:
        source: Java source code as a string.
        path: Path to the source file (for reporting).
        
    Returns:
        Dict in canonical format with keys:
        - file: File path string
        - module: Package name
        - classes: List of class info dicts
        - imports: List of import strings
        - data_structures: Dict of DS usage flags
        - complexity: Dict with function/loop metrics
        - syntax_ok: Boolean indicating parse success
    """
    try:
        tree = javalang.parse.parse(source)
    except Exception as e:
        return {
            "file": str(path),
            "module": "",
            "classes": [],
            "imports": [],
            "data_structures": {},
            "complexity": {},
            "syntax_ok": False,
            "syntax_error": str(e),
        }

    # imports: list of import.path strings
    imports = [imp.path for imp in tree.imports] if getattr(tree, 'imports', None) else []

    # Extract package name for module field
    package_name = tree.package.name if getattr(tree, 'package', None) else ""

    class_infos = []
    total_functions = 0
    functions_with_nested_loops = 0
    max_loop_depth_overall = 0

    # Collect class creations to detect usage of e.g. ArrayList via new ArrayList<>()
    created_types = detect_class_creations(tree)

    # Iterate types (top-level classes, interfaces, enums)
    for type_decl in getattr(tree, 'types', []):

        if not isinstance(type_decl, ClassDeclaration):
            continue

        cname = type_decl.name
        # bases: extends and implements
        bases = []
        if type_decl.extends:
            # extends is a Type object; get its name 
            if hasattr(type_decl.extends, 'name'):
                bases.append(type_decl.extends.name)
            else:
                bases.append(str(type_decl.extends))
        if type_decl.implements:
            for impl in type_decl.implements:
                if hasattr(impl, 'name'):
                    bases.append(impl.name)
                else:
                    bases.append(str(impl))

        methods = set()
        has_constructor = False
        special_methods = []  # Java equivalents: toString, equals, hashCode, compareTo
        private_attrs = set()
        public_attrs = set()

        # fields: FieldDeclaration nodes
        for field in getattr(type_decl, 'fields', []) or []:
            # FieldDeclaration: has .declarators (list of VariableDeclarator) and .modifiers set
            mods = getattr(field, 'modifiers', set())
            for decl in getattr(field, 'declarators', []) or []:
                if isinstance(decl, VariableDeclarator):
                    fname = decl.name
                    if 'private' in mods:
                        private_attrs.add(fname)
                    else:
                        public_attrs.add(fname)

        # methods & constructors
        # javalang puts methods + constructors under type_decl.methods (MethodDeclaration)
        for member in getattr(type_decl, 'methods', []) or []:
            if isinstance(member, MethodDeclaration):
                methods.add(member.name)
                # special methods mapping: treat toString/equals/hashCode/compareTo as "dunder-like"
                if member.name in {"toString", "equals", "hashCode", "compareTo"}:
                    special_methods.append(member.name)

                # complexity: treat each method as a function
                total_functions += 1
                depth = max_loop_depth(member)
                max_loop_depth_overall = max(max_loop_depth_overall, depth)
                if depth >= 2:
                    functions_with_nested_loops += 1

                # find `this` assignments within the method
                tas = find_this_assignments(member)
                for a in tas:
                    # best-effort visibility: we don't know modifiers here; assume public unless field exists private
                    if a in private_attrs:
                        pass
                    else:
                        public_attrs.add(a)

        for ctor in getattr(type_decl, 'constructors', []) or []:
            if isinstance(ctor, ConstructorDeclaration):
                # name equals class name usually
                methods.add(ctor.name)
                has_constructor = True
                total_functions += 1
                depth = max_loop_depth(ctor)
                max_loop_depth_overall = max(max_loop_depth_overall, depth)
                if depth >= 2:
                    functions_with_nested_loops += 1

                tas = find_this_assignments(ctor)
                for a in tas:
                    if a in private_attrs:
                        pass
                    else:
                        public_attrs.add(a)

        # remove any private attrs from public set
        public_attrs.difference_update(private_attrs)

        class_infos.append({
            "name": cname,
            "module": package_name,
            "file_path": str(path),
            "bases": bases,
            "methods": sorted(methods),
            "has_constructor": has_constructor,
            "special_methods": special_methods,
            "private_attrs": sorted(private_attrs),
            "public_attrs": sorted(public_attrs),
        })

    # Data structure heuristics: look at imports & created types
    ds = {
        "list_literals": 0,
        "dict_literals": 0,
        "set_literals": 0,
        "tuple_literals": 0,
        "list_comprehensions": 0,
        "dict_comprehensions": 0,
        "set_comprehensions": 0,
        "uses_defaultdict": False,
        "uses_counter": False,
        "uses_heapq": False,
        "uses_bisect": False,
        "uses_sorted": False,
    }

    # If imports or class creations mention common types, flag them
    if any('ArrayList' in imp or 'List' in imp or 'java.util.ArrayList' in imp for imp in imports) or any('ArrayList' == t for t in created_types):
        ds["list_literals"] += 1
    if any('HashMap' in imp or 'Map' in imp or 'java.util.HashMap' in imp for imp in imports) or any('HashMap' == t for t in created_types):
        ds["dict_literals"] += 1
    if any('HashSet' in imp or 'Set' in imp or 'java.util.HashSet' in imp for imp in imports) or any('HashSet' == t for t in created_types):
        ds["set_literals"] += 1
    if any('PriorityQueue' in imp or 'java.util.PriorityQueue' in imp for imp in imports) or any('PriorityQueue' == t for t in created_types):
        ds["uses_heapq"] = True
    # sorted analog: Collections.sort or Stream.sorted() detection via imports / class creations
    if any('Collections' in imp or 'java.util.Collections' in imp for imp in imports):
        ds["uses_sorted"] = True

    complexity = {
        "total_functions": total_functions,
        "functions_with_nested_loops": functions_with_nested_loops,
        "max_loop_depth": max_loop_depth_overall,
    }

    return {
        "file": str(path),
        "module": package_name,
        "classes": class_infos,
        "imports": imports,
        "data_structures": ds,
        "complexity": complexity,
        "syntax_ok": True,
    }

# convert per_file metrics to your ClassInfo dataclass
def per_file_to_classinfo_list(per_file_metrics: Dict[str, Any], ClassInfoCls):
    """
    Convert per-file metrics to a list of ClassInfo dataclass instances.
    
    Args:
        per_file_metrics: Dict returned by analyze_source().
        ClassInfoCls: The ClassInfo dataclass (from python_analyzer).
        
    Returns:
        List of ClassInfo instances for each class in the file.
    """
    out = []
    for ci in per_file_metrics.get("classes", []):
        out.append(ClassInfoCls(
            name=ci["name"],
            module=ci.get("module", ""),
            file_path=Path(ci["file_path"]),
            bases=ci.get("bases", []),
            methods=set(ci.get("methods", [])),
            has_init=ci.get("has_constructor", False),
            dunder_methods=len(ci.get("special_methods", [])),
            private_attrs=set(ci.get("private_attrs", [])),
            public_attrs=set(ci.get("public_attrs", [])),
        ))
    return out

