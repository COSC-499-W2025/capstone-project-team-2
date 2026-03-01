from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple, Iterable
from collections import OrderedDict
from git import Repo, InvalidGitRepositoryError

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

    Matching rules (in priority order):
      1. Exact normalized match
      2. Same last name + matching first name or first initial
      3. At least 2 shared words (each > 3 chars)
      4. Single name matches multi-word name (e.g., "Sam" matches "Sam Example")
    
    This avoids false positives like "John Smith" matching "Sarah Smith".
    """
    
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True

    ta, tb = tokens(na), tokens(nb)
    if not ta or not tb:
        return False

    #2: Match by last name + first name or first initial
    # This handles "Sam Example" -> "Sam E Example" or "Sam" with last name match
    if len(ta) > 1 and len(tb) > 1:
        if ta[-1] == tb[-1] and ta[0] and tb[0]:
            if ta[0] == tb[0] or (len(ta[0]) > 0 and len(tb[0]) > 0 and ta[0][0] == tb[0][0]):
                return True

    #3: At least 2 shared words (each > 3 chars)
    # This handles "John William Smith" -> "John Smith" but not "John Smith" -> "Sarah Smith"
    long_tokens_a = [t for t in ta if len(t) > 3]
    long_tokens_b = [t for t in tb if len(t) > 3]
    shared = set(long_tokens_a) & set(long_tokens_b)
    if len(shared) >= 2:
        return True

    #4: Single name matches multi-word name if the single name is contained
    # This handles "Sam" -> "Sam Example" (when last name check didn't apply)
    if len(ta) == 1 and len(tb) > 1:
        # Single token from 'a' must match a token in 'b' (and be > 3 chars to be meaningful)
        return len(ta[0]) >= 3 and ta[0] in tb
    if len(tb) == 1 and len(ta) > 1:
        # Single token from 'b' must match a token in 'a'
        return len(tb[0]) >= 3 and tb[0] in ta

    return False


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
    Return a mapping of POSIX relative file paths to file owners from metadata.
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
        rel = p.relative_to(root).as_posix()
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

    for c in contribs_list:
        canon = None
        for o in owners:
            if name_matches(c, o):
                canon = c.strip()
                owner_to_canonical[o] = canon
                break
        contrib_to_canonical[c] = canon or c.strip()

    for o in owners:
        if o not in owner_to_canonical:
            owner_to_canonical[o] = o.strip()

    return owner_to_canonical, contrib_to_canonical

def detect_individual_contributions_local(
    project_root: Path,
    *,
    extractor: Optional[FileMetadataExtractor] = None,
    include_unattributed: bool = True
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

def canonical_for_git(name: Optional[str], email: Optional[str], contribs: List[str], owner_to_canon: Dict[str, str]) -> str:
    
    """
    Resolve canonical contributor name for a Git author.
    
    Priority order:
    1. Match name against CONTRIBUTORS entries
    2. Match email local part against CONTRIBUTORS entries
    3. Match against metadata owners
    4. Use email local part (keeps different emails separate)
    5. Use name as-is
    6. Return "<unknown>"
    """
    
    #1: Check if name matches any CONTRIBUTORS entry
    if name:
        for c in contribs:
            if name_matches(c, name):
                return c.strip()
    
    #2-3: Check email-based matches
    if email:
        local = email.split("@", 1)[0]
        clean_local = local.split('+')[0]  # Remove decorators like +1, +2
        
        # Check if email local part matches a contributor
        for c in contribs:
            if clean_local.lower() in normalize(c) or local.lower() in normalize(c):
                return c.strip()
        
        # Check against metadata owners
        for owner, canon in owner_to_canon.items():
            if name_matches(canon, name or "") or clean_local.lower() in normalize(owner):
                return canon
        
        #4: No CONTRIBUTORS match - use email to keep them separate
        # Use clean_local (without + decorator) so chris+one and chris+two merge to "Chris"
        return clean_local.replace(".", " ").replace("_", " ").title()
    
    #5: No email - use name as-is
    if name:
        return name.strip()
    
    #6: No name or email
    return "<unknown>"

def detect_individual_contributions_git(project_root: Path, *, repo: Optional[Repo] = None) -> Dict[str, Dict]:
    
    """
    Detect individual contributions using Git history.

    Key behavior:
    - Different emails are treated as separate contributors UNLESS they match a CONTRIBUTORS entry
    - CONTRIBUTORS file provides canonical names that merge multiple identities
    - Untracked files are placed in <unattributed>
    """
    
    try:
        repo = repo or Repo(project_root)
    except (InvalidGitRepositoryError, Exception):
        raise ValueError("Path is not a git repository")

    # Load contributor names from CONTRIBUTORS/AUTHORS/README files
    contribs = contributor_names_from_files(project_root)
    
    # Initialize owner_to_canon mapping for metadata owners
    owner_to_canon = {c: c.strip() for c in contribs}

    # Initialize buckets for each contributor from CONTRIBUTORS file
    buckets: Dict[str, Dict[str, List[str]]] = {
        canon: {"files_owned": [], "files_from_metadata": [], "files_from_text": []}
        for canon in set(contribs)
    }
    buckets[UNATTRIBUTED] = {"files_owned": [], "files_from_metadata": [], "files_from_text": []}

    # Cache canonical names for emails and names
    email_to_canon: Dict[str, str] = {}
    name_to_canon: Dict[str, str] = {}

    # Get tracked files from git
    try:
        tracked = set(repo.git.ls_files().splitlines())
    except Exception:
        tracked = set(
            p.relative_to(project_root).as_posix()
            for p in project_root.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )

    # Attribute each tracked file to a contributor
    for rel in tracked:
        try:
            commits = list(repo.iter_commits(paths=str(rel), max_count=1))
        except Exception:
            commits = []
        
        if not commits:
            buckets[UNATTRIBUTED]["files_owned"].append(rel)
            continue

        # Get author information
        commit = commits[0]
        author = getattr(commit, "author", None)
        author_name = getattr(author, "name", None) if author else None
        author_email = getattr(author, "email", None) if author else None

        # Determine canonical name
        if author_email:
            key = author_email.lower()
            if key in email_to_canon:
                canonical = email_to_canon[key]
            else:
                canonical = canonical_for_git(author_name, author_email, contribs, owner_to_canon)
                email_to_canon[key] = canonical
        elif author_name:
            # No email - use name-based matching
            matched = next((existing for existing in name_to_canon if name_matches(existing, author_name)), None)
            if matched:
                canonical = name_to_canon[matched]
            else:
                canonical = canonical_for_git(author_name, None, contribs, owner_to_canon)
                name_to_canon[author_name] = canonical
        else:
            canonical = "<unknown>"

        # Add file to contributor's bucket
        buckets.setdefault(canonical, {"files_owned": [], "files_from_metadata": [], "files_from_text": []})
        buckets[canonical]["files_owned"].append(rel)

    # Handle untracked files (exist on disk but not in git)
    file_map = files_to_owner_map(project_root, FileMetadataExtractor(project_root))
    for rel in file_map.keys():
        if rel not in tracked and rel not in buckets[UNATTRIBUTED]["files_owned"]:
            buckets[UNATTRIBUTED]["files_owned"].append(rel)

    # Finalize results
    return {
        person: {
            "files_owned": sorted(stats["files_owned"]),
            "file_count": len(stats["files_owned"]),
            "files_from_metadata": sorted(stats["files_from_metadata"]),
            "files_from_text": sorted(stats["files_from_text"]),
        }
        for person, stats in buckets.items()
    }

def detect_individual_contributions(project_path: str | Path, *, extractor: Optional[FileMetadataExtractor] = None) -> Dict:
    """
    Entry point: detect individual contributions for collaborative projects.

    Raises ValueError if:
        path is invalid
        project is not marked as collaborative
    """
    
    root = Path(project_path)
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Project path does not exist or is not a directory: {project_path}")

    pt = detect_project_type(root)
    if pt.get("project_type") != "collaborative":
        raise ValueError("Project is not collaborative")

    mode = pt.get("mode", "local")
    if mode == "git":
        try:
            with Repo(root) as repo:
                contributors = detect_individual_contributions_git(root, repo=repo)
                return {"is_collaborative": True, "mode": "git", "contributors": contributors}
        except Exception:
            # Fallback to local mode if Git operations fail
            pass

    # local mode (or fallback)
    contributors = detect_individual_contributions_local(root, extractor=extractor)
    return {"is_collaborative": True, "mode": "local", "contributors": contributors}
