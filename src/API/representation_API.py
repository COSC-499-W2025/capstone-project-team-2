"""
FastAPI endpoints for user-controlled representation preferences.
Supports human-in-the-loop tweaks for how projects are displayed by allowing
custom ordering, chronology fixes, comparison attributes, highlighted skills,
and showcase selections. Preferences are persisted under User_config_files so
they are reused across sessions.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from src.reporting import representation_preferences as prefs
from src.reporting.representation_preferences import apply_preferences, update_preferences

representationRouter = APIRouter(prefix="/representation", tags=["Representation"])

class PreferencesPayload(BaseModel):
    """Partial payload for updating representation preferences."""

    project_order: Optional[List[str]] = None
    chronology_corrections: Optional[Dict[str, Dict[str, str]]] = None
    comparison_attributes: Optional[List[str]] = None
    highlight_skills: Optional[List[str]] = None
    showcase_projects: Optional[List[str]] = None
    project_overrides: Optional[Dict[str, Dict[str, str]]] = None

@representationRouter.get("/preferences")
def get_preferences() -> Dict[str, Any]:
    """
    Return stored representation preferences.

    Returns: Dict[str, Any]: Current saved preferences.
    """

    return prefs.load_preferences()


@representationRouter.post("/preferences")
def set_preferences(payload: PreferencesPayload) -> Dict[str, Any]:
    """
    Update stored representation preferences with user selections.

    Args: payload: Partial preference fields to update.

    Returns: Dict[str, Any]: Updated preferences after persistence.
    """

    updated = update_preferences(payload.model_dump(exclude_none=True))
    return updated


@representationRouter.get("/projects")
def list_projects_with_preferences(
    only_showcase: bool = Query(False),
    snapshot_label: str | None = Query(default=None),
) -> Dict[str, Any]:
    """
    Return project insights ordered and filtered per user preferences.

    Args:
        only_showcase: When True, return only showcase projects if defined.
        snapshot_label: Optional snapshot label to filter incremental uploads.

    Returns: Dict[str, Any]: Ordered projects and applied preference metadata.
    """

    try:
        result = apply_preferences(
            only_showcase=only_showcase,
            snapshot_label=snapshot_label,
        )
        return result
    except HTTPException:
        raise
    except Exception:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=500,
            detail="Unable to load projects with the current representation preferences.",
        )
