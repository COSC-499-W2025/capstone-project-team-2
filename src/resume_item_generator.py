"""
resume_item_generator
=====================

Core logic for generating résumé-ready items from a project workspace.

This module exposes:
- `ResumeItem`: a dataclass with structured project details
- `generate_resume_item`: the main entry point that inspects a project root,
  detects languages/frameworks/skills, infers collaboration context, and composes
  a succinct résumé summary with highlight bullets.

Design goals:
- Deterministic output (sorted lists)
- Separation of concerns (type detection, stack detection, skills inference)
- Readable, ATS-friendly text for summaries and highlights
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

# These helpers are expected to be provided by sibling modules.
from .project_skill_insights import identify_skills
from .project_stack_detection import detect_project_stack
from .project_type_detection import detect_project_type
from .get_contributors_percentage_per_person import get_contributors_percentages_git

@dataclass(frozen=True)
class ResumeItem:
    """
    Structured representation of a résumé-ready project highlight.

    Attributes:
        project_name: Human readable project name.
        summary: Single sentence résumé summary tailored to detected signals.
        highlights: Supporting bullet points offering quick context.
        project_type: individual/collaborative/unknown classification.
        detection_mode: Whether the classification came from git or local cues.
        languages: Sorted list of detected programming languages.
        frameworks: Sorted list of detected frameworks or tooling.
        skills: Sorted list of higher level skills inferred from dependencies.
        framework_sources: Map of framework → evidence file paths relative to root.
    """

    project_name: str
    summary: str
    highlights: List[str]
    project_type: str
    detection_mode: str
    languages: List[str]
    frameworks: List[str]
    skills: List[str]
    framework_sources: Dict[str, List[str]]


def generate_resume_item(project_root: Path | str, project_name: str | None = None) -> ResumeItem:
    """
    Analyse a project workspace and produce a résumé-ready description.

    Args:
        project_root: Path to the project directory to analyse.
        project_name: Optional explicit project name. Defaults to folder name.

    Returns:
        ResumeItem with curated summary, highlight bullets, and supporting metadata.
    """
    root = Path(project_root)
    resolved_root = root.resolve()

    # Use explicit name if provided; otherwise use the directory name.
    name = project_name or resolved_root.name

    # Determine project type - first try Git analysis
    project_type = "unknown"  # Fixed: always initialize with fallback
    detection_mode = "local"
    
    try:
        project_type_git = get_contributors_percentages_git(str(resolved_root)).output_result()
        if project_type_git != "Data unsuccessfully collected":
            project_type_bool = project_type_git.get("is_collaborative")
            if project_type_bool is True:
                project_type = "collaborative"
                detection_mode = "git"
            elif project_type_bool is False:
                project_type = "individual"
                detection_mode = "git"
    except Exception:
        pass  # Git analysis failed, use fallback below

    # If Git analysis failed or returned unknown, use detect_project_type as fallback
    if project_type == "unknown":
        project_type_info = detect_project_type(resolved_root)
        project_type = project_type_info.get("project_type", "unknown")
        detection_mode = str(project_type_info.get("mode", "local")).lower()

    # Detect programming languages and frameworks/tools from the project.
    stack_info = detect_project_stack(resolved_root)
    languages = sorted(stack_info.get("languages", []))
    frameworks = sorted(stack_info.get("frameworks", []))
    framework_sources = {
        key: sorted(value) for key, value in stack_info.get("framework_sources", {}).items()
    }

    # Infer higher-level skills and sort to ensure deterministic output.
    skills = sorted(identify_skills(resolved_root))

    # Compose résumé-ready text.
    summary = _compose_summary(
        name=name,
        project_type=project_type,
        languages=languages,
        frameworks=frameworks,
        detection_mode=detection_mode,
    )

    highlights = _compose_highlights(
        languages=languages,
        frameworks=frameworks,
        skills=skills,
        detection_mode=detection_mode,
        project_type=project_type,
    )

    return ResumeItem(
        project_name=name,
        summary=summary,
        highlights=highlights,
        project_type=project_type,
        detection_mode=detection_mode,
        languages=languages,
        frameworks=frameworks,
        skills=skills,
        framework_sources=framework_sources,
    )


def _compose_summary(
    *,
    name: str,
    project_type: str,
    languages: List[str],
    frameworks: List[str],
    detection_mode: str,
) -> str:
    """
    Build the single-sentence summary line for the résumé.

    Persona verb changes based on project type:
      - collaborative → "Collaborated to deliver ..."
      - individual   → "Built ..."
      - unknown      → "Developed ..."
    """
    persona = {
        "collaborative": "Collaborated to deliver",
        "individual": "Built",
    }.get(project_type, "Developed")

    stack_descriptor = _describe_stack(languages, frameworks)

    # Add a subtle Git collaboration cue to the summary when relevant.
    git_phrase = ", leveraging Git-backed collaboration" if detection_mode == "git" else ""

    return f"{persona} {name}{stack_descriptor}{git_phrase}.".strip()


def _compose_highlights(
    *,
    languages: List[str],
    frameworks: List[str],
    skills: List[str],
    detection_mode: str,
    project_type: str,
) -> List[str]:
    """
    Build an ordered list of highlights.
    Order:
      1) Implementation note (stack)
      2) Skills summary
      3) Git workflow note (if applicable)
    Fallback:
      - Return a single generic bullet if no signals are present.
    """
    highlights: List[str] = []

    # 1) Stack implementation note
    if languages or frameworks:
        stack_text = _describe_stack(languages, frameworks, prefix=" using ")
        highlights.append(f"Implemented core functionality{stack_text}.")

    # 2) Skills summary
    if skills:
        highlights.append(f"Demonstrated skills: {_format_list(skills)}.")

    # 3) Git collaboration/management note (only if applicable)
    if detection_mode == "git":
        verb = "coordinated" if project_type == "collaborative" else "managed"
        highlights.append(f"{verb.capitalize()} version control workflows in Git.")

    # Fallback when no signals are present
    return highlights or ["Documented project insights ready for résumé inclusion."]


def _describe_stack(
    languages: List[str],
    frameworks: List[str],
    prefix: str = " with ",
) -> str:
    """
    Convert language/framework lists into a short descriptor string.

    Examples:
      languages=["Python"], frameworks=["Flask"]
      → " with Python; framework Flask"
    """
    if not languages and not frameworks:
        return ""

    segments: List[str] = []
    if languages:
        segments.append(_format_list(languages))
    if frameworks:
        descriptor = "frameworks" if len(frameworks) > 1 else "framework"
        segments.append(f"{descriptor} {_format_list(frameworks)}")

    stack_text = "; ".join(segments)
    return f"{prefix}{stack_text}"


def _format_list(items: List[str]) -> str:
    """Oxford-comma style list formatting for readability."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


__all__ = ["ResumeItem", "generate_resume_item"]


