from pathlib import Path
import sys
from typing import Dict, Any, List, Generator, Type
from tree_sitter import Language, Parser
import tree_sitter_c_sharp as tscs # type: ignore
from .base_c_analyzer_utils import cutilities

class csharpanalysis:

    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(tscs.language())
    
    def analyze_file(self, source: str, path: Path) -> Dict[str, Any]:
        report = self.empty_report(path)

        try:
            tree = self.parser.parse(bytes(source,"utf8"))
            root = tree.root_node
            report["syntax_ok"] = True
        except Exception:
            report["syntax_ok"] = False
            return report
        
        report["imports"] = self.extract_usings(root, source)
        report["classes"] = self.extract_classes(root, source, path)
        report["data_structures"] = self.extract_data_structures(root, source)
        report["complexity"] = self.extract_complexity(root)
        
        return report
    
    def empty_report(self, path: Path) -> Dict[str, Any]:
            return {
        "file": str(path),
        "module": "",
        "classes": [],
        "imports": [],
        "data_structures": {},
        "complexity": {},
        "syntax_ok": False,
        }

    
    def extract_usings(self, root, source: str) -> List[str]:
        imports = []
        for node in cutilities.tree_walk(root):
            if node.type == "using_directive":
                imports.append(source[node.start_byte:node.end_byte].strip())
        return imports
    
    def extract_classes(self, root, source: str, path: Path) -> List[Dict[str, Any]]:
        classes = []
        for node in cutilities.tree_walk(root):
            if node.type in ("class_declaration", "struct_declaration"):
                classes.append(self.parse_class(node, source, path))
        return classes
    
    def get_identifier(self, node, source: str) -> str:
        for child in cutilities.tree_walk(node):
            if child.type == "identifier":
                return source[child.start_byte:child.end_byte]
        return ""

    def get_access(self, node) -> str:
        for child in node.children:
            if child.type == "modifier":
                for mod in child.children:
                    mod_text = mod.text.decode()
                    if mod_text in ("private", "protected", "internal", "protected internal", "private protected"):
                        return "private"
                    elif mod_text == "public":
                        return "public"
        if node.type == "field_declaration":
            return "private"
        return "public"
    
    def get_field_name(self, node, source: str) -> str:
        """Get field name from field_declaration node"""
        for child in node.children:
            if child.type == "variable_declaration":
                for subchild in child.children:
                    if subchild.type == "variable_declarator":
                        for identifier in subchild.children:
                            if identifier.type == "identifier":
                                return source[identifier.start_byte:identifier.end_byte]
        return ""
    
    def parse_class(self, node, source: str, path: Path) -> Dict[str, Any]:
        name = "<anonymous>"
        bases = []
        methods = []
        special_methods = []
        private_attrs = []
        public_attrs = []
        has_constructor = False

        # class name
        for child in node.children:
            if child.type == "identifier":
                name = source[child.start_byte:child.end_byte]
                break

        # inheritance / interfaces
        for child in node.children:
            if child.type == "base_list":
                for base in cutilities.tree_walk(child):
                    if base.type == "identifier":
                        bases.append(source[base.start_byte:base.end_byte])

        # body
        for child in node.children:
            if child.type == "declaration_list":
                for member in child.children:
                    # fields
                    if member.type == "field_declaration":
                        access = self.get_access(member)
                        fname = self.get_field_name(member, source)
                        if fname:
                            if access == "private":
                                private_attrs.append(fname)
                            else:
                                public_attrs.append(fname)
                    # methods
                    elif member.type == "method_declaration":
                        mname = self.get_identifier(member, source)
                        if mname:
                            methods.append(mname)
                            if cutilities.is_special(mname):
                                special_methods.append(mname)

                    # constructor
                    elif member.type == "constructor_declaration":
                        has_constructor = True
                        methods.append(name)
                        special_methods.append(name)

                    # destructor
                    elif member.type in ("destructor_declaration", "finalizer_declaration"):
                        dname = f"~{name}"
                        methods.append(dname)
                        special_methods.append(dname)

                    # operator overloads
                    elif member.type == "operator_declaration":
                        op = source[member.start_byte:member.end_byte]
                        methods.append("operator")
                        special_methods.append(op)

        return {
            "name": name,
            "module": "",
            "file_path": str(path),
            "bases": bases,
            "methods": methods,
            "private_attrs": private_attrs,
            "public_attrs": public_attrs,
            "special_methods": special_methods,
            "has_constructor": has_constructor,
            "virtual_methods": [],
            "override_methods": [],
        }
    
    def extract_complexity(self, root) -> Dict[str, int]:
        total_functions = 0
        nested_loops = 0
        max_depth = 0

        for node in cutilities.tree_walk(root):
            if node.type in ("method_declaration", "constructor_declaration"):
                total_functions += 1
                depth = cutilities.calculate_loop_depth(node)
                max_depth = max(max_depth, depth)
                if depth >= 2:
                    nested_loops += 1

        return {
            "total_functions": total_functions,
            "functions_with_nested_loops": nested_loops,
            "max_loop_depth": max_depth,
        }
    
    def extract_data_structures(self, root, source: str) -> Dict[str, int]:
        ds = {
            "arrays": 0,
            "lists": 0,
            "dictionaries": 0,
            "queues": 0,
            "stacks": 0,
            "hash_sets": 0,
            "dynamic_memory": 0,
        }

        for node in cutilities.tree_walk(root):
            # Fields and properties
            if node.type in ("field_declaration", "property_declaration"):
                text = source[node.start_byte:node.end_byte]

                if "[]" in text or "Array" in text:
                    ds["arrays"] += 1
                if "List<" in text:
                    ds["lists"] += 1
                if "Dictionary<" in text:
                    ds["dictionaries"] += 1
                if "Queue<" in text:
                    ds["queues"] += 1
                if "Stack<" in text:
                    ds["stacks"] += 1
                if "HashSet<" in text:
                    ds["hash_sets"] += 1

            # Dynamic memory allocations (new keyword)
            if node.type == "object_creation_expression":
                ds["dynamic_memory"] += 1

        return ds