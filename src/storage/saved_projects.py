import json
from pathlib import Path
from typing import Any

# Utilities for reading, listing, and cleaning up saved analysis artifacts.
from src.core.app_context import AppContext
from src.aggregation.oop_aggregator import pretty_print_oop_report
from src.core.app_context import runtimeAppContext

def list_saved_projects(folder: Path) -> list[Path]:
    """
    Return saved analysis files from the configured folder and legacy location.

    Args:
        folder (Path): New default storage directory.

    Returns:
        list[Path]: Unique JSON analysis files excluding config artifacts.
    """
    candidate_dirs: list[Path] = []

    if folder.exists():
        candidate_dirs.append(folder)

    legacy_dir = folder.parent
    if legacy_dir.exists() and legacy_dir not in candidate_dirs:
        candidate_dirs.append(legacy_dir)

    if not candidate_dirs:
        return []

    all_files: list[Path] = []
    for d in candidate_dirs:
        all_files.extend(sorted(d.glob("*.json")))

    seen = set()
    unique_files: list[Path] = []
    for f in all_files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(f)

    filtered = [
        f
        for f in unique_files
        if f.name
        not in {
            "UserConfigs.json",
            "default_user_configuration.json",
            "project_insights.json",
        }
    ]

    return filtered


def show_saved_summary(path_or_name: Path | str) -> None:
    """
    Display a summary of a saved analysis JSON.

    Args:
        path_or_name (Path | str): Location of the saved analysis file, or project name.
    """
    # Handle both Path objects and string project names
    if isinstance(path_or_name, str):
        base_dir = Path(runtimeAppContext.default_save_dir).expanduser().resolve()
        path = base_dir / f"{path_or_name}.json"
        display_name = f"{path_or_name}.json"
    else:
        path = path_or_name
        display_name = path.name

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {display_name}: {e}")
        return

    analysis: dict[str, Any] = data if isinstance(data, dict) else {}
    if "analysis" in analysis and isinstance(analysis["analysis"], dict):
        analysis = analysis["analysis"]

    pt = (
        analysis.get("resume_item", {}).get("project_type")
        or analysis.get("project_type", {}).get("project_type", "—")
    )
    mode = (
        analysis.get("resume_item", {}).get("detection_mode")
        or analysis.get("project_type", {}).get("mode", "—")
    )
    stack = analysis.get("resume_item", {}) or {}
    langs = stack.get("languages") or analysis.get("stack", {}).get("languages", [])
    frws = stack.get("frameworks") or analysis.get("stack", {}).get("frameworks", [])
    skills = stack.get("skills") or analysis.get("skills", [])
    duration = analysis.get("duration_estimate", "—")
    summary = stack.get("summary", "—")

    contrib_summary = analysis.get("contribution_summary") or {}
    contributors_raw = (
        analysis.get("contributors")
        or contrib_summary.get("contributors")
        or {}
    )
    contrib_metric = contrib_summary.get("metric", "items")

    contributors_list: list[tuple[str, int, str | None]] = []

    if isinstance(contributors_raw, dict):
        def _count(info: dict) -> int:
            if "file_count" in info:
                return int(info.get("file_count") or 0)
            if "commit_count" in info:
                return int(info.get("commit_count") or 0)
            return len(info.get("files_owned", []))

        tmp: list[tuple[str, int, str | None]] = []
        for name, info in contributors_raw.items():
            count = _count(info)
            if count > 0 or name == "<unattributed>":
                pct = info.get("percentage")
                tmp.append((name, count, pct))
        contributors_list = sorted(tmp, key=lambda tup: tup[1], reverse=True)

    print(f"\n== {display_name} ==")
    print(f"Project root : {analysis.get('project_root', '—')}")
    print(f"Type         : {pt} (mode={mode})")
    print(f"Languages    : {', '.join(langs) or '—'}")
    print(f"Frameworks   : {', '.join(frws) or '—'}")
    print(f"Skills       : {', '.join(skills) or '—'}")
    if "ai_analysis" in analysis.keys():
        print( "  AI Data:")
        print(f"   Structures        : {', '.join(analysis['ai_analysis']['structures_used'])}")
        print(f"   Skills            : {', '.join(analysis['ai_analysis']['design_concepts'])}")
        print(f"   Time Complexities : {', '.join(analysis['ai_analysis']['time_complexities_recorded'])}")
        print(f"   Space Complexities: {', '.join(analysis['ai_analysis']['space_complexities_recorded'])}")
        print(f"   Control Flows     : {', '.join(analysis['ai_analysis']['control_flow_and_error_handling_patterns'])}")
        print(f"   Libraries         : {', '.join(analysis['ai_analysis']['libraries_detected'])}")
        print(f"   Strengths         : {', '.join(analysis['ai_analysis']['inferred_strengths'])}")
    print(f"Duration     : {duration}")
    print()

    if contributors_list:
        print("Contributors :")
        for name, count, pct in contributors_list:
            if pct:
                print(f"  - {name}: {count} {contrib_metric} ({pct})")
            else:
                print(f"  - {name}: {count} {contrib_metric}")
        print()

    if summary and summary != "—":
        print(f"Résumé line  : {summary}")
    print()

    doc_analysis = analysis.get("document_analysis")
    if isinstance(doc_analysis, dict) and doc_analysis:
        doc_summary = doc_analysis.get("summary") or {}
        documents = doc_analysis.get("documents") or []
        duplicates = doc_analysis.get("duplicates") or []
        errors = doc_analysis.get("errors") or []

        unique_count = doc_summary.get("unique_documents", 0)
        dup_count = doc_summary.get("duplicate_documents", 0)
        total_words = doc_summary.get("total_words", 0)
        by_format = doc_summary.get("by_format") or {}
        by_type = doc_summary.get("by_type") or {}

        if unique_count or dup_count or total_words or documents or duplicates or errors:
            fmt_str = ", ".join(f"{k}:{v}" for k, v in by_format.items()) or "—"
            type_str = ", ".join(f"{k}:{v}" for k, v in by_type.items()) or "—"
            all_metrics = []
            all_dates = []
            all_topics = []
            for doc in documents:
                all_metrics.extend(doc.get("metrics") or [])
                all_dates.extend(doc.get("dates") or [])
                all_topics.extend(doc.get("topics") or [])

            def _uniq(seq):
                seen = set()
                out = []
                for item in seq:
                    key = str(item).lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(str(item))
                return out

            all_metrics = _uniq(all_metrics)[:8]
            all_dates = _uniq(all_dates)[:8]
            all_topics = _uniq(all_topics)[:10]

            print("Document analysis:")
            print(f"  Unique docs : {unique_count}")
            print(f"  Duplicates  : {dup_count}")
            print(f"  Total words : {total_words}")
            print(f"  Formats     : {fmt_str}")
            print(f"  Types       : {type_str}")
            if all_topics:
                print(f"  Key topics  : {', '.join(all_topics)}")
            if all_metrics:
                print(f"  Metrics     : {', '.join(all_metrics)}")
            if all_dates:
                print(f"  Dates       : {', '.join(all_dates)}")

            if documents:
                print("  Files:")
                for doc in documents[:10]:
                    doc_path = doc.get("path", "—")
                    doc_format = doc.get("format", "—")
                    doc_words = doc.get("word_count", 0)
                    doc_type = (doc.get("doc_type") or {}).get("label", "unknown")
                    doc_conf = (doc.get("doc_type") or {}).get("confidence", "unknown")
                    print(f"    - {doc_path} ({doc_format}, {doc_words} words, {doc_type}, {doc_conf})")
                    title = doc.get("title")
                    summary = doc.get("summary")
                    key_points = doc.get("key_points") or []
                    authors = doc.get("authors") or []
                    venue = doc.get("venue")
                    year = doc.get("published_year")
                    page_count = doc.get("page_count")
                    refs = doc.get("references_count")
                    figures = doc.get("figure_count")
                    tables = doc.get("table_count")
                    if title:
                        print(f"      Title   : {title}")
                    if authors:
                        print(f"      Authors : {', '.join(authors[:6])}")
                    if venue:
                        if year:
                            print(f"      Venue   : {venue} ({year})")
                        else:
                            print(f"      Venue   : {venue}")
                    if summary:
                        print(f"      Summary : {summary}")
                    if key_points:
                        kp = "; ".join(key_points[:4])
                        print(f"      Highlights: {kp}")
                    metrics_bits = []
                    if page_count:
                        metrics_bits.append(f"{page_count} pages")
                    if refs:
                        metrics_bits.append(f"{refs} references")
                    if figures:
                        metrics_bits.append(f"{figures} figures")
                    if tables:
                        metrics_bits.append(f"{tables} tables")
                    if metrics_bits:
                        print(f"      Doc stats: {', '.join(metrics_bits)}")
                remaining = len(documents) - 10
                if remaining > 0:
                    print(f"    ... and {remaining} more")

            if errors:
                print(f"  Errors      : {len(errors)}")
            print()

    oop_analysis = analysis.get("oop_analysis")
    if oop_analysis and isinstance(oop_analysis, dict):
        pretty_print_oop_report(oop_analysis)


def get_saved_projects_from_db() -> list[tuple]:
    """
    Fetch all saved projects from the database.

    Args:
        None

    Returns:
        list[tuple]: (Pname, uploaded_at) rows.
    """
    cursor = runtimeAppContext.conn.cursor()
    try:
        cursor.execute(
            # We only need identifiers and metadata for deletion checks.
            "SELECT Pname, uploaded_at "
            "FROM project_data ORDER BY uploaded_at DESC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def delete_from_database_by_name(project_name: str) -> bool:
    """
    Delete a database record by project name.

    Args:
        project_name (str): Primary key (Pname) to remove.

    Returns:
        bool: True if a record was deleted.
    """
    return runtimeAppContext.store.delete(project_name)

#TODO remove prints
def delete_file_from_disk(filename: str) -> bool:
    """
    Delete a file only if no remaining DB records reference it.

    Args:
        filename (str): Target filename.

    Returns:
        bool: True if the file was removed.
    """
    try:
        base_dir = Path(runtimeAppContext.default_save_dir).expanduser().resolve()
        file_path = base_dir / filename

        if not file_path.exists():
            legacy_path = base_dir.parent / filename
            if legacy_path.exists():
                file_path = legacy_path
            else:
                return False

        try:
            refs = runtimeAppContext.store.count_file_references(filename)
        except Exception as e:
            print(f"[WARNING] Could not check DB references for '{filename}': {e}")
            return False

        if refs > 0:
            print(
                f"[INFO] File '{filename}' is still referenced by {refs} record(s). "
                "Not deleting."
            )
            return False

        file_path.unlink()
        return True

    except Exception as e:
        print(f"[WARNING] Failed to delete file '{filename}': {e}")
        return False
