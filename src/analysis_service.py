import copy
import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.app_context import AppContext
from src.data_extraction import FileMetadataExtractor
from src.extraction import extractInfo
from src.get_contributors_percentage_per_person import contribution_summary
from src.project_duration_estimation import Project_Duration_Estimator
from src.project_insights import record_project_insight
from src.python_oop_metrics import (
    analyze_python_project_oop,
    pretty_print_oop_report,
)
from src.resume_item_generator import generate_resume_item
from src.file_data_saving import SaveFileAnalysisAsJSON


def _input_path(prompt: str, allow_blank: bool = False) -> Optional[Path]:
    """
    Prompt user for a path and loop until it exists.
    Returns path or None.
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
    Validate and extract ZIP using extractInfo.runExtraction().
    Returns Path to extracted folder on success.
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
    Wrap Project_Duration_Estimator.get_duration().
    If successful returns duration estimate, otherwise "unavailable (...)".
    """
    try:
        estimate = Project_Duration_Estimator(hierarchy)
        return str(estimate.get_duration())
    except Exception as e:
        return f"unavailable ({e})"


def convert_datetime_to_string(obj):
    """
    Recursively converts datetime objects to strings in a dictionary or list.
    Also handles timedelta objects.
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


def python_oop_analysis(root: Path, resume, legacy_save_dir: Path) -> Dict[str, Any] | None:
    """
    Runs Python OOP analysis if external AI consent is disabled and the project contains Python code.
    """
    config_path = legacy_save_dir / "UserConfigs.json"
    try:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        has_external = config_data.get("consented", {}).get("external", False)
    except Exception as e:
        print(f"[WARN] Could not read user config, assuming no external consent: {e}")
        has_external = False

    if not has_external and "Python" in resume.languages:
        try:
            print("[INFO] External AI is disabled. Running non-LLM Python analysis...\n")
            oop_metrics = analyze_python_project_oop(root)
            pretty_print_oop_report(oop_metrics)
            return oop_metrics
        except Exception as e:
            print(f"[ERROR] Python OOP analysis failed: {e}")
            return None

    return None


def export_json(project_name: str, analysis: Dict[str, Any], ctx: AppContext) -> None:
    """
    Save analyzed project as a json file and to the database using the default directory.
    """
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
    print(f"[INFO] Saved to filesystem → {file_path}")

    try:
        record_id = ctx.store.insert_json(filename, analysis_serializable)
        print(f"[INFO] Saved to database (ID: {record_id})")
    except Exception as e:
        print(f"[WARNING] Could not save to database: {e}")


def analyze_project(root: Path, ctx: AppContext) -> None:
    """
    Analyze the project at the given root and optionally persist results.
    """
    print(f"\n[INFO] Analyzing: {root}\n")

    hierarchy = FileMetadataExtractor(root).file_hierarchy()
    duration = estimate_duration(hierarchy)
    resume = generate_resume_item(root, project_name=root.name)

    contrib_summary: Dict[str, Any] | None = None
    contributors_data: Dict[str, Any] | None = None
    try:
        if resume.project_type == "collaborative":
            contrib_summary = contribution_summary(root)
            contributors_data = (contrib_summary or {}).get("contributors") or None
    except Exception as e:
        print(f"[WARN] Contribution percentage analysis failed: {e}")
        contrib_summary = None
        contributors_data = None

    analysis: Dict[str, Any] = {
        "project_root": str(root),
        "hierarchy": hierarchy,
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

    if contrib_summary is not None:
        analysis["contribution_summary"] = contrib_summary
    if contributors_data:
        analysis["contributors"] = contributors_data

    print("[SUMMARY]")
    print(f"  Type       : {resume.project_type} (mode={resume.detection_mode})")
    print(f"  Languages  : {', '.join(resume.languages) or '—'}")
    print(f"  Frameworks : {', '.join(resume.frameworks) or '—'}")
    print(f"  Skills     : {', '.join(resume.skills) or '—'}")
    print(f"  Duration   : {duration}\n")

    if contributors_data:
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

    elif resume.project_type == "collaborative":
        print("  Contributors: (could not detect)\n")

    if resume.summary:
        print(f"  Résumé line: {resume.summary}\n")

    oop_metrics = python_oop_analysis(root, resume, ctx.legacy_save_dir)

    if oop_metrics is not None:
        analysis["python_oop_analysis"] = oop_metrics

    analysis = convert_datetime_to_string(analysis)

    try:
        insight = record_project_insight(
            analysis,
            contributors=contributors_data,
        )
        print(
            f"[INFO] Insight recorded for project '{insight.project_name}' "
            f"(id={insight.id})."
        )
    except Exception as e:
        print(f"[WARN] Failed to record project insight: {e}")

    export_json(root.name, analysis, ctx)
