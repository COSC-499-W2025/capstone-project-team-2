from src.core.analysis_service import (
    analyze_project,
    extract_if_zip,
    safe_project_name,
)
from src.core.app_context import runtimeAppContext

from pathlib import Path
import shutil

from fastapi import APIRouter, HTTPException, UploadFile, status

analysisRouter = APIRouter(
    prefix="/analyze"
)

@analysisRouter.get("/")
def perform_analysis_API(
    use_ai: bool = False,
    project_name: str | None = None,
    remove_duplicates: bool = True,
) -> dict:
    """
    API call for performing analysis on a project folder. Extracts from a zip file if provided Path is a zip file. Analysis is saved.

    HTTP call is GET /analyze
    Optional Get /analyze/?use_ai=bool&remove_duplicates=bool

    Args:
        use_ai (bool): determines whether analysis uses ai
        remove_duplicates (bool): controls whether duplicate files are deleted.

    Returns:
        dict: status message and dedup summary on success; str error on failure under status.
    """
    
    folder_path = runtimeAppContext.currently_uploaded_file
    if folder_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No project has been uploaded yet. Call POST /projects/upload first.",
        )

    extracted_temp_dir: Path | None = None
    try:
        if isinstance(folder_path, Path):
            if not folder_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Uploaded path not found: {folder_path}",
                )
            if (folder_path.suffix.lower() == ".zip"):
                folder = extract_if_zip(folder_path)
                extracted_temp_dir = folder
            else:
                folder = folder_path
        else:   #Can only be an UploadFile at this point
            folder = extract_if_zip(folder_path)
            extracted_temp_dir = folder

        source_project_name = (
            project_name
            or runtimeAppContext.currently_uploaded_project_name
            or folder.name
        )
        effective_project_name = safe_project_name(source_project_name)

        result = analyze_project(
            folder,
            use_ai_analysis=use_ai,
            project_name=effective_project_name,
            remove_duplicates=remove_duplicates,
        ) or {}
        return {
            "status": "Analysis Finished and Saved",
            "dedup": result.get("dedup"),
            "snapshots": result.get("snapshots", []),
            "project_name": effective_project_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {e}",
        )
    finally:
        if extracted_temp_dir is not None:
            shutil.rmtree(extracted_temp_dir, ignore_errors=True)
