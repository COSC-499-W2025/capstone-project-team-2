from src.core.analysis_service import (
    analyze_project,
    extract_if_zip,
)

from pathlib import Path

from fastapi import APIRouter

analysisRouter = APIRouter(
    prefix="/analyze"
)

#Currently Incomplete, need to handle arguments issue
@analysisRouter.get("/")
def perform_analysis_API(folder_path: Path, use_ai: bool = False):
    """
    API call for performing analysis on a project folder. Extracts from a zip file if provided Path is a zip file. Analysis is saved.

    HTTP call is GET /analyze

    Args:
        folder_path (Path): file path of project folder/zip file
        use_ai (bool): determines whether analysis uses ai

    Returns:
        str: string stating finished state
    """
    if (folder_path.suffix.lower() == ".zip"):
        folder_path = extract_if_zip(folder_path)
    analyze_project(folder_path, use_ai_analysis=use_ai)
    return "finished"