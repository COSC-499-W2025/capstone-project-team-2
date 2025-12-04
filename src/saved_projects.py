import json
from pathlib import Path
from typing import Any

# Utilities for reading, listing, and cleaning up saved analysis artifacts.
from src.app_context import AppContext
from src.oop_aggregator import pretty_print_oop_report


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


def show_saved_summary(path: Path) -> None:
    """
    Display a summary of a saved analysis JSON.

    Args:
        path (Path): Location of the saved analysis file.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {path.name}: {e}")
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

    print(f"\n== {path.name} ==")
    print(f"Project root : {analysis.get('project_root', '—')}")
    print(f"Type         : {pt} (mode={mode})")
    print(f"Languages    : {', '.join(langs) or '—'}")
    print(f"Frameworks   : {', '.join(frws) or '—'}")
    print(f"Skills       : {', '.join(skills) or '—'}")
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

    oop_analysis = analysis.get("oop_analysis")
    if oop_analysis and isinstance(oop_analysis, dict):
        pretty_print_oop_report(oop_analysis)


def get_saved_projects_from_db(ctx: AppContext) -> list[tuple]:
    """
    Fetch all saved projects from the database.

    Args:
        ctx (AppContext): Shared DB context.

    Returns:
        list[tuple]: (id, filename, uploaded_at) rows.
    """
    cursor = ctx.conn.cursor()
    try:
        cursor.execute(
            # We only need identifiers and metadata for deletion checks.
            "SELECT id, filename, uploaded_at "
            "FROM project_data ORDER BY uploaded_at DESC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def delete_from_database_by_id(record_id: int, ctx: AppContext) -> bool:
    """
    Delete a database record by ID.

    Args:
        record_id (int): Primary key to remove.
        ctx (AppContext): Shared DB context.

    Returns:
        bool: True if a record was deleted.
    """
    return ctx.store.delete(record_id)


def delete_file_from_disk(filename: str, ctx: AppContext) -> bool:
    """
    Delete a file only if no remaining DB records reference it.

    Args:
        filename (str): Target filename.
        ctx (AppContext): Shared DB/store context.

    Returns:
        bool: True if the file was removed.
    """
    try:
        base_dir = Path(ctx.default_save_dir).expanduser().resolve()
        file_path = base_dir / filename

        if not file_path.exists():
            legacy_path = base_dir.parent / filename
            if legacy_path.exists():
                file_path = legacy_path
            else:
                return False

        try:
            refs = ctx.store.count_file_references(filename)
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
