from pathlib import Path
import re

try:
    # GitPython is optional; code must handle environments without it
    from git import Repo, InvalidGitRepositoryError, NoSuchPathError
except ImportError:
    Repo = None
    InvalidGitRepositoryError = Exception
    NoSuchPathError = Exception

# Keep this after the optional git import so src import works regardless of GitPython
from src.data_extraction import FileMetadataExtractor


"""
Detect whether a local or Git-based project is 'individual' or 'collaborative'.

Supports:
- Local non-Git projects using file metadata and text cues
- Git repositories using commit author history
"""


def _collect_git_authors_from_repo(repo) -> set[str]:
    """
    Collect unique author names from a Git repository.

    Returns:
        set[str]: Unique author names found in commit history.
    """
    authors = set()
    try:
        for commit in repo.iter_commits():
            name = getattr(commit.author, "name", None)
            if name and name.strip():
                authors.add(name.strip())
    except Exception:
        # Be tolerant of odd repos; return whatever we’ve gathered
        pass
    return authors


def detect_git_collaboration(path: Path) -> dict:
    """
    Try to interpret the path as a local Git repo and detect collaboration.
    Returns {"project_type": "...", "mode":"git"} or raises InvalidGitRepositoryError
    to indicate the path isn't a git repo (caller will fallback).

    IMPORTANT (Windows):
    We explicitly close the Repo to release file handles so TemporaryDirectory
    can clean up without PermissionError.
    """
    if Repo is None:
        return {"project_type": "unknown", "mode": "git"}

    repo = None
    try:
        repo = Repo(path)  # may raise InvalidGitRepositoryError or NoSuchPathError
        authors = _collect_git_authors_from_repo(repo)
        if not authors:
            return {"project_type": "unknown", "mode": "git"}
        if len(authors) > 1:
            return {"project_type": "collaborative", "mode": "git"}
        return {"project_type": "individual", "mode": "git"}

    except (InvalidGitRepositoryError, NoSuchPathError):
        # Explicitly re-raise so caller can fall back to local checks
        raise
    except Exception:
        # Any other git error -> unknown
        return {"project_type": "unknown", "mode": "git"}
    finally:
        # Crucial for Windows: release open handles to .git/*
        if repo is not None:
            try:
                repo.close()
            except Exception:
                pass
        # Drop reference to encourage collection
        del repo


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
    """
    Extract names from a text file.
    - Handles multi-part names (John Michael Doe)
    - Handles hyphens and apostrophes (Anne-Marie, O'Connor, D'Angelo)
    - Handles CamelCase tokens like McLovin or MacArthur
    - Processes line-by-line to avoid merging unrelated lines
    - Normalizes curly apostrophes to straight ones
    """
    found = set()
    try:
        raw = file_path.read_text(encoding="utf-8", errors="ignore")
        text = raw.replace("\u2019", "'").replace("\u2018", "'")  # normalize curly quotes

        token = (
            r"[A-Z][a-zÀ-ÖØ-öø-ÿ]*"                      # start with capital, allow zero+ lowercase
            r"(?:[A-Z][a-zÀ-ÖØ-öø-ÿ]+)*"                 # allow internal capital-start fragments
            r"(?:['-][A-Z][a-zÀ-ÖØ-öø-ÿ]*)*"             # allow - or ' followed by capital-start fragment
        )

        # name = one or more tokens separated by whitespace on the same line
        name_re = re.compile(rf"\b{token}(?:\s+{token})*\b")

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            matches = name_re.findall(line)
            for m in matches:
                low = m.lower()
                if low in {"contributors", "contributor", "authors", "author"}:
                    continue
                clean = re.sub(r"\s+", " ", m).strip()
                found.add(clean)

    except Exception:
        pass

    return found


def detect_collaboration_by_metadata(authors: set[str]) -> dict:
    """Detect collaboration via file metadata authors."""
    if len(authors) > 1:
        return {"project_type": "collaborative", "mode": "local"}
    elif len(authors) == 1:
        return {"project_type": "individual", "mode": "local"}
    return {"project_type": "unknown", "mode": "local"}


def detect_collaboration_by_text(files: list[Path]) -> dict:
    """Detect collaboration via contributor text files."""
    all_names = set()
    for file_path in files:
        all_names.update(extract_names_from_text(file_path))

    if len(all_names) > 1:
        return {"project_type": "collaborative", "mode": "local"}
    elif len(all_names) == 1:
        return {"project_type": "individual", "mode": "local"}
    return {"project_type": "unknown", "mode": "local"}


def detect_project_type(project_path: str | Path) -> dict:
    """
    If the folder is a git repo, use commit history.
    Otherwise, fall back to local checks.

    Returns:
        {"project_type": "individual" | "collaborative" | "unknown", "mode": "git" | "local"}
    """
    root = Path(project_path)

    if Repo is not None:
        try:
            # Attempt to detect using git
            return detect_git_collaboration(root)
        except (InvalidGitRepositoryError, NoSuchPathError):
            # Not a git repo — fall back to local detection
            pass

    if not root.exists() or not root.is_dir():
        return {"project_type": "unknown", "mode": "local"}

    authors = collect_authors(root)
    contributor_files = find_contributor_files(root)

    text_result = detect_collaboration_by_text(contributor_files)
    metadata_result = detect_collaboration_by_metadata(authors)

    # Priority 1: Collaborative if ANY signal says collaborative
    if text_result["project_type"] == "collaborative" or metadata_result["project_type"] == "collaborative":
        return {"project_type": "collaborative", "mode": "local"}

    # Priority 2: Individual if no collaborative signals, but at least one individual signal
    if text_result["project_type"] == "individual" or metadata_result["project_type"] == "individual":
        return {"project_type": "individual", "mode": "local"}

    # Priority 3: Unknown otherwise
    return {"project_type": "unknown", "mode": "local"}
