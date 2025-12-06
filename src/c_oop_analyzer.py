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
import re

    # Common OOP naming patterns in C
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
    includes = []
    include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
    for match in re.finditer(include_pattern, source):
        includes.append(match.group(1))

    struct_info = []
    struct_pattern = r'(?:typedef\s+)?struct\s+(\w+)?\s*\{([^}]+)\}'


    # Track all function definitions for complexity
    total_functions = 0
    functions_with_nested_loops = 0
    max_loop_depth_overall = 0
    static_function_count = 0

    # Track constructors/destructors for lifecycle management
    constructor_funcs = set()
    destructor_funcs = set()

    for match in re.finditer(struct_pattern, source, re.DOTALL):
        struct_name = match.group(1) or "anonymous"
        struct_body = match.group(2)

        # Count function pointers
        func_ptr_pattern = r'\(\s*\*\s*(\w+)\s*\)'
        func_ptrs = re.findall(func_ptr_pattern, struct_body)
        
        # Check for nested structs 
        nested_struct_pattern = r'struct\s+(\w+)\s+(\w+);'
        nested_structs = re.findall(nested_struct_pattern, struct_body)
        
        # Extract bases 
        bases = []
        first_member_pattern = r'^\s*struct\s+(\w+)\s+\w+;'
        first_member = re.search(first_member_pattern, struct_body.strip())
        if first_member:
            bases.append(first_member.group(1))
        
        # Check if this is a vtable struct
        is_vtable = any(re.match(pat, struct_name, re.IGNORECASE) 
                       for pat in VTABLE_PATTERNS)
        has_multiple_func_ptrs = len(func_ptrs) >= 2
        
        # Determine if has constructor
        has_constructor = False
        for ctor_pat in CONSTRUCTOR_PATTERNS:
            struct_ctor_pattern = ctor_pat.replace('.*', struct_name.lower())
            if re.search(struct_ctor_pattern, source.lower()):
                has_constructor = True
                break
        
        special_methods = []
        special_func_names = ['compare', 'equals', 'hash', 'clone', 'destroy', 'init']
        for fp in func_ptrs:
            if any(special in fp.lower() for special in special_func_names):
                special_methods.append(fp)
        

        struct_info.append({
            "name": struct_name,
            "module": "N/A",  # C doesn't have modules
            "file_path": str(path),
            "bases": bases,
            "methods": func_ptrs,  # function pointers are methods
            "has_constructor": has_constructor,
            "special_methods": special_methods,
            "private_attrs": [],  # C structs don't have private attrs (encapsulation via opaque ptrs)
            "public_attrs": [],   # We don't count individual members here
            "is_vtable": is_vtable and has_multiple_func_ptrs,
        })

    # Find function definitions for complexity analysis
    func_pattern = r'(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)'
    for match in re.finditer(func_pattern, source):
        is_static = match.group(1) is not None
        func_name = match.group(3)
        
        if is_static:
            static_function_count += 1
        
        # Skip common non-function patterns
        if func_name in {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'struct'}:
            continue
        
        total_functions += 1
        
        # Check for constructor/destructor patterns
        is_constructor = any(re.match(pat, func_name) for pat in CONSTRUCTOR_PATTERNS)
        is_destructor = any(re.match(pat, func_name) for pat in DESTRUCTOR_PATTERNS)
        
        if is_constructor:
            constructor_funcs.add(func_name)
        if is_destructor:
            destructor_funcs.add(func_name)
        
        func_start = match.end()
        brace_depth = 0
        func_body_start = -1
        func_body_end = -1
        
        for i in range(func_start, min(func_start + 50, len(source))):
            if source[i] == '{':
                func_body_start = i
                break
        
        if func_body_start > 0:
            brace_depth = 1
            for i in range(func_body_start + 1, len(source)):
                if source[i] == '{':
                    brace_depth += 1
                elif source[i] == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        func_body_end = i
                        break
            
            if func_body_end > func_body_start:
                func_body = source[func_body_start:func_body_end]
                max_loop_depth_overall = max(max_loop_depth_overall, loop_depth)

    
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
            "static_functions": static_function_count,
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

