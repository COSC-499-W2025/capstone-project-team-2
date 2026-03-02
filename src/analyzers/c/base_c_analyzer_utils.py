
from typing import Generator, Callable, Dict, Any, Iterable
import re


class cutilities:
    """
    Utility functions for C-family language analysis (C++, C#).
    Provides tree traversal, complexity calculation, and pattern recognition helpers.
    """
    
    @staticmethod
    def tree_walk(node) -> Generator:
        """
        Recursively traverse a tree-sitter parse tree in depth-first order.
        
        Args:
            node: Tree-sitter node to start traversal from
            
        Yields:
            Each node in the tree, starting with the input node
        """
        yield node
        for child in node.children:
            yield from cutilities.tree_walk(child)

    @staticmethod
    def calculate_loop_depth(node) -> int:
        """
        Calculate maximum loop nesting depth within a function.
        Used for cyclomatic complexity analysis.
        
        Args:
            node: Tree-sitter node representing a function/method
            
        Returns:
            Maximum depth of nested loops (0 if no loops)
        """
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
        """
        Determine if a method name represents a special/magic method.
        Special methods include operators, destructors, and common overridable methods.
        
        Args:
            name: Method name as string
            
        Returns:
            True if the method is considered special, False otherwise
        """
        return(
        name.startswith("operator") or
        name.startswith("~") or
        name in {"toString", "clone", "equals", "begin", "end"}
        )
    
    