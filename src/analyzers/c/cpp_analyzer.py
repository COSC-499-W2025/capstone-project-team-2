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
import os
import re
import logging

_CPP_IMPORT_ERROR: Exception | None = None

try:
    from tree_sitter import Language, Parser
    import tree_sitter_cpp as tscpp
    from .base_c_analyzer_utils import cutilities
except Exception as e:
    _CPP_IMPORT_ERROR = e
    # Allow module to import, but analyzer usage will bubble a RuntimeError later.
    Language = None  # type: ignore
    Parser = None    # type: ignore
    tscpp = None     # type: ignore
    cutilities = None  # type: ignore

class cppanalysis:

    """
    Analyze C++ source code for object-oriented structure and static metrics.
    Output strictly follows the C analyzer aggregation schema:
        report["classes"][]
        report["imports"]
        report["data_structures"]
        report["complexity"]
        report["cpp_spec"]
    Args:
        None
    Returns:
        Dict[str, Any]: Analysis report containing detected classes,
        inheritance, methods, encapsulation, complexity metrics,
        and C++-specific language features.
    """


    # initialize Tree_sitter parser with a CPP language
    # bubble initialization files inside init
    def __init__(self):
        if _CPP_IMPORT_ERROR is not None:
            raise RuntimeError(
                f"C++ analyzer unavailable: dependency/import failure: {_CPP_IMPORT_ERROR}"
            ) from _CPP_IMPORT_ERROR

        try:
            self.parser = Parser()
            self.parser.language = Language(tscpp.language())
        except Exception as e:
            raise RuntimeError(f"C++ analyzer initialization failed: {e}") from e

    def analyze_file(self, source:str, path:Path) -> Dict[str, Any]:
        """
        Analyze a single C++ source file and extract structural metrics.
        Output strictly follows the C/C++ analyzer aggregation schema:
            report["classes"][]
            report["imports"]
            report["data_structures"]
            report["complexity"]
            report["cpp_spec"]
        Args:
            source (str): Raw C++ source code as a string.
            path (Path): File path used for reporting context.
        Returns:
            Dict[str, Any]: Parsed analysis report for the given source file.
        """
        report = self.empty_report(path)

        try:
            tree = self.parser.parse(bytes(source, "utf8"))
            root = tree.root_node
            report["syntax_ok"] = True
        except Exception as e:
            report["syntax_ok"] = False
            report["error"] = f"Parse failed: {e}"
            logging.warning("CPP parse failed for %s: %s", path, e, exc_info=True)
            return report

        try:
            report["imports"] = self.extract_includes(root, source)
            report["classes"] = self.extract_classes(root, source, path)
            report["data_structures"] = self.extract_data_structures(root, source)
            report["complexity"] = self.extract_complexity(root)
            report["cpp_spec"] = self.cpp_spec(root, source)
        except Exception as e:
            # keep syntax_ok True because parse succeeded
            report["error"] = f"Extraction failed: {e}"
            logging.warning("CPP extraction failed for %s: %s", path, e, exc_info=True)

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

    def extract_includes(self, root, source: str) -> List[str]:
         includes = []
         for node in cutilities.tree_walk(root):
              if node.type in ("preproc_include"):
                   includes.append(source[node.start_byte:node.end_byte].strip())
         
         return includes
    

    def extract_classes(self, root, source: str, path: Path):
         classes = []
         for node in cutilities.tree_walk(root):
              if node.type in ("class_specifier", "struct_specifier"):
                   classes.append(self.parse_class(node, source, path))
         
         return classes
    
    def parse_class(self, node, source: str, path: Path):
         """
        Parse a single C++ class or struct declaration.
        Output strictly follows the analyzer class schema:
            name, bases, methods, access modifiers,
            constructors, virtual and override methods.
        Args:
            node (Node): Tree-sitter class or struct specifier node.
            source (str): Raw C++ source code.
            path (Path): Source file path.
        Returns:
            Dict[str, Any]: Structured class representation.
        """
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
                bases.extend(self.extract_base_classes(child, source))

         # check body of class
         for child in node.children:
              if child.type == "field_declaration_list":
                current_access = "private" if is_class else "public"

                for body in child.children:
                     if body.type == "access_specifier":
                          access_type = source[body.start_byte:body.end_byte]
                          current_access = access_type.rstrip(':')

                     if body.type == "field_declaration":
                        print(f"Field declaration: {source[body.start_byte:body.end_byte]}")
                        fname = self.extract_fname(body, source)
                        if fname:
                            if current_access == "private":
                                private_attrs.append(fname)
                            else:
                                public_attrs.append(fname)

                        else:
                            # No field name found, might be a method declaration
                            methodinf = self.extract_methodinf(body, source, name)
                            print(f"Method info from field_declaration: {methodinf}")
                            if methodinf:
                                mname = methodinf["name"]
                                methods.append(mname)
                                if methodinf["is_constructor"]:
                                    has_constructor = True
                                if methodinf["is_virtual"]:
                                    virtual_methods.append(mname)
                                if methodinf["is_override"]:
                                    override_methods.append(mname)
                                if cutilities.is_special(mname):
                                    special_methods.append(mname)
                          

                     elif body.type in ("function_definition", "declaration", "field_declarator"):
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
                                
                               if cutilities.is_special(mname):
                                    special_methods.append(mname)
         return {
            "name": name,
            "module": "",
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
         """
        Extract method metadata from a C++ declaration or definition.
        Output strictly follows analyzer method classification rules:
            constructors, destructors, virtual, override, special methods.
        Args:
            method_node (Node): Tree-sitter node representing a method.
            source (str): Raw C++ source code.
            cname (str): Enclosing class name.
        Returns:
            Dict[str, Any] | None: Method metadata or None if not applicable.
        """
         mname = ""
         is_virtual = False
         is_override = False
         is_destructor = False

         mtext = source[method_node.start_byte:method_node.end_byte]
         is_virtual = "virtual" in mtext.split("(")[0]
         is_override = "override" in mtext

         for node in cutilities.tree_walk(method_node):
            if node.type == "function_declarator":
                for child in node.children:
                    if child.type == "operator_name":
                        mname = f"operator{source[child.start_byte:child.end_byte].replace('operator', '').strip()}"
                        break
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

        for node in cutilities.tree_walk(root):
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
                for child in cutilities.tree_walk(node):
                    if child.type == "operator_name":
                        cpp_spec["operator_overloads"] += 1
                        break

            # Abstract classes
            elif node.type in ("class_specifier", "struct_specifier"):
                class_name = self.get_cname(node, source)
                if class_name:
                    class_names.add(class_name)
                    # Check for pure virtual functions (= 0)
                    if self.pure_virtual(node, source):
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
    
    def extract_data_structures(self, root, source: str) -> Dict[str, int]:
        """
        Detect data structure usage within C++ source code.
        Output strictly follows the data structure aggregation schema:
            arrays, hash_tables, linked_lists, trees,
            queues, stacks, dynamic_memory, pointer_arrays.
        Args:
            root (Node): Tree-sitter root node.
            source (str): Raw C++ source code.
        Returns:
            Dict[str, int]: Data structure usage counters.
        """
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
        for node in cutilities.tree_walk(root):
            if node.type == "field_declaration":
                field_text = source[node.start_byte:node.end_byte]
        
                if any(t in field_text for t in ["std::vector", "std::array"]):
                    ds["arrays"] += 1
        
                elif any(t in field_text for t in ["std::map", "std::unordered_map"]):
                    ds["hash_tables"] += 1
        
                elif any(t in field_text for t in ["std::list", "std::forward_list"]):
                    ds["linked_lists"] += 1

            # Count type identifiers for STL containers
            elif node.type == "template_type":
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
    
    def extract_complexity(self, root) -> Dict[str, int]:
        total_functions = 0
        nested_loops = 0
        max_depth = 0

        for node in cutilities.tree_walk(root):
            if node.type == "function_definition":
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
    
    def extract_base_classes(self, base_clause, source: str) -> List[str]:
        """Extract base class names from base_class_clause"""
        bases = []
        for node in cutilities.tree_walk(base_clause):
            if node.type in ("type_identifier", "template_type"):
                base_name = source[node.start_byte:node.end_byte]
                if base_name and base_name not in ("public", "private", "protected"):
                    bases.append(base_name)
        return bases
    
    def extract_fname(self, field_node, source: str) -> str:
        """Extract field name from field_declaration"""
        for child in field_node.children:
            if child.type == "field_identifier":
                return source[child.start_byte:child.end_byte]
        return ""

    @staticmethod
    def analyze_cpp_project(root: Path, extensions=None) -> List[Dict[str, Any]]:
        root = Path(root)

        if not root.exists():
            raise ValueError(f"CPP project root does not exist: {root}")
        if not root.is_dir():
            raise ValueError(f"CPP project root is not a directory: {root}")

        if extensions is None:
            extensions = [".cpp", ".cc", ".cxx", ".hpp", ".h"]

        analyzer = cppanalysis()  # bubbles import/init failures

        reports = []
        for path in root.rglob("*"):
            if path.suffix.lower() in extensions:
                try:
                    source = path.read_text(encoding="utf-8", errors="ignore")
                    reports.append(analyzer.analyze_file(source, path))
                except Exception as e:
                    logging.warning("CPP file read/analyze failed for %s: %s", path, e, exc_info=True)
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
