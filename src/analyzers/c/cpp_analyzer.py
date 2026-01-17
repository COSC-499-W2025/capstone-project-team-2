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
         special_methods = []
         has_constructor = False
         virtual_methods = []
         override_methods = []

         is_class = node.type == "class_specifier"
         current_access = "private" if is_class else "public"

         return {
            "name": name,
            "modules": "",
            "file_path": str(path),
            "bases": bases,
            "methods": [],
            "private_attrs": [],
            "special_methods": [],
            "has_constructor" : False,
            "virtual_methods": [],
            "override_methods": [],
         }