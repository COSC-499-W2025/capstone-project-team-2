
from typing import Generator, Callable, Dict, Any, Iterable
import re


class cutilities:
    
    @staticmethod
    def tree_walk(node) -> Generator:
        yield node
        for child in node.children:
            yield from cutilities.tree_walk(child)

    @staticmethod
    def calculate_loop_depth(node) -> int:
        """Calculate maximum loop nesting depth within a function"""
        max_depth = 0
    
        def traverse(x, current_depth):
            nonlocal max_depth
        
            if x.type in ("for_statement", "while_statement", "do_statement"):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
        
            for child in x.children:
                traverse(child, current_depth)
    
        traverse(node, 0)
        return max_depth
    
    @staticmethod
    def is_special(name: str) -> bool:
        return(
        name.startswith("operator") or
        name.startswith("~") or
        name in {"toString", "clone", "equals", "begin", "end"}
        )
    
    