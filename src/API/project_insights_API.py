from sys import prefix
from fastapi import APIRouter
from pathlib import Path

from src.reporting.project_insights import (
    list_project_insights,
    list_skill_history,
    rank_projects_by_contribution,
    summaries_for_top_ranked_projects,
)

from src.core.app_context import runtimeAppContext
from src.reporting.representation_preferences import apply_preferences
from src.analysis.insight_helpers import parse_date, filter_insights

insights_router = APIRouter(prefix="/insights")

@insights_router.get("/projects")
def return_insight_projects_chronological(language: str | None = None, skill: str | None = None, since_str: str | None = None):
    """
    Chronologically lists all projects that have been analyzed. Can filter by language, skill, and by projects completed after a date.

    API call is "/insights/projects?language=str&skill=str&since_str=str

    Args:
        language (str): languages to filter projects by
        skill (str): skill to filter projects by
        since_str (str): string date to filter projects from after that date

    Returns:
        List[dict]: A list of dictionaries representing projects in the format of a ProjectInsight. The list is projects in chronological order.
    """
    storage_path = Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"

    since_dt = parse_date(since_str)

    projects = list_project_insights(storage_path=storage_path)
    projects = filter_insights(
        projects,
        language=language,
        skill=skill,
        since=since_dt,
    )
    #cannot return namespaces or ProjectInsight objects through api calls so we need to convert to dicts
    filtered_projects = []
    for p in projects:
        filtered_projects.append(p.to_dict())
    return filtered_projects

@insights_router.get("/skills")
def return_insights_skills_chronological(skill: str | None = None, since_str: str | None = None):
    """
    Chronologically lists all skills and the projects they are from. Can filter by skill, and by projects completed after a date.

    API call is "/insights/skills?skill=str&since_str=str

    Args:
        skill (str): skill to filter projects by
        since_str (str): string date to filter projects from after that date

    Returns:
        List[dict]: A list of dictionaries representing projects in the format of a ProjectInsight. The list is skills in projects in chronological order.
    """
    storage_path = Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"

    since_dt = parse_date(since_str)

    history = list_skill_history(storage_path=storage_path)
    if since_dt or skill:
        filtered = []
        for entry in history:
            when = parse_date(entry.get("analyzed_at"))
            if since_dt and when and when < since_dt:
                continue
            if skill and all(skill.lower() != s.lower() for s in entry.get("skills", [])):
                continue
            filtered.append(entry)
        history = filtered
    return history