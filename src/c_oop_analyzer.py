"""
C OOP Analyzer

Analyzes C source files for oop patterns.
Produces reports compatible with oop_aggregator.

Detects:
- Structs with function pointers (methods)
- Constructor/destructor patterns
- Encapsulation (opaque pointers, static functions)
- Inheritance (struct composition)
- Polymorphism (vtables, function pointers)
"""

from pathlib import Path
from typing import Dict, Any, List, Set
# from pycparser import c_parser, c_ast found this late in the run, will refactor into later
import re

# Common naming patterns for constructor/destructor like methods
CONSTRUCTOR_PATTERNS = [
    r'.*_create$', r'.*_new$', r'.*_init$', r'.*_alloc$',
    r'create_.*', r'new_.*', r'init_.*', r'alloc_.*'
]

DESTRUCTOR_PATTERNS = [
    r'.*_destroy$', r'.*_free$', r'.*_delete$', r'.*_cleanup$',
    r'destroy_.*', r'free_.*', r'delete_.*', r'cleanup_.*'
]

# Vtable naming patterns
VTABLE_PATTERNS = [
    r'.*_ops$', r'.*_operations$', r'.*_vtable$', r'.*_vtbl$',
    r'.*_methods$', r'.*_funcs$', r'.*_interface$'
]

def analyze_source(source: str, path: Path) -> Dict[str, Any]:
    source_l = source.lower()

    includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', source)
    struct_pattern = r'(?:typedef\s+)?struct\s+(\w+)?\s*\{([^}]+)\}\s*(\w+)?'
    struct_info = []

    # Track constructors/destructors for lifecycle management
    constructor_funcs = set()
    destructor_funcs = set()

    # Track all function definitions for complexity
    total_functions = 0
    functions_with_nested_loops = 0
    max_loop_depth_overall = 0
    #static_function_count = 0

    for match in re.finditer(struct_pattern, source, re.DOTALL):
        name1, body, name2 = match.group(1), match.group(2), match.group(3)
        struct_name = name1 or name2 or "anonymous"

        # function pointers
        func_ptrs = re.findall(r'\(\s*\*\s*(\w+)\s*\)', body)

        # nested structs
        nested_structs = re.findall(r'struct\s+(\w+)\s+(\w+);', body)
        
        # Extract bases 
        bases = []
        first_member = re.search(r'^\s*struct\s+(\w+)\s+\w+;', body.strip())
        if first_member:
            bases.append(first_member.group(1))
        
        # Check if this is a vtable struct
        is_vtable = any(re.match(pat, struct_name, re.IGNORECASE) 
                       for pat in VTABLE_PATTERNS)
        has_multiple_func_ptrs = len(func_ptrs) >= 2
        
        # Determine if has constructor
        has_constructor = False
        struct_l = struct_name.lower()
        for pat in CONSTRUCTOR_PATTERNS:
            pat_fixed = re.sub(r'\.\*', struct_l, pat.lower())
            if re.search(pat_fixed, source_l):
                has_constructor = True
                break
        
        special_methods = []
        special_func_names = ['compare', 'equals', 'hash', 'clone', 'destroy', 'init']
        for name in func_ptrs:
            if any(special in name.lower() for special in special_func_names):
                special_methods.append(name)
        

        struct_info.append({
            "name": struct_name,
            "module": "N/A",  # C doesn't have modules
            "file_path": str(path),
            "bases": bases,
            "methods": func_ptrs,  # function pointers are methods
            "has_constructor": has_constructor,
            "special_methods": special_methods,
            "private_attrs": [],  # C structs don't have private attrs
            "public_attrs": [],
            "is_vtable": is_vtable and has_multiple_func_ptrs,
            "nested_structs": nested_structs,
        })

    # Find function definitions for complexity analysis
    #static_function_count = 0
    func_pattern = r'^\s*(?P<static>static\s+)?(?P<ret_type>[\w\*\s]+?)\s+(?P<name>\w+)\s*\([^;]*\)\s*\{'
    for match in re.finditer(func_pattern, source, re.MULTILINE):
        #is_static = bool(match.group(1))
        func_name = match.group(3)

        
    #    if is_static:
    #        print("Static function detected:", func_name)
     #       static_function_count += 1
        
        # Skip common non-function patterns
        if func_name in {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'struct'}:
            continue
        
        
        # Check for constructor/destructor patterns
        if any(re.match(p, func_name.lower()) for p in CONSTRUCTOR_PATTERNS):
            constructor_funcs.add(func_name)

        if any(re.match(p, func_name.lower()) for p in DESTRUCTOR_PATTERNS):
            destructor_funcs.add(func_name)

        total_functions += 1
        
        func_start = match.end()
        brace_depth = 1
        end = func_start
        
        for i in range(func_start, len(source)):
            if source[i] == '{':
                brace_depth += 1
            elif source[i] == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    end = i
                    break

        func_body = source[func_start:end]
        loop_depth = calc_loop_depth(func_body)

        max_loop_depth_overall = max(max_loop_depth_overall, loop_depth)
        if loop_depth >= 2:
            functions_with_nested_loops += 1
    
        # Data structure detection from includes and code
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
    
        # Detect common C data structure usage
        if re.search(r'\w+\s*\[\s*\d*\s*\]', source) or 'malloc' in source:
            ds["list_literals"] += 1
    
        # Hash tables / maps (via includes or implementations)
        if any('hash' in inc.lower() or 'map' in inc.lower() for inc in includes):
            ds["dict_literals"] += 1
    
        # Sets (via includes)
        if any('set' in inc.lower() for inc in includes):
            ds["set_literals"] += 1
    
        # Priority queue / heap
        if any('heap' in inc.lower() or 'queue' in inc.lower() for inc in includes):
            ds["uses_heapq"] = True
    
        # Sorting
        if 'qsort' in source or 'sort' in source.lower():
            ds["uses_sorted"] = True
    
        # Binary search
        if 'bsearch' in source:
            ds["uses_bisect"] = True
    
        complexity = {
            "total_functions": total_functions,
            "functions_with_nested_loops": functions_with_nested_loops,
            "max_loop_depth": max_loop_depth_overall,
        }
    
        # Additional C-specific data 
        c_spec = {
            #"static_functions": static_function_count,
            "opaque_pointers": num_opaque_pointers(source),
            "vtable_structs": sum(1 for s in struct_info if s.get("is_vtable", False)),
            "constructor_functions": len(constructor_funcs),
            "destructor_functions": len(destructor_funcs),
        }
    
    return {
        "file": str(path),
        "module": "N/A",  # C doesn't have module system
        "classes": struct_info,
        "imports": includes,
        "data_structures": ds,
        "complexity": complexity,
        "syntax_ok": True,
        "c_spec": c_spec,  # Extra data for C-specific reports
    }

def calc_loop_depth(code: str) -> int:
    """
    Calculate maximum nesting depth of loops in code snippet.
    
    Args:
        code: C code string to analyze.
        
    Returns:
        Maximum loop nesting depth.
    """
    max_depth = 0
    current_depth = 0
    
    # Find all loop keywords
    loop_keywords = ['for', 'while', 'do']
    
    # Track brace depth to understand nesting
    for line in code.split('\n'):
        line = line.strip()

        for keywords in loop_keywords:
            if keywords == 'do' and line.startswith('do'):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                break
            elif keywords in ('for', 'while') and re.match(rf'\b{keywords}\s*\(', line):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
                break
    
        current_depth = max(0,current_depth - line.count('}'))
    return max_depth
                
def num_opaque_pointers(source: str) -> int:
    """
    Count opaque pointer typedefs (a key encapsulation pattern in C).
    Pattern: typedef struct foo *foo_t;
    
    Args:
        source: C source code string.
        
    Returns:
        Count of opaque pointer typedefs.
    """
    opaque_pattern = r'typedef\s+struct\s+\w+\s*\*\s*\w+;'
    return len(re.findall(opaque_pattern, source))

def analyze_c_project(root: Path, extensions: List[str] = None) -> List[Dict[str, Any]]:
    """
    Analyze all C files in a project directory and return canonical reports.
    
    Args:
        root: Root directory path.
        extensions: List of file extensions to analyze (default: ['.c', '.h']).
        
    Returns:
        List of canonical per-file reports suitable for oop_aggregator.
    """
    if extensions is None:
        extensions = ['.c', '.h']
    
    root = Path(root).resolve()
    ignore_dirs = {".git", "__pycache__", ".venv", "venv", "env", "build", "dist", "obj"}
    
    canonical_reports = []
    
    for ext in extensions:
        for path in root.rglob(f"*{ext}"):
            # ignored directories
            if any(part in ignore_dirs for part in path.parts):
                continue
            
            try:
                source = path.read_text(encoding="utf-8", errors='ignore')
                report = analyze_source(source, path)
                canonical_reports.append(report)
            except Exception as e:
                # Return error report
                canonical_reports.append({
                    "file": str(path),
                    "module": "",
                    "classes": [],
                    "imports": [],
                    "data_structures": {},
                    "complexity": {},
                    "syntax_ok": False,
                    "syntax_error": str(e),
                })
    
    return canonical_reports
