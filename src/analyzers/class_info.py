from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

@dataclass
class ClassInfo:
    """
    Canonical representation of class-level OOP information
    across all supported languages.
    """
    name: str
    module: str
    file_path: Path
    bases: List[str] = field(default_factory=list)
    methods: Set[str] = field(default_factory=set)
    has_init: bool = False
    dunder_methods: int = 0
    private_attrs: Set[str] = field(default_factory=set)
    public_attrs: Set[str] = field(default_factory=set)
