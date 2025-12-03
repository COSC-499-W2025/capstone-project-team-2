# java_javalang_analyzer.py
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple
import javalang

from javalang.tree import (
    ClassDeclaration, MethodDeclaration, ConstructorDeclaration,
    VariableDeclarator, MemberReference, Assignment, This, ClassCreator,
    ForStatement, WhileStatement, DoStatement
)

def iter_nodes(node):
    
    """ Generator to iterate all nodes in the AST starting from 'node' in depth-first manner."""
    
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
    Compute max loop nesting depth under a node (counts nested for/while/do). 
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
    Find attribute names assigned to this, e.g., this.x = ...
    Return set of attribute names.
    """
    attrs = set()
    for n in iter_nodes(method_node):
        if isinstance(n, Assignment):
            lhs = n.expressionl  # left-hand side
            # could be a This.MemberReference or just MemberReference
            try:
                if isinstance(lhs, MemberReference):
                    if lhs.qualifier == 'this' and lhs.member:
                        attrs.add(lhs.member)
                # Also handle explicit This nodes
                if isinstance(lhs, This):
                    pass
            except Exception:
                pass
    return attrs

def detect_class_creations(root) -> List[str]:
    """
    Find 'new TypeName(...)' occurrences and return simple type names.
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
    Parse a Java source string and produce per-file metrics in the canonical shape.
    """
    try:
        tree = javalang.parse.parse(source)
    except javalang.parser.JavaSyntaxError as e:
        return {
            "file": str(path),
            "classes_parsed": 0,
            "class_infos": [],
            "imports": [],
            "data_structures": {},
            "complexity": {},
            "syntax_ok": False,
            "syntax_error": str(e),
        }
    except Exception as e:
        return {
            "file": str(path),
            "classes_parsed": 0,
            "class_infos": [],
            "imports": [],
            "data_structures": {},
            "complexity": {},
            "syntax_ok": False,
            "syntax_error": str(e),
        }

    # imports: list of import.path strings
    imports = [imp.path for imp in tree.imports] if getattr(tree, 'imports', None) else []

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
        has_init = False
        dunder_count = 0
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
                    dunder_count += 1

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
                has_init = True
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
            "module": "", # Java has no module concept like Python; could use package name if desired
            "file_path": str(path),
            "bases": bases,
            "methods": sorted(methods),
            "has_init": has_init,
            "dunder_count": dunder_count,
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
        "classes_parsed": len(class_infos),
        "class_infos": class_infos,
        "imports": imports,
        "data_structures": ds,
        "complexity": complexity,
        "syntax_ok": True,
    }

# convert per_file metrics to your ClassInfo dataclass
def per_file_to_classinfo_list(per_file_metrics: Dict[str, Any], ClassInfoCls):
    """
    ClassInfoCls is your ClassInfo dataclass (imported from your python analyzer module).
    Returns List[ClassInfoCls] instances.
    """
    out = []
    for ci in per_file_metrics.get("class_infos", []):
        out.append(ClassInfoCls(
            name=ci["name"],
            module=ci.get("module", ""),
            file_path=Path(ci["file_path"]),
            bases=ci.get("bases", []),
            methods=set(ci.get("methods", [])),
            has_init=ci.get("has_init", False),
            dunder_methods=ci.get("dunder_count", 0),
            private_attrs=set(ci.get("private_attrs", [])),
            public_attrs=set(ci.get("public_attrs", [])),
        ))
    return out


# Quick CLI test
if __name__ == "__main__":
    import json
    sample = '''
    package com.example;
    import java.util.ArrayList;
    import java.util.HashMap;
    public class Foo extends Base implements IExample {
        private int x;
        public String name;
        public Foo() { this.x = 0; }
        public void doSomething() {
            for (int i=0;i<10;i++){
                for (int j=0;j<5;j++){
                    System.out.println(i+j);
                }
            }
        }
        public String toString() { return name; }
    }
    '''
    res = analyze_source(sample, Path("src/com/example/Foo.java"))
    print(json.dumps(res, indent=2))
