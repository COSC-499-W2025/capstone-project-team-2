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
    save_json: bool = False,
    known_doc_hashes: dict | None = None,
):
    """
    Run project analysis for API usage, handling zip extraction and non-interactive mode.

    Args:
        ctx (AppContext): Shared database/storage context.
        folder_path (Path): Path to a project directory or zip file to extract.
        use_ai (bool): Whether to include AI-based code analysis.
        save_json (bool): Persist JSON without prompting when True.
        known_doc_hashes (dict | None): Optional sha256→path map to detect duplicates across uploads.

    Returns:
        dict: Complete analysis payload ready for API response.
    """
    if folder_path.suffix.lower() == ".zip":
        folder_path = extract_if_zip(folder_path)
    return analyze_project(
        folder_path,
        ctx,
        use_ai_analysis=use_ai,
        interactive=False,
        save_json=save_json,
        known_doc_hashes=known_doc_hashes,
    )
