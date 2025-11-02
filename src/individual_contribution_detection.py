from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple, Iterable
from collections import OrderedDict

# Add parent to path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.data_extraction import FileMetadataExtractor
from src.project_type_detection import (
    detect_project_type,
    find_contributor_files,
    extract_names_from_text,
)

UNATTRIBUTED = "<unattributed>"

def normalize(name: str) -> str:
    
    """Return a lowercase, trimmed version of a name."""
    
    return name.strip().lower()

def tokens(name: str) -> List[str]:
    
    """Split a normalized name into lowercase word tokens."""
    
    return [t for t in normalize(name).split() if t]

def name_matches(a: str, b: str) -> bool:
    
    """
    Return True if two names likely refer to the same person.

    Matching rules:
      - Exact normalized match
      - Same last name and same first name or first initial
      - Any shared word longer than 3 characters
    """
    
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True

    ta, tb = tokens(na), tokens(nb)
    if not ta or not tb:
        return False

    # Match by last name + first name or first initial
    if ta[-1] == tb[-1] and (ta[0] == tb[0] or ta[0][0] == tb[0][0]):
        return True

    # Match by any long token
    return any(len(t) > 3 and t in tb for t in ta)

def contributor_names_from_files(root: Path) -> List[str]:
    
    """
    Extract contributor names from standard project files (CONTRIBUTORS, AUTHORS, README).
    Deduplicate and preserve first-seen capitalization.
    """
    
    seen = OrderedDict()
    for f in find_contributor_files(root):
        for n in extract_names_from_text(f):
            key = normalize(n)
            if key and key not in seen:
                seen[key] = n.strip()
    return list(seen.values())

def files_to_owner_map(root: Path, extractor: FileMetadataExtractor) -> Dict[str, Optional[str]]:
    
    """
    Return a mapping of relative file paths to file owners from metadata.
    Skips .git and known contributor text files.
    """
    
    ignore = {"CONTRIBUTORS", "AUTHORS", "README", "README.MD", "README.TXT"}
    mapping: Dict[str, Optional[str]] = {}
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.name.upper() in ignore:
            continue
        try:
            owner = extractor.get_author(p)
        except Exception:
            owner = None
        rel = str(p.relative_to(root)).replace("\\", "/")
        mapping[rel] = owner if owner and owner not in ("Unknown", "Author Unknown", "") else None
    return mapping

def build_canonical(metadata_owners: Iterable[str], contribs: Iterable[str]) -> Tuple[Dict[str, str], Dict[str, str]]:
    
    """
    Build unified name mappings to link contributor names and file metadata owners.

    Returns:
        (owner_to_canonical, contrib_to_canonical)
        Each maps raw names to a single canonical display name.
    """
    
    owner_to_canonical: Dict[str, str] = {}
    contrib_to_canonical: Dict[str, str] = {}

    owners = [o for o in dict.fromkeys(metadata_owners) if o]
    contribs_list = [c for c in dict.fromkeys(contribs) if c]

    matched_owners = set()
    for c in contribs_list:
        canon = None
        for o in owners:
            if name_matches(c, o):
                canon = c.strip()
                owner_to_canonical[o] = canon
                matched_owners.add(o)
                break
        contrib_to_canonical[c] = canon or c.strip()

    for o in owners:
        if o not in owner_to_canonical:
            owner_to_canonical[o] = o.strip()

    return owner_to_canonical, contrib_to_canonical

def detect_individual_contributions_local(
    project_root: Path,
    *,
    extractor: Optional[FileMetadataExtractor] = None
) -> Dict[str, Dict]:
    
    """
    Detect and summarize individual contributions in a local (non-Git) project.

    Combines:
      - File metadata authorship
      - Contributor names from text files
      - Filename heuristics for unmatched files
    """
    
    extractor = extractor or FileMetadataExtractor(project_root)

    contrib_names = contributor_names_from_files(project_root)
    file_map = files_to_owner_map(project_root, extractor)

    owners = [v for v in set(file_map.values()) if v is not None]
    owner_to_canon, contrib_to_canon = build_canonical(owners, contrib_names)

    # Initialize contributor buckets (always include <unattributed> to avoid KeyError)
    buckets: Dict[str, Dict[str, List[str]]] = {}

    # Create a bucket for every canonical contributor
    for c in set(owner_to_canon.values()) | set(contrib_to_canon.values()):
        buckets[c] = {"files_owned": [], "files_from_metadata": [], "files_from_text": []}

    # Always include <unattributed> bucket (safe even if empty)
    buckets[UNATTRIBUTED] = {"files_owned": [], "files_from_metadata": [], "files_from_text": []}

    # Assign metadata-owned files
    for rel, owner in file_map.items():
        if owner:
            canonical = owner_to_canon.get(owner, owner)
            buckets.setdefault(canonical, {"files_owned": [], "files_from_metadata": [], "files_from_text": []})
            buckets[canonical]["files_owned"].append(rel)
            buckets[canonical]["files_from_metadata"].append(rel)
        else:
            buckets[UNATTRIBUTED]["files_owned"].append(rel)

    # Infer unattributed files by filename tokens
    token_buckets = {canon: set(tokens(canon)) for canon in buckets if canon != UNATTRIBUTED}
    for rel in list(buckets[UNATTRIBUTED]["files_owned"]):
        fname = Path(rel).name.lower()
        for canon, toks in token_buckets.items():
            if any(tok in fname for tok in toks if len(tok) > 2):
                buckets[canon]["files_owned"].append(rel)
                buckets[canon]["files_from_text"].append(rel)
                buckets[UNATTRIBUTED]["files_owned"].remove(rel)
                break

    # Finalize counts and sort lists
    result: Dict[str, Dict] = {}
    for person, stats in buckets.items():
        result[person] = {
            "files_owned": sorted(stats["files_owned"]),
            "file_count": len(stats["files_owned"]),
            "files_from_metadata": sorted(stats["files_from_metadata"]),
            "files_from_text": sorted(stats["files_from_text"]),
        }
    return result

def detect_individual_contributions(project_path: str | Path, *, extractor: Optional[FileMetadataExtractor] = None) -> Dict:
    
    """
    Entry point: detect individual contributions for collaborative projects.

    Raises ValueError if:
      - path is invalid
      - project is not marked as collaborative
    """
    
    root = Path(project_path)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {project_path}")

    pt = detect_project_type(root)
    if pt.get("project_type") != "collaborative":
        raise ValueError("Project is not collaborative")

    contributors = detect_individual_contributions_local(root, extractor=extractor)
    return {"is_collaborative": True, "mode": "local", "contributors": contributors}
