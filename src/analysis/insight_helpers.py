"""
Shared helpers for working with project insights.

Responsibilities:
- Parse dates into timezone-aware datetimes
- Filter insight objects by language, skill, or recency
- Compute composite scores that combine contributions, recency, and skill breadth

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
    recency_weight: float = 10.0,
    skill_weight: float = 0.5,
) -> tuple[float, dict]:
    """
    Compute a composite score that favors contribution strength, recency, and skill breadth.

    Returns:
        (score, parts) where parts contains individual components for display.
    """
    base = insight.contribution_score(contributor)
    skill_bonus = len(insight.skills) * skill_weight

    analyzed = parse_date(insight.analyzed_at)
    recency_bonus = 0.0
    age_days = None
    if analyzed:
        age_days = max(0, (datetime.now(timezone.utc) - analyzed).days)
        # Linear decay over one year
        recency_bonus = max(0.0, recency_weight * (1 - min(age_days, 365) / 365))

    score = base + recency_bonus + skill_bonus
    return score, {
        "base": base,
        "recency": recency_bonus,
        "skills": skill_bonus,
        "age_days": int(age_days) if age_days is not None else None,
    }

__all__ = ["parse_date", "filter_insights", "compute_composite_score"]
