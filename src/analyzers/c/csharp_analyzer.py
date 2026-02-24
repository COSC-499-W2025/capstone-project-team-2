from pathlib import Path
import sys
from typing import Dict, Any, List, Generator, Type
from tree_sitter import Language, Parser
import tree_sitter_c_sharp as tscs # type: ignore
from .base_c_analyzer_utils import cutilities

class csharpanalysis:
    """
    Analyze C# source code for object-oriented structure and static metrics.
    Output strictly follows the C analyzer aggregation schema:
        report["classes"][]
        report["imports"]
        report["data_structures"]
        report["complexity"]
    Args:
        None
    Returns:
        Dict[str, Any]: Analysis report containing detected classes,
        inheritance, methods, encapsulation, complexity metrics,
        and C#-specific language features.
    """

    def __init__(self):
        try:
            self.parser = Parser()
            self.parser.language = Language(tscs.language())
        except Exception as e:
            raise RuntimeError(f"C# analyzer initialization failed: {e}") from e
        
    def analyze_file(self, source: str, path: Path) -> Dict[str, Any]:
        """
        Analyze a C# source file and extract structural information.
        
        Args:
            source: C# source code as string
            path: File path for reference
            
        Returns:
            Dict containing classes, imports, data structures, and complexity metrics
        """
        report = self.empty_report(path)

        try:
            tree = self.parser.parse(bytes(source,"utf8"))
            root = tree.root_node
            report["syntax_ok"] = True
        except Exception as e:
            report["syntax_ok"] = False
            report["error"] = f"Parse failed: {e}"
            return report
    
        try:
            report["imports"] = self.extract_usings(root, source)
            report["classes"] = self.extract_classes(root, source, path)
            report["data_structures"] = self.extract_data_structures(root, source)
            report["complexity"] = self.extract_complexity(root)
        except Exception as e:
            report["error"] = f"Extraction failed: {e}"
    
        return report
    
    def empty_report(self, path: Path) -> Dict[str, Any]:
            """
        Create an empty analysis report structure.
        
        Args:
            path: File path for the report
            
        Returns:
            Empty report dictionary with default values
        """
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
        """
        Extract using directives (imports) from C# code.
        
        Args:
            root: Parse tree root node
            source: Source code string
            
        Returns:
            List of using directive strings
        """
        imports = []
        for node in cutilities.tree_walk(root):
            if node.type == "using_directive":
                imports.append(source[node.start_byte:node.end_byte].strip())
        return imports
    
    def extract_classes(self, root, source: str, path: Path) -> List[Dict[str, Any]]:
        """
        Extract all class and struct declarations from the parse tree.
        
        Args:
            root: Parse tree root node
            source: Source code string
            path: File path for reference
            
        Returns:
            List of class information dictionaries
        """
        classes = []
        for node in cutilities.tree_walk(root):
            if node.type in ("class_declaration", "struct_declaration"):
                classes.append(self.parse_class(node, source, path))
        return classes
    
    def get_identifier(self, node, source: str) -> str:
        """
        Extract identifier name from a node (for classes, methods, etc.).
        
        Args:
            node: Tree-sitter node
            source: Source code string
            
        Returns:
            Identifier name as string, or empty string if not found
        """
        for child in cutilities.tree_walk(node):
            if child.type == "identifier":
                return source[child.start_byte:child.end_byte]
        return ""

    def get_access(self, node) -> str:
        """
        Determine access level (public/private) of a class member.
        C# fields are private by default, methods are public by default.
        
        Args:
            node: Tree-sitter node representing a class member
            
        Returns:
            "private" or "public"
        """
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
        """
        Extract field name from field_declaration node.
        C# field declarations have structure: field_declaration -> variable_declaration -> variable_declarator -> identifier
        
        Args:
            node: field_declaration node
            source: Source code string
            
        Returns:
            Field name as string, or empty string if not found
        """
        for child in node.children:
            if child.type == "variable_declaration":
                for subchild in child.children:
                    if subchild.type == "variable_declarator":
                        for identifier in subchild.children:
                            if identifier.type == "identifier":
                                return source[identifier.start_byte:identifier.end_byte]
        return ""
    
    def parse_class(self, node, source: str, path: Path) -> Dict[str, Any]:
        """
        Parse a class or struct declaration and extract all relevant information.
        
        Args:
            node: class_declaration or struct_declaration node
            source: Source code string
            path: File path for reference
            
        Returns:
            Dictionary containing:
                - name: class/struct name
                - bases: list of inherited classes/interfaces
                - methods: list of method names
                - private_attrs: list of private field names
                - public_attrs: list of public field names
                - special_methods: list of constructors, destructors, operators
                - has_constructor: boolean indicating presence of constructor
        """
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
        """
        Calculate cyclomatic complexity metrics.
        
        Args:
            root: Parse tree root node
            
        Returns:
            Dictionary containing:
                - total_functions: count of all methods and constructors
                - functions_with_nested_loops: count of functions with loop depth >= 2
                - max_loop_depth: maximum nesting depth of loops found
        """
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
        """
        Count usage of common C# data structures and collections.
        
        Args:
            root: Parse tree root node
            source: Source code string
            
        Returns:
            Dictionary with counts for:
                - arrays: Array[] or Array types
                - lists: List<T> collections
                - dictionaries: Dictionary<K,V> collections
                - queues: Queue<T> collections
                - stacks: Stack<T> collections
                - hash_sets: HashSet<T> collections
        """
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