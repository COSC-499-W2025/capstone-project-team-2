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
from typing import Dict, Any, List, Generator
from tree_sitter import Language, Parser
import os
import re