"""FastAPI endpoint for listing skills from stored project insights."""

from pathlib import Path
from fastapi import APIRouter, HTTPException

from src.core.app_context import runtimeAppContext
from src.reporting.project_insights import list_skill_history

skillsRouter = APIRouter()

@skillsRouter.get("/skills")
def list_skills(detailed: bool = False) -> list:
    """
    Return unique skills (default) or full skill history when detailed.

    Args:
        detailed: When True, returns per-project skill history entries.

    Returns:
        list: Unique skill names or detailed skill history records.
    """
    
    # Wrapped in try-catch block because: 
    # 1. runtimeAppContext.legacy_save_dir could be None, which can cause a TypeError
    # 2. list_skill_history() could fail for other reasons (corrupted JSON, permission issues)
    
    try:
        storage_path = Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"
        history = list_skill_history(storage_path=storage_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve skills: {exc}",
        )

    if detailed:
        return history

    skills = sorted(
        {
            skill
            for entry in history
            for skill in entry.get("skills", [])
            if skill
        }
    )
    return skills
