import copy
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Analysis helpers used by the CLI menus for project ingestion and persistence.
from src.core.app_context import AppContext
from src.core.data_extraction import FileMetadataExtractor
from src.core.extraction import extractInfo
from src.analysis.get_contributors_percentage_per_person import contribution_summary
from src.core.project_duration_estimation import Project_Duration_Estimator
from src.reporting.project_insights import record_project_insight
from src.analyzers.multilang_orchestrator import MultiLangOrchestrator
from src.aggregation.oop_aggregator import pretty_print_oop_report
from src.reporting.resume_item_generator import generate_resume_item
from src.storage.file_data_saving import SaveFileAnalysisAsJSON
from src.config.user_startup_config import ConfigLoader
from src.core.ai_data_scrubbing import ai_data_scrubber
from src.core.AI_analysis_code import codeAnalysisAI
from src.core.document_analysis import DocumentAnalyzer
from src.core.portfolio_service import (
    load_portfolio_showcase,
    build_portfolio_showcase,
    display_portfolio_showcase,
)

def input_path(prompt: str, allow_blank: bool = False) -> Optional[Path]:
    """
    Prompt user for a path until it exists.

    Args:
        prompt (str): Message shown to the user.
        allow_blank (bool): If True, empty input returns None.

    Returns:
        Optional[Path]: Resolved path or None when blank is allowed.
    """
    while True:
        p = input(prompt).strip()
        if not p and allow_blank:
            return None
        path = Path(p).expanduser().resolve()
        if path.exists():
            return path
        print(f"[ERROR] Path not found: {path}")


def extract_if_zip(zip_path: Path) -> Path:
    """
    Validate and extract a ZIP archive.

    Args:
        zip_path (Path): Location of the ZIP file.

    Returns:
        Path: Extracted folder path.

    Raises:
        RuntimeError: Extraction returned an empty result.
        ValueError: Extraction reported an error string.
        FileNotFoundError: Expected extracted folder missing.
    """
    out = extractInfo(str(zip_path)).runExtraction()

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


def estimate_duration(hierarchy: Dict[str, Any]) -> str:
    """
    Estimate project duration from a file hierarchy.

    Args:
        hierarchy (Dict[str, Any]): File tree metadata.

    Returns:
        str: Duration string or "unavailable (...)" on failure.
    """
    try:
        estimate = Project_Duration_Estimator(hierarchy)
        return str(estimate.get_duration())
    except Exception as e:
        return f"unavailable ({e})"


def convert_datetime_to_string(obj):
    """
    Recursively convert datetime/timedelta objects to strings.

    Args:
        obj: Arbitrary nested structure containing datetime values.

    Returns:
        Any: Same structure with serialized datetimes.
    """
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(obj, datetime.timedelta):
        return str(obj)
    if isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    return obj


def oop_analysis(root: Path, resume, verbose: bool = True) -> Dict[str, Any] | None:
    """
    Run non-LLM OOP analysis when external AI is disabled and supported languages exist.

    Args:
        root (Path): Project root to scan.
        resume: Resume metadata with detected languages.
        verbose (bool): If True, prints progress to console.

    Returns:
        Dict[str, Any] | None: OOP metrics when run, otherwise None.
    """
    try:
        config_data = ConfigLoader().load()
        has_external = config_data.get("consented", {}).get("external", False)
    except Exception as e:
        if verbose:
            print(f"[WARN] Could not read user config, assuming no external consent: {e}")
        has_external = False

    # Check if project has Python, Java, C, or JavaScript
    supported_languages = {"Python", "Java", "C", "JavaScript"}
    detected_languages = set(resume.languages) & supported_languages

    if not has_external and detected_languages:
        
        try:
            
            langs = ", ".join(sorted(detected_languages))
            if verbose:
                print(f"[INFO] External AI is disabled. Running non-LLM OOP analysis for {langs}...\n")
            oop_metrics = MultiLangOrchestrator(root).analyze()
            if verbose:
                pretty_print_oop_report(oop_metrics)
            return oop_metrics
        
        except (FileNotFoundError, ValueError) as e: 
            
            if verbose:
                print(f"[ERROR] OOP analysis failed: {e}")
            return None

    return None

def export_json(
    project_name: str,
    analysis: Dict[str, Any],
    ctx: AppContext,
    prompt_user: bool = True,
    verbose: bool = True,
) -> None:
    """
    Persist analyzed project to disk and database.

    Args:
        project_name (str): Filename stem for the saved JSON.
        analysis (Dict[str, Any]): Serializable analysis payload.
        ctx (AppContext): Shared DB/store handles.
        prompt_user (bool): If True, ask before saving.
        verbose (bool): If True, log save operations to console.

    Returns:
        None: Writes to filesystem/DB when permitted.
    """
    if prompt_user:
        ans = input("Save JSON report? (y/n): ").strip().lower() or "n"
        if not ans.startswith("y"):
            return

    out_dir = Path(ctx.default_save_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = project_name + ".json"

    analysis_copy = copy.deepcopy(analysis)
    analysis_serializable = convert_datetime_to_string(analysis_copy)

    saver = SaveFileAnalysisAsJSON()
    saver.saveAnalysis(project_name, analysis_serializable, str(out_dir))
    file_path = out_dir / filename
    if verbose:
        print(f"[INFO] Saved to filesystem → {file_path}")

    try:
        record_id = ctx.store.insert_json(filename, analysis_serializable)
        if verbose:
            print(f"[INFO] Saved to database (ID: {record_id})")
    except Exception as e:
        if verbose:
            print(f"[WARNING] Could not save to database: {e}")


def analyze_project(
    root: Path,
    ctx: AppContext,
    project_label: str | None = None,
    use_ai_analysis: bool = False,
    portfolio_mode: bool = False,
    interactive: bool = True,
    save_json: Optional[bool] = None,
    known_doc_hashes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Analyze a project folder and optionally persist results.

    Args:
        root (Path): Project root to scan.
        ctx (AppContext): Shared DB/store handles.
        project_label (str | None): Optional override for saved project name.
        use_ai_analysis (bool): If true, uses ollama AI analysis
        portfolio_mode (bool):
            If True, suppresses full technical reporting and persistence,
            and instead generates and prints a curated portfolio showcase
            derived from analysis results and optional user-authored YAML
            overrides. Defaults to False.
        interactive (bool): When False, suppress console prompts/output for API usage.
        save_json (Optional[bool]): Force saving JSON (True), skip saving (False),
            or prompt the user when interactive (None).
        known_doc_hashes (Optional[Dict[str, str]]): Optional prior document hash index
            used to flag duplicates across incremental uploads.

    Returns:
        Dict[str, Any]: Analysis payload for the project.
    """
    if interactive:
        print(f"\n[INFO] Analyzing: {root}\n")

    display_name = project_label or root.name
    hierarchy = FileMetadataExtractor(root).file_hierarchy()
    duration = estimate_duration(hierarchy)
    resume = generate_resume_item(root, project_name=display_name)
    doc_analysis = DocumentAnalyzer(root, known_hashes=known_doc_hashes).analyze()
    ai_analysis = None
    if use_ai_analysis == True:
        ollamaObject = codeAnalysisAI(root)
        ai_analysis_raw = ollamaObject.run_analysis()
        scrubber = ai_data_scrubber(ai_analysis_raw)
        ai_analysis = scrubber.get_scrubbed_dict()

    contrib_summary: Dict[str, Any] | None = None
    contributors_data: Dict[str, Any] | None = None
    try:
        if resume.project_type == "collaborative":
            contrib_summary = contribution_summary(root)
            contributors_data = (contrib_summary or {}).get("contributors") or None
    except Exception as e:
        if interactive:
            print(f"[WARN] Contribution percentage analysis failed: {e}")
        contrib_summary = None
        contributors_data = None

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

    if not portfolio_mode and interactive:
        print("[SUMMARY]")
        print(f"  Type       : {resume.project_type} (mode={resume.detection_mode})")
        print(f"  Languages  : {', '.join(resume.languages) or '—'}")
        print(f"  Frameworks : {', '.join(resume.frameworks) or '—'}")
        print(f"  Skills     : {', '.join(resume.skills) or '—'}")
        print(f"  Duration   : {duration}\n")

    if contributors_data and interactive:
        metric = (contrib_summary or {}).get("metric", "items")

        def _count(info: dict) -> int:
            if "file_count" in info:
                return int(info.get("file_count") or 0)
            if "commit_count" in info:
                return int(info.get("commit_count") or 0)
            return len(info.get("files_owned", []))

        filtered: list[tuple[str, dict]] = []
        for name, info in contributors_data.items():
            count = _count(info)
            if count > 0 or name == "<unattributed>":
                filtered.append((name, info))

        if filtered:
            print("  Contributors:")
            for name, info in sorted(filtered, key=lambda kv: _count(kv[1]), reverse=True):
                count = _count(info)
                pct = info.get("percentage")
                if pct:
                    print(f"    - {name}: {count} {metric} ({pct})")
                else:
                    print(f"    - {name}: {count} {metric}")
            print()
        else:
            print("  Contributors: (no file ownership data)\n")

    elif resume.project_type == "collaborative" and interactive:
        print("  Contributors: (could not detect)\n")

    if resume.summary and interactive:
        print(f"  Résumé line: {resume.summary}\n")

    oop_metrics = None
    if not portfolio_mode:
        oop_metrics = oop_analysis(root, resume, verbose=interactive)
        
    if oop_metrics is not None:
        analysis["oop_analysis"] = oop_metrics

    analysis = convert_datetime_to_string(analysis)

    try:
        insight = record_project_insight(
            analysis,
            contributors=contributors_data,
        )
        if interactive:
            print(
                f"[INFO] Insight recorded for project '{insight.project_name}' "
                f"(id={insight.id})."
            )
    except Exception as e:
        if interactive:
            print(f"[WARN] Failed to record project insight: {e}")

    portfolio_yaml = load_portfolio_showcase(display_name)
    analysis["portfolio_showcase"] = build_portfolio_showcase(analysis, portfolio_yaml)
    
    if portfolio_mode:
        ps = analysis["portfolio_showcase"]
        if interactive:
            display_portfolio_showcase(ps)
        return analysis

    prompt_for_save = interactive and save_json is None
    if save_json is False:
        should_save = False
        prompt_for_save = False
    else:
        should_save = bool(save_json) or prompt_for_save
    if should_save:
        export_json(
            display_name,
            analysis,
            ctx,
            prompt_user=prompt_for_save,
            verbose=interactive,
        )

    return analysis
