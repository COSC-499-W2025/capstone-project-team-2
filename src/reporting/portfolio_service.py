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

    return PortfolioShowcase(
        title=overrides.get("project", {}).get(
            "title", resume_item.get("project_name", "Portfolio Project")
        ),

        role=overrides.get("project", {}).get("role"),

        overview=overrides.get("portfolio", {}).get(
            "overview",
            resume_item.get("summary", "")
        ),

        technical_highlights=overrides.get("portfolio", {}).get(
            "highlights",
            [
                f"{classes.get('count', 0)} classes across multiple languages",
                f"Average {classes.get('avg_methods_per_class', 0)} methods per class",
                f"OOP score: {score.get('oop_score', 'N/A')} ({score.get('rating', '')})",
            ],
        ),

        design_quality={
            "oop_rating": score.get("rating"),
            "oop_comment": score.get("comment"),
            "inheritance_classes": classes.get("with_inheritance"),
            "max_loop_depth": complexity.get("max_loop_depth"),
        },

        evidence={
            "files_analyzed": oop.get("files_analyzed"),
            "total_functions": complexity.get("total_functions"),
            "collection_literals": sum(
                data_structs.get(k, 0)
                for k in [
                    "list_literals",
                    "dict_literals",
                    "set_literals",
                    "tuple_literals",
                ]
            ),
        },

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
    project_root = Path(__file__).resolve().parents[2]
    config_dir = project_root / "User_config_files"
    portfolio_dir = config_dir / "portfolio_overrides"
    portfolio_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize project name for filename
    safe_name = project_name.replace(" ", "_").replace("/", "_")
    yaml_path = portfolio_dir / f"{safe_name}.yaml"
    
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
