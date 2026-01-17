"""
CPP Analyzer

Analyzes CPP source files for oop patterns.

Detects:
- Classes / structs
- Inheritance
- Constructors
- Methods (including virtual/override)
- Encapsulation (public/private fields)
- Polymorphism (virtual methods and overrides)
- Basic complexity metrics
"""

from pathlib import Path
from typing import Dict, Any, List, Generator, Type
from tree_sitter import Language, Parser
import tree_sitter_cpp as tscpp
import os
import re

class cppanalysis:


    # initialize Tree_sitter parser with a CPP language
    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(tscpp.language())

    def analyze_file(self, source:str, path:Path) -> Dict[str, Any]:
        report = self.empty_report(path)

        try:
            tree = self.parser.parse(bytes(source,"utf8"))
            root = tree.root_node
            report["syntax_ok"] = True
        except Exception:
            report["syntax_ok"] = False
            return report
        
        report["imports"] = self.extract_includes(root, source)
        report["classes"] = self.extract_classes(root, source, path)
        report["data_structures"] = self.extract_data_structures(root, source)
        report["complex"] = self.extract_complexity(root)
        report["cpp_spec"] = self.extract_cpp_specific(root, source)
        
        return report
    
    def empty_report(self, path: Path) -> Dict[str, Any]:
                return {
            "file": str(path),
            "module": "",
            "classes": [],
            "imports": [],
            "data_structures": {},
            "complexity": {},
            "cpp_spec": {},
            "syntax_ok": False,
        }
    def tree_walk(self, node) -> Generator:
         yield node
         for child in node.children:
              yield from self.tree_walk(child)

    def extract_includes(self, root, source: str) -> List[str]:
         includes = []
         for node in self.tree_walk(root):
              if node.type in ("preproc_include"):
                   includes.append(source[node.start_byte:node.end_byte].strip)
         
         return includes
    

    def extract_classes(self, root, source: str, path: Path):
         classes = []
         for node in self.tree_walk(root):
              if node.type in ("class_specifier", "struct_specifier"):
                   classes.append(self.parse_class(node, source, path))
         
         return classes
    
    def parse_class(self, node, source: str, path: Path):
         name = "<anonymous>"
         bases = []
         methods = []
         private_attrs = []
         public_attrs = []
         special_methods = []
         has_constructor = False
         virtual_methods = []
         override_methods = []

         # check access type
         is_class = node.type == "class_specifier"
         current_access = "private" if is_class else "public"

         # check class name
         for child in node.children:
              if child.type == "type_identifier":
                   name = source[child.start_byte:child.end_byte]
                   break
         # check inheritance 
         for child in node.children:
            if child.type == "base_class_clause":
                bases.extend(self._extract_base_classes(child, source))

         # check body of class
         for child in node.children:
              if child.type == "base_class_clause":
                current_access = "private" if is_class else "public"

                for body in child.children:
                     if body.type == "access_specifier":
                          access_type = source[body.start_byte:body.end_byte]
                          current_access = access_type.rstrip(':')

                     elif body.type == "field_declaration":
                          fname = self.extract_fname(body, source)
                          if fname:
                            if access_type == "private":
                                private_attrs.append(fname)
                            else:
                                public_attrs.append(fname)
                     elif body.type in ("function_deffinition", "declaration"):
                          methodinf = self.extract_methodinf(body, source, name)
                          if methodinf:
                               mname = methodinf["name"]
                               methods.append(mname)

                               if methodinf["is_constructor"]:
                                    has_constructor = True
                                
                               if methodinf["is_virtual"]:
                                    virtual_methods.append(mname)

                               if methodinf["is_override"]:
                                    override_methods.append(mname)
                                
                               if self.is_special(mname):
                                    special_methods(mname)
         return {
            "name": name,
            "modules": "",
            "file_path": str(path),
            "bases": bases,
            "methods": methods,
            "private_attrs": private_attrs,
            "public_attrs": public_attrs,
            "special_methods": special_methods,
            "has_constructor" : has_constructor,
            "virtual_methods": virtual_methods,
            "override_methods": override_methods,
         }
    
    def extract_methodinf(self, method_node, source: str, cname: str):
         mname = ""
         is_virtual = False
         is_override = False
         is_destructor = False

         mtext = source[method_node.start_byte:method_node.end_byte]
         is_virtual = "virtual" in mtext.split("(")[0]
         is_override = "override" in mtext

         for node in self.tree_walk(method_node):
            if node.type == "function_declarator":
                for child in node.children:
                    if child.type in ("identifier", "field_identifier", "destructor_name"):
                        mname = source[child.start_byte:child.end_byte]
                        break
                    elif child.type == "qualified_identifier":
                        # Handle qualified names like ClassName::methodName
                        parts = source[child.start_byte:child.end_byte].split("::")
                        if parts:
                            mname = parts[-1]
                        break
                if mname:
                    break
            elif node.type in ("identifier", "field_identifier") and not mname:
                # Fallback
                pname = source[node.start_byte:node.end_byte]
                if pname and pname not in ("void", "int", "bool", "char", "const", "static"):
                    mname = pname
                    break
        
         if not mname:
            return None
         
         is_constructor = (mname == cname or mname == f"~{cname}")
         if mname.startswith("~"):
              is_destructor = True

         return {
            "name": mname,
            "is_constructor": is_constructor,
            "is_virtual": is_virtual,
            "is_override": is_override,
            "is_destructor": is_destructor,
         }
    
    def is_special(self, name: str) -> bool:
         return(
            name.startswith("operator") or
            name.startswith("~") or
            name in {"toString", "clone", "equals", "begin", "end"}
         )
    
    def cpp_spec(self, root, source: str) -> Dict[str, int]:
        """Extract C++-specific OOP patterns and features"""
        cpp_spec = {
            "template_classes": 0,
            "namespaces": 0,
            "abstract_classes": 0,
            "smart_pointers": 0,
            "raii_classes": 0,
            "operator_overloads": 0,
        }

        # Track classes for abstract detection
        class_names = set()
        pure_virtual_classes = set()

        for node in self._walk_tree(root):
            if node.type == "template_declaration":
                # Check if it contains a class
                for child in node.children:
                    if child.type in ("class_specifier", "struct_specifier"):
                        cpp_spec["template_classes"] += 1
                        break

            elif node.type == "namespace_definition":
                cpp_spec["namespaces"] += 1

            # unique_ptr, shared_ptr, weak_ptr
            elif node.type == "template_type":
                ttext = source[node.start_byte:node.end_byte]
                if any(ptr in ttext for ptr in ["unique_ptr", "shared_ptr", "weak_ptr"]):
                    cpp_spec["smart_pointers"] += 1

            # Operator overload
            elif node.type == "function_definition":
                for child in self._walk_tree(node):
                    if child.type == "operator_name":
                        cpp_spec["operator_overloads"] += 1
                        break

            # Abstract classes
            elif node.type in ("class_specifier", "struct_specifier"):
                class_name = self._get_class_name(node, source)
                if class_name:
                    class_names.add(class_name)
                    # Check for pure virtual functions (= 0)
                    if self._has_pure_virtual(node, source):
                        pure_virtual_classes.add(class_name)

            # pattern detection (destructor + resource management)
            elif node.type == "destructor_name":
                #if class has destructor, likely RAII
                cpp_spec["raii_classes"] += 1

        cpp_spec["abstract_classes"] = len(pure_virtual_classes)

        return cpp_spec

    def get_cname(self, class_node, source: str) -> str:
        """Extract class name from class_specifier node"""
        for child in class_node.children:
            if child.type == "type_identifier":
                return source[child.start_byte:child.end_byte]
        return ""

    def pure_virtual(self, class_node, source: str) -> bool:
        """Check if class has any pure virtual functions (= 0)"""
        ctext = source[class_node.start_byte:class_node.end_byte]
        # Look for "= 0" pattern which indicates pure virtual
        return "= 0" in ctext and "virtual" in ctext
    
    def _extract_data_structures(self, root, source: str) -> Dict[str, int]:
        """Extract data structure usage through type declarations"""
        ds = {
            "arrays": 0,
            "hash_tables": 0,
            "linked_lists": 0,
            "trees": 0,
            "queues": 0,
            "stacks": 0,
            "dynamic_memory": 0,
            "pointer_arrays": 0,
        }

        # Count type identifiers for STL containers
        for node in self._walk_tree(root):
            if node.type == "template_type":
                type_text = source[node.start_byte:node.end_byte]
                
                if any(t in type_text for t in ["std::vector", "std::array"]):
                    ds["arrays"] += 1
                    if "*" in type_text or "ptr" in type_text.lower():
                        ds["pointer_arrays"] += 1
                
                elif any(t in type_text for t in ["std::map", "std::unordered_map", "std::hash_map"]):
                    ds["hash_tables"] += 1
                
                elif any(t in type_text for t in ["std::list", "std::forward_list"]):
                    ds["linked_lists"] += 1
                
                elif any(t in type_text for t in ["std::set", "std::multiset", "std::tree"]):
                    ds["trees"] += 1
                
                elif any(t in type_text for t in ["std::stack"]):
                    ds["stacks"] += 1
                
                elif any(t in type_text for t in ["std::queue", "std::priority_queue", "std::deque"]):
                    ds["queues"] += 1
            
            # Count dynamic memory operations
            elif node.type == "new_expression":
                ds["dynamic_memory"] += 1
            elif node.type == "delete_expression":
                ds["dynamic_memory"] += 1
            elif node.type == "call_expression":
                call_text = source[node.start_byte:node.end_byte]
                if "malloc(" in call_text or "free(" in call_text:
                    ds["dynamic_memory"] += 1

        return ds

    def analyze_cpp_project(root: Path, extensions=None) -> List[Dict[str, Any]]:
        if extensions is None:
            extensions = [".cpp", ".cc", ".cxx", ".hpp", ".h"]

        analyzer = cppanalysis()
        reports = []

        for path in root.rglob("*"):
            if path.suffix.lower() in extensions:
                try:
                    source = path.read_text(encoding="utf-8", errors="ignore")
                    reports.append(analyzer.analyze_source(source, path))
                except Exception as e:
                    reports.append({
                        "file": str(path),
                        "module": "",
                        "classes": [],
                        "imports": [],
                        "data_structures": {},
                        "complexity": {},
                        "cpp_spec": {},
                        "syntax_ok": False,
                        "error": str(e),
                    })

        return reports

