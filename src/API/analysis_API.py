from src.core.analysis_service import (
    analyze_project,
    extract_if_zip,
)
from src.core.app_context import runtimeAppContext

from pathlib import Path

from fastapi import APIRouter, UploadFile

analysisRouter = APIRouter(
    prefix="/analyze"
)

@analysisRouter.get("/")
def perform_analysis_API(use_ai: bool = False) -> str:
    """
    API call for performing analysis on a project folder. Extracts from a zip file if provided Path is a zip file. Analysis is saved.

    HTTP call is GET /analyze
    Optional Get /analyze/?use_ai=bool

    Args:
        use_ai (bool): determines whether analysis uses ai

    Returns:
        str: string stating finished state or error code (Not all errors implemented yet)
    """
    
    folder_path = runtimeAppContext.currently_uploaded_file

    try:
        if isinstance(folder_path, Path):
            if (folder_path.suffix.lower() == ".zip"):
                folder = extract_if_zip(folder_path)
            else:
                folder = folder_path
        else:   #Can only be an UploadFile at this point
            folder = extract_if_zip(folder_path)
        analyze_project(folder, use_ai_analysis=use_ai)
        return "Analysis Finished and Saved"
    except Exception as e:
        return str(e)
