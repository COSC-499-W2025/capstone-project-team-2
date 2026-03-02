"""
Portfolio Service

Responsible for constructing curated, human-readable portfolio narratives
from analysis data. This module is framework-agnostic and
does not perform YAML persistence or PDF rendering.

"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import ruamel.yaml

@dataclass
class PortfolioShowcase:
    """Human-readable portfolio narrative."""

    title: str
    overview: str
    role: str | None
    technical_highlights: List[str]
    design_quality: Dict[str, Any]
    evidence: Dict[str, Any]
    skills: List[str]
    contributors: List[str]

def build_portfolio_showcase(
    analysis: dict,
    overrides: dict | None = None
) -> PortfolioShowcase:
    """
    Build curated portfolio showcase content from analysis output.

    Args:
        analysis (dict): Full project analysis output.
        overrides (dict, optional): Human-authored overrides.

    Returns:
        PortfolioShowcase: Structured portfolio narrative.
    """
    overrides = overrides or {}

    resume_item = analysis.get("resume_item", {})
    oop = analysis.get("oop_analysis") or {}

    score = oop.get("score", {})
    classes = oop.get("classes", {})
    complexity = oop.get("complexity", {})
    data_structs = oop.get("data_structures", {})

    # Pull evidence stored on resume_item by analyze_project.
    ev = resume_item.get("evidence") or {}
    duration = ev.get("duration")
    contributor_count = ev.get("contributor_count", 0)
    contributor_breakdown = ev.get("contributor_breakdown") or {}
    doc_metrics = ev.get("doc_metrics") or []
    doc_key_points = ev.get("doc_key_points") or []
    doc_types_found = ev.get("doc_types_found") or []
    test_file_count = ev.get("test_file_count") or 0

    # Pull richer signals directly from document_analysis for topics and summaries.
    doc_analysis = analysis.get("document_analysis") or {}
    documents = doc_analysis.get("documents") or []
    doc_topics: List[str] = []
    doc_summaries: List[str] = []
    for doc in documents:
        for t in (doc.get("topics") or []):
            if t not in doc_topics:
                doc_topics.append(t)
        s = (doc.get("summary") or "").strip()
        if s and len(s) > 30 and s not in doc_summaries:
            doc_summaries.append(s)

    # Overview: resume summary (terse) + duration/team context + doc-extracted summary.
    base_summary = resume_item.get("summary", "")
    overview_parts = [base_summary] if base_summary else []
    if duration and duration != "Unknown":
        if contributor_count > 1:
            overview_parts.append(
                f"Developed over {duration} as part of a team of {contributor_count} contributors."
            )
        else:
            overview_parts.append(f"Developed over {duration}.")
    if doc_summaries:
        overview_parts.append(doc_summaries[0])
    elif doc_key_points:
        overview_parts.append(doc_key_points[0])
    default_overview = " ".join(overview_parts)

    # Technical highlights: OOP narrative prose first, then counts and score.
    oop_narrative = ev.get("oop_narrative") or ""
    default_highlights: List[str] = []
    if oop_narrative:
        default_highlights.append(oop_narrative)
    if classes.get("count", 0):
        default_highlights.append(
            f"{classes['count']} class(es) with an average of "
            f"{classes.get('avg_methods_per_class', 0)} methods per class."
        )
    default_highlights.append(
        f"OOP score: {score.get('oop_score', 'N/A')} ({score.get('rating', '')})"
    )

    # Evidence: all quantifiable signals. More thorough than the resume.
    built_evidence: Dict[str, Any] = {}
    if oop.get("files_analyzed") is not None:
        built_evidence["files_analyzed"] = oop["files_analyzed"]
    if complexity.get("total_functions") is not None:
        built_evidence["total_functions"] = complexity["total_functions"]
    collection_literals = sum(
        data_structs.get(k, 0)
        for k in ("list_literals", "dict_literals", "set_literals", "tuple_literals")
    )
    if collection_literals:
        built_evidence["collection_literals"] = collection_literals
    if test_file_count:
        built_evidence["test_files"] = test_file_count
    if duration and duration != "Unknown":
        built_evidence["project_duration"] = duration
    if doc_metrics:
        built_evidence["extracted_metrics"] = doc_metrics
    if doc_key_points:
        built_evidence["key_achievements"] = doc_key_points
    if doc_types_found:
        built_evidence["document_types"] = doc_types_found
    if doc_topics:
        built_evidence["topics"] = doc_topics[:6]
    if contributor_breakdown:
        built_evidence["contributor_breakdown"] = contributor_breakdown

    return PortfolioShowcase(
        title=overrides.get("project", {}).get(
            "title", resume_item.get("project_name", "Portfolio Project")
        ),

        role=overrides.get("project", {}).get("role"),

        overview=overrides.get("portfolio", {}).get("overview", default_overview),

        technical_highlights=overrides.get("portfolio", {}).get(
            "highlights", default_highlights
        ),

        design_quality={
            "oop_rating": score.get("rating"),
            "oop_comment": score.get("comment"),
            "inheritance_classes": classes.get("with_inheritance"),
            "max_loop_depth": complexity.get("max_loop_depth"),
        },

        evidence=built_evidence,

        skills=resume_item.get("skills", []),
        contributors=list((analysis.get("contributors") or {}).keys()),
    )

def display_portfolio_showcase(ps: PortfolioShowcase) -> None:
    """
    Pretty-print portfolio showcase to CLI.

    Args:
        ps (PortfolioShowcase): Portfolio showcase data.

    Returns:
        None
    """
    
    print("\n===============================")
    print(" PORTFOLIO SHOWCASE")
    print("===============================\n")

    print(f"Project: {ps.title}")
    if ps.role:
        print(f"Role   : {ps.role}\n")

    if ps.overview:
        print("Overview:")
        print(ps.overview, "\n")

    if ps.technical_highlights:
        print("Technical Highlights:")
        for h in ps.technical_highlights:
            print(f"• {h}")
        print()

    if ps.design_quality:
        print("Design Quality:")
        for k, v in ps.design_quality.items():
            if v is not None:
                label = k.replace("_", " ").title()
                print(f"• {label}: {v}")
        print()

    if ps.evidence:
        print("Evidence:")
        for k, v in ps.evidence.items():
            if v is not None:
                label = k.replace("_", " ").title()
                print(f"• {label}: {v}")
        print()

    if ps.skills:
        print("Skills:")
        for s in ps.skills:
            print(f"• {s}")
        print()

    if ps.contributors:
        print("Contributors:")
        for c in ps.contributors:
            print(f"• {c}")
        print()

@dataclass
class PortfolioData:
    """Container for portfolio showcase and full analysis data."""
    
    showcase: PortfolioShowcase
    analysis: Dict[str, Any]


def load_portfolio_showcase(project_name: str) -> Dict[str, Any]:
    """
    Load portfolio YAML overrides for a project.
    
    Looks for a YAML file in the User_config_files directory that contains
    human-authored overrides for portfolio display (title, role, overview, highlights).
    
    Args:
        project_name (str): Name of the project to load overrides for.
    
    Returns:
        dict: Portfolio override data, or empty dict if file not found or invalid.
    """
    yaml_path = _portfolio_override_path(project_name)
    
    if not yaml_path.exists():
        return {}
    
    try:
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.load(f) or {}
    except Exception as e:
        print(f"[WARNING] Could not parse portfolio YAML for '{project_name}': {e}")
        return {}


def _portfolio_override_path(project_name: str) -> Path:
    """
    Resolve the YAML override path for a project showcase.

    Args:
        project_name (str): Project display name.

    Returns:
        Path: Normalized YAML path under User_config_files/portfolio_overrides.
    """
    project_root = Path(__file__).resolve().parents[2]
    portfolio_dir = project_root / "User_config_files" / "portfolio_overrides"
    portfolio_dir.mkdir(parents=True, exist_ok=True)
    safe_name = project_name.replace(" ", "_").replace("/", "_")
    return portfolio_dir / f"{safe_name}.yaml"


def save_project_role_override(project_name: str, role: str) -> Dict[str, Any]:
    """
    Persist a human-authored role override for a project showcase.

    Args:
        project_name (str): Project name used for override lookup.
        role (str): Role text supplied by the user.

    Returns:
        Dict[str, Any]: Full merged override payload after saving.
    """
    yaml_path = _portfolio_override_path(project_name)
    overrides = load_portfolio_showcase(project_name)
    if not isinstance(overrides, dict):
        overrides = {}

    project_block = overrides.get("project")
    if not isinstance(project_block, dict):
        project_block = {}
    project_block["role"] = role
    overrides["project"] = project_block

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(overrides, f)

    return overrides