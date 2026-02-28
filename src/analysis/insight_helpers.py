"""
Shared helpers for working with project insights.

Responsibilities:
- Parse dates into timezone-aware datetimes
- Filter insight objects by language, skill, or recency
- Compute contribution-first ranking scores and expose rationale components

These are used by menu_insights and can be reused anywhere we need consistent
insight filtering and scoring logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

def parse_date(value: str | None) -> datetime | None:
    """Parse a date/datetime string into a timezone-aware datetime in UTC."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def filter_insights(
    insights: Iterable,
    *,
    language: str | None = None,
    skill: str | None = None,
    since: datetime | None = None,
):
    """Filter insight objects by language, skill, and a minimum analyzed_at timestamp."""
    language_l = language.lower() if language else None
    skill_l = skill.lower() if skill else None
    filtered = []
    for ins in insights:
        if language_l and all(language_l != lang.lower() for lang in ins.languages):
            continue
        if skill_l and all(skill_l != skl.lower() for skl in ins.skills):
            continue

        if since:
            analyzed = parse_date(ins.analyzed_at)
            if analyzed and analyzed < since:
                continue
        filtered.append(ins)
    return filtered

def compute_composite_score(
    insight,
    *,
    contributor: str | None = None,
    tie_break_scale: float = 1e-4,
) -> tuple[float, dict]:
    """
    Compute a contribution-driven ranking score.

    Primary score is the normalized contribution score from ``insight.contribution_score``.
    A tiny count-based tie-break keeps ordering stable when percentages are equal.

    Args:
        insight: Insight-like object that exposes contribution ranking helpers.
        contributor: Optional contributor name to rank by.
        tie_break_scale: Small multiplier applied to raw counts when breaking equal percentages.

    Returns:
        Tuple of ``(score, parts)`` where ``parts`` contains user-facing rationale fields.
    """
    base = float(insight.contribution_score(contributor))

    count = 0
    if hasattr(insight, "contribution_count"):
        try:
            count = int(insight.contribution_count(contributor))
        except Exception:
            count = 0

    metric = "items"
    if hasattr(insight, "contribution_metric"):
        try:
            metric = str(insight.contribution_metric(contributor) or "items")
        except Exception:
            metric = "items"

    basis = "count"
    contributors = getattr(insight, "contributors", {}) or {}
    if contributor and contributor in contributors:
        percentage_value = contributors[contributor].get("contribution_percentage")
        if percentage_value is None:
            percentage_value = contributors[contributor].get("percentage")
        basis = "percentage" if percentage_value is not None else "count"

    tie_break = (max(0, count) * tie_break_scale) if basis == "percentage" else 0.0
    score = base + tie_break

    return score, {
        "basis": basis,
        "contribution": base,
        "count": count,
        "metric": metric,
        "tie_break": tie_break,
    }

__all__ = ["parse_date", "filter_insights", "compute_composite_score"]
