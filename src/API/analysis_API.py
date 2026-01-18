from src.core.analysis_service import (
    input_path,
    analyze_project,
    extract_if_zip,
)

from pathlib import Path
import json
import os

from src.core.app_context import AppContext

def perform_analysis_API(
    ctx: AppContext,
    folder_path: Path,
    use_ai: bool,
):
    """
    API call for performing analysis on a project folder. Extracts from a zip file if provided Path is a zip file. Analysis is saved.

    Args:
        ctx (AppContext): Runtime stored variables, likely to be changed
        folder_path (Path): file path of project folder/zip file
        use_ai (bool): determines whether analysis uses ai

    Returns:
        None
    """
    if folder_path.suffix.lower() == ".zip":
        folder_path = extract_if_zip(folder_path)
    analyze_project(folder_path, ctx, use_ai_analysis=use_ai)
