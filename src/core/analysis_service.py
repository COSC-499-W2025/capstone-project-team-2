import copy
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from fastapi import UploadFile

# Analysis helpers used by the CLI menus for project ingestion and persistence.
from src.core.app_context import runtimeAppContext
from src.core.data_extraction import FileMetadataExtractor
from src.core.extraction import extractInfo
from src.analysis.get_contributors_percentage_per_person import contribution_summary
from src.core.project_duration_estimation import Project_Duration_Estimator
from src.reporting.project_insights import record_project_insight
from src.analyzers.multilang_orchestrator import MultiLangOrchestrator
from src.reporting.resume_item_generator import generate_resume_item
from src.storage.file_data_saving import SaveFileAnalysisAsJSON
from src.storage.dedup_index import deduplicate_project
from src.core.ai_data_scrubbing import ai_data_scrubber
from src.core.AI_analysis_code import codeAnalysisAI
from src.utils.utility_methods import convert_datetime_to_string
from src.core.document_analysis import DocumentAnalyzer
from src.core.project_stack_detection import detect_project_stack
from src.reporting.portfolio_service import (
    load_portfolio_showcase,
    build_portfolio_showcase,
)
from src.analysis.file_traverser import ProjectTraversalModule

def extract_if_zip(zip_path: Path | UploadFile) -> Path:
    """
    Validate and extract a ZIP archive.

    Args:
        zip_path (Path | UploadPath): Location of the ZIP file or a file-like object.

    Returns:
        Path: Extracted folder path.

    Raises:
        RuntimeError: Extraction returned an empty result.
        ValueError: Extraction reported an error string.
        FileNotFoundError: Expected extracted folder missing.
    """
    out = extractInfo().runExtraction(zip_path)

    if not out:
        raise RuntimeError("Extraction returned empty result.")

    if isinstance(out, str) and (
        out.startswith("Error")
        or "Error!" in out
        or out.lower().startswith("error")
    ):
        raise ValueError(f"Extraction failed: {out}")

    extracted_path = Path(out)
    if not extracted_path.exists():
        raise FileNotFoundError(f"Expected extracted folder not found at: {extracted_path}")

    return extracted_path

def oop_analysis(root: Path, languages_found) -> Dict[str, Any] | None:
    """
    Run OOP analysis when Python/Java/C is present.
    Uses MultiLangOrchestrator to analyze projects containing Python, Java, C, C# and/or C++.

    Args:
        root (Path): Project root to scan.
        languages_found: Languages found in project

    Returns:
        Dict[str, Any] | None: OOP metrics when run, otherwise None.
        
    Critical behavior:
      - If supported languages are present and analysis fails, raise to the API.
      - If no supported languages are present, return None.
    """

    # Check if project has Python, Java, C, or JavaScript
    supported_languages = {"Python", "Java", "C", "JavaScript", "C++", "C#"}
    detected_languages = set(languages_found) & supported_languages

    if not detected_languages:
        return None
        
    return MultiLangOrchestrator(root).analyze() # raise exceptions to api

def export_json(project_name: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist analyzed project to disk and database.

    Args:
        project_name (str): Filename stem for the saved JSON.
        analysis (Dict[str, Any]): Serializable analysis payload.

    Returns:
        Dict[str, Any]: Metadata about the export (currently `{"skipped": False}`).
    """

    out_dir = Path(runtimeAppContext.default_save_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = project_name + ".json"
    dest_path = out_dir / filename

    def _snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a compact snapshot record for incremental uploads."""
        resume = payload.get("resume_item", {}) or {}
        return {
            "analyzed_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
            "project_root": payload.get("project_root"),
            "duration_estimate": payload.get("duration_estimate"),
            "resume_item": resume,
            "project_type": payload.get("project_type"),
            "dedup": payload.get("dedup"),
            "contributors": payload.get("contributors"),
        }

    # Copy to avoid mutating the caller's analysis dict before persistence.
    analysis_copy = copy.deepcopy(analysis)

    # If a previous snapshot exists, preserve its history and append a new entry.
    snapshots: List[Dict[str, Any]] = []
    if dest_path.exists():
        try:
            existing = json.loads(dest_path.read_text(encoding="utf-8"))
        except Exception:
            existing = None

        if isinstance(existing, dict):
            prev_snapshots = existing.get("snapshots")
            if isinstance(prev_snapshots, list):
                snapshots.extend(prev_snapshots)

            # Treat the existing top-level analysis as a snapshot if not already tracked.
            if not prev_snapshots:
                snapshots.append(_snapshot(existing))

            # Merge high-level aggregates so history isn’t lost.
            prev_skills = set(existing.get("resume_item", {}).get("skills", []))
            prev_frameworks = set(existing.get("resume_item", {}).get("frameworks", []))
            analysis_copy.setdefault("resume_item", {})
            analysis_copy["resume_item"].setdefault("skills", [])
            analysis_copy["resume_item"].setdefault("frameworks", [])
            analysis_copy["resume_item"]["skills"] = sorted(
                prev_skills | set(analysis_copy["resume_item"].get("skills", []))
            )
            analysis_copy["resume_item"]["frameworks"] = sorted(
                prev_frameworks | set(analysis_copy["resume_item"].get("frameworks", []))
            )

    snapshots.append(_snapshot(analysis_copy))
    analysis_copy["snapshots"] = snapshots

    saver = SaveFileAnalysisAsJSON()
    saver.saveAnalysis(project_name, analysis_copy, str(out_dir))

    try:
        db_result = runtimeAppContext.store.insert_json(filename, analysis_copy)
        was_update = False
        if isinstance(db_result, tuple):
            _, was_update = db_result
        elif db_result:
            was_update = True
        if was_update:
            print(f"[INFO] Project '{filename}' already exists - updated with new version")
    except Exception as e:
        logging.warning(f"Could not save to database: {e}")

    return {"skipped": False, "snapshots": snapshots}


def analyze_project(
    root: Path,
    use_ai_analysis: bool = False,
    project_name: str | None = None,
    remove_duplicates: bool = True,
) -> Dict[str, Any]:
    """
    Analyze a project folder and persist results.

    Args:
        root (Path): Project root to scan.
        use_ai_analysis (bool): If true, uses ollama AI analysis.
        remove_duplicates (bool): If true, duplicate files are deleted after being recorded.

    Returns:
        None
    """

    display_name = project_name or root.name
    hierarchy = FileMetadataExtractor(root).file_hierarchy()  #Metadata extracted with datetime objects
    try:
        duration = Project_Duration_Estimator(hierarchy).get_duration_human() #Project duration estimate
    except Exception:  #If error, gracefully replace estimation
        duration = "Unknown"

    # Run doc_analysis and contrib_summary once here and pass into generate_resume_item
    # to avoid scanning the project twice.
    doc_analysis = DocumentAnalyzer(root).analyze()

    contrib_summary: Dict[str, Any] | None = None
    contributors_data: Dict[str, Any] | None = None
    try:
        contrib_summary = contribution_summary(root)
        contributors_data = (contrib_summary or {}).get("contributors") or None
    except Exception as e:
        contrib_summary = None
        contributors_data = None

    resume = generate_resume_item(
        root,
        project_name=display_name,
        doc_analysis=doc_analysis,
        contrib_summary_data=contrib_summary,
    )

    # Backfill duration into evidence now that we have it from Project_Duration_Estimator.
    evidence_block = dict(resume.evidence)
    evidence_block["duration"] = duration

    #AI analysis performance through ollama
    ai_analysis = None
    if use_ai_analysis == True:
        ollamaObject = codeAnalysisAI(root)
        ai_analysis_raw = ollamaObject.run_analysis()
        scrubber = ai_data_scrubber(ai_analysis_raw)
        ai_analysis = scrubber.get_scrubbed_dict()

    analysis: Dict[str, Any] = {
        "project_root": str(root),
        "hierarchy": hierarchy,
        "document_analysis": doc_analysis,
        "duration_estimate": duration,
        "resume_item": {
            "project_name": resume.project_name,
            "summary": resume.summary,
            "highlights": resume.highlights,
            "project_type": resume.project_type,
            "detection_mode": resume.detection_mode,
            "languages": resume.languages,
            "frameworks": resume.frameworks,
            "skills": resume.skills,
            "framework_sources": resume.framework_sources,
            "evidence": evidence_block,
        },
        "project_type": {
            "project_type": resume.project_type,
            "mode": resume.detection_mode,
        },
    }

    if ai_analysis:
        analysis["ai_analysis"] = ai_analysis

    if contrib_summary is not None:
        analysis["contribution_summary"] = contrib_summary
    if contributors_data:
        analysis["contributors"] = contributors_data

    # Optional: stack detection (fallback to resume languages only)
    try:
        stack_languages = detect_project_stack(root).get("languages", [])
    except Exception as e:
        logging.warning(f"Project stack detection failed (optional): {e}")
        stack_languages = []

    languages_for_oop = sorted(set(stack_languages) | set(resume.languages))
    oop_metrics = oop_analysis(root, languages_for_oop)  # may raise (critical)

        
    if oop_metrics is not None:
        analysis["oop_analysis"] = oop_metrics

    portfolio_yaml = load_portfolio_showcase(display_name)
    
    portfolio_input = {
        "resume_item": analysis.get("resume_item", {}),
        "contributors": analysis.get("contributors"),
        "oop_analysis": analysis.get("oop_analysis"),
        "document_analysis": analysis.get("document_analysis"),
    }
        
    ps = build_portfolio_showcase(portfolio_input, portfolio_yaml)   
     
    #Project insights likely needs to be rebuilt
    snapshot_label = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    try:
        insight = record_project_insight(
            analysis,
            contributors=contributors_data,
            snapshot_label=snapshot_label,
        )
    except Exception as e:
        logging.warning(f"Failed to record project insight (optional): {e}")
        insight = None 

    #Need to remember this exists but also this can't be here
    #portfolio_yaml = load_portfolio_showcase(display_name)
    #analysis["portfolio_showcase"] = build_portfolio_showcase(analysis, portfolio_yaml)
    #
    #if portfolio_mode:
    #    ps = analysis["portfolio_showcase"]
    #    display_portfolio_showcase(ps)
    #    return

    dedup_result = deduplicate_project(
        root,
        Path(runtimeAppContext.default_save_dir) / "dedup_index.json",
        remove_duplicates=remove_duplicates,
    )
    analysis["dedup"] = {
        "unique_files": dedup_result.unique_files,
        "duplicate_files": dedup_result.duplicate_files,
        "duplicates": dedup_result.duplicates,
        "index_size": dedup_result.index_size,
        "removed": dedup_result.removed,
    }

    export_meta = export_json(display_name, convert_datetime_to_string(analysis)) or {}
    return {
        "dedup": analysis["dedup"],
        "snapshots": export_meta.get("snapshots", []),
    }