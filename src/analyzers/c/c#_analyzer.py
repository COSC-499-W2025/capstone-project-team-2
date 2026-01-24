from pathlib import Path
from typing import Dict, Any, List, Generator, Type
from tree_sitter import Language, Parser
import tree_sitter_c_sharp as tscs
import os
import re


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
        
        report["imports"] = self.extract_includes(root, source)
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