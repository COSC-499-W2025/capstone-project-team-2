from pathlib import Path
import re
from src.data_extraction import FileMetadataExtractor

"""
Detect whether a local project folder is 'individual' or 'collaborative'
using file metadata and simple text cues.
"""

def collect_authors(root: Path) -> set[str]:
    
    """Collect unique authors using FileMetadataExtractor."""
    
    extractor = FileMetadataExtractor(root)
    authors = set()
    for path in root.rglob("*"):
        if path.is_file():
            author = extractor.get_author(path)
            if author and author not in ("Unknown", "Author Unknown", ""):
                authors.add(author)
    return authors


def find_contributor_files(root: Path) -> list[Path]:
    
    """Return a list of known contributor/author files found in the project."""
    
    known_files = ("CONTRIBUTORS", "AUTHORS", "README.md")
    result = []
    for f in known_files:
        file_path = root / f
        if file_path.exists() and file_path.is_file():
            result.append(file_path)
    return result



def extract_names_from_text(file_path: Path) -> set[str]:
    
    """Extract simple 'First Last' names from a text file."""
    
    name_pattern = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
    found = set()
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        matches = name_pattern.findall(text)
        found.update(matches)
    except Exception:
        pass
    return found


def detect_collaboration_by_metadata(authors: set[str]) -> bool:
    
    """Return True if multiple unique authors detected."""
    
    return len(authors) > 1


def detect_collaboration_by_text(files: list[Path]) -> bool:
    
    """Return True if multiple unique names found across contributor files."""
    
    all_names = set()
    for file_path in files:
        all_names.update(extract_names_from_text(file_path))
    return len(all_names) > 1


def detect_project_type(project_path: str | Path) -> dict:
    
    """
    Determine whether the project is 'individual' or 'collaborative'.

    Args:
        project_path (str | Path): path to the local project folder

    Returns:
        dict: {"project_type": "individual" | "collaborative" | "unknown"}
    """
    
    root = Path(project_path)
    if not root.exists() or not root.is_dir():
        return {"project_type": "unknown"}

    authors = collect_authors(root)
    contributor_files = find_contributor_files(root)
    
    if detect_collaboration_by_metadata(authors):
        return {"project_type": "collaborative"}

    if detect_collaboration_by_text(contributor_files):
        return {"project_type": "collaborative"}

    return {"project_type": "individual"}
