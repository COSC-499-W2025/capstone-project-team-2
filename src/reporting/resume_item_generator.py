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
from typing import Any, Dict, List

# These helpers are expected to be provided by sibling modules.
from .project_skill_insights import identify_skills
from ..core.project_stack_detection import detect_project_stack
from ..core.project_type_detection import detect_project_type
from ..analysis.get_contributors_percentage_per_person import contribution_summary
from ..core.document_analysis import DocumentAnalyzer

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
    evidence: Dict[str, Any]


def generate_resume_item(
    project_root: Path | str,
    project_name: str | None = None,
    doc_analysis: Dict[str, Any] | None = None,
    contrib_summary_data: Dict[str, Any] | None = None,
) -> ResumeItem:
    """
    Analyse a project workspace and produce a résumé-ready description.

    Args:
        project_root: Path to the project directory to analyse.
        project_name: Optional explicit project name. Defaults to folder name.
        doc_analysis: Optional pre-computed DocumentAnalyzer output. Reused to avoid double scan.
        contrib_summary_data: Optional pre-computed contribution_summary output. Reused to avoid double scan.

    Returns:
        ResumeItem with curated summary, highlight bullets, and supporting metadata.
    """
    root = Path(project_root)
    resolved_root = root.resolve()

    # Use explicit name if provided; otherwise use the directory name.
    name = project_name or resolved_root.name

    # Determine project type - first try Git analysis
    project_type = "unknown"
    detection_mode = "local"

    _contrib: Dict[str, Any] = contrib_summary_data or {}
    if not _contrib:
        try:
            _contrib = contribution_summary(resolved_root) or {}
        except Exception:
            _contrib = {}

    if _contrib:
        is_collaborative = _contrib.get("is_collaborative", False)
        detection_mode = _contrib.get("mode", "local")
        project_type = "collaborative" if is_collaborative else "individual"

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

    # Build evidence block from doc signals and contributor data.
    # duration is None here — analyze_project backfills it after estimation.
    evidence = _extract_evidence(resolved_root, doc_analysis=doc_analysis, contrib_summary=_contrib)

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
        evidence=evidence,
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


def _extract_evidence(
    root: Path,
    *,
    doc_analysis: Dict[str, Any] | None = None,
    contrib_summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Gather evidence signals from the project for portfolio display.
    Called once in generate_resume_item; stored on ResumeItem.evidence.
    duration is None here — analyze_project backfills it after estimation.
    """
    evidence: Dict[str, Any] = {
        "duration": None,
        "doc_metrics": [],
        "doc_key_points": [],
        "doc_types_found": [],
        "test_file_count": 0,
        "contributor_count": 0,
        "contributor_names": [],
        "contributor_breakdown": {},
    }

    # Test file count
    test_count = 0
    try:
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            parts_lower = [p.lower() for p in f.parts]
            name_lower = f.name.lower()
            if (
                "test" in parts_lower
                or name_lower.startswith("test_")
                or name_lower.endswith("_test.py")
                or name_lower.endswith("_test.java")
                or name_lower.endswith(".test.js")
                or name_lower.endswith(".spec.ts")
            ):
                test_count += 1
    except Exception:
        pass
    evidence["test_file_count"] = test_count

    # Document signals: metrics, key points, doc types
    doc_metrics: List[str] = []
    doc_key_points: List[str] = []
    doc_types_found: List[str] = []
    try:
        result = doc_analysis if isinstance(doc_analysis, dict) else DocumentAnalyzer(root).analyze()
        for doc in result.get("documents", []):
            for m in doc.get("metrics", []):
                if m not in doc_metrics:
                    doc_metrics.append(m)
            if len(doc_metrics) >= 6:
                doc_metrics = doc_metrics[:6]
            for kp in doc.get("key_points", []):
                kp_clean = kp.strip()
                if kp_clean and kp_clean not in doc_key_points and len(kp_clean) > 20:
                    doc_key_points.append(kp_clean)
            if len(doc_key_points) >= 3:
                doc_key_points = doc_key_points[:3]
            doc_type_info = doc.get("doc_type") or {}
            label = doc_type_info.get("label", "")
            confidence = doc_type_info.get("confidence", "")
            if label and label != "unknown" and confidence in ("medium", "high"):
                entry = label
                if label == "research paper":
                    parts = []
                    if doc.get("references_count"):
                        parts.append(f"{doc['references_count']} references")
                    if doc.get("figure_count"):
                        parts.append(f"{doc['figure_count']} figures")
                    if doc.get("table_count"):
                        parts.append(f"{doc['table_count']} tables")
                    if parts:
                        entry = f"research paper ({', '.join(parts)})"
                if entry not in doc_types_found:
                    doc_types_found.append(entry)
    except Exception:
        pass

    evidence["doc_metrics"] = doc_metrics
    evidence["doc_key_points"] = doc_key_points
    evidence["doc_types_found"] = doc_types_found

    # Contributor breakdown
    try:
        cs = contrib_summary or {}
        contributors: Dict[str, Any] = cs.get("contributors") or {}
        if contributors:
            evidence["contributor_count"] = len(contributors)
            evidence["contributor_names"] = sorted(contributors.keys())
            evidence["contributor_breakdown"] = {
                name: info.get("percentage", "")
                for name, info in contributors.items()
                if info.get("percentage")
            }
    except Exception:
        pass

    return evidence

__all__ = ["ResumeItem", "generate_resume_item"]