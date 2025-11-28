import json
import sys
from pathlib import Path
from typing import Any, Dict,Optional
import datetime
import zipfile

sys.path.append(str(Path(__file__).resolve().parents[1]))
# Local module Imports
from src.CLI_Interface_for_user_config import ConfigurationForUsersUI
from src.user_consent import UserConsent
from src.data_extraction import FileMetadataExtractor
from src.extraction import extractInfo
from src.project_duration_estimation import Project_Duration_Estimator
from src.resume_item_generator import generate_resume_item
from src.user_startup_config import ConfigLoader
from src.file_data_saving import SaveFileAnalysisAsJSON
from src.db_helper_function import HelperFunct
from src.Docker_finder import DockerFinder
from src.Configuration import configuration_for_users
from src.individual_contribution_detection import detect_individual_contributions
from src.project_insights import (
    record_project_insight,
    list_project_insights,
    rank_projects_by_contribution,
)
import mysql.connector
from mysql.connector import Error


# Connection code for MySQL Docker container
port_number,host_ip= DockerFinder().get_mysql_host_information()
for attempt in range(5):
    try:
        conn = mysql.connector.connect(
            host= host_ip,         # matches the service name in docker-compose.yml
            port=port_number,
            database="appdb",
            user="appuser",
            password="apppassword"
        )

        if conn.is_connected():
            print("✅ Connected to MySQL successfully!")
            break
    except Error as e:
        print(f"MySQL not ready yet: {e}")

if conn is None or not conn.is_connected():
    raise Exception("❌ Could not connect to MySQL after 5 attempts.")

store = HelperFunct(conn)

root_folder = Path(__file__).absolute().resolve().parents[1]
# Legacy location: User_config_files
LEGACY_SAVE_DIR = root_folder / "User_config_files"
# New location: nested project_insights folder
DEFAULT_SAVE_DIR = LEGACY_SAVE_DIR / "project_insights"


def _input_path(prompt: str, allow_blank: bool = False) -> Optional[Path]:
    """
    prompt user for a path and loop until it exists
    returns path or none 

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
    uses extractInfo.runExtraction() to validate and extract ZIP
    Returns Path to extracted folder on success, or None on error.
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
    Wraps Project_Duration_Estimator.get_duration().
    If successful returns duration estimate, otherwise "unavailable (...)".
    """
    try:
        estimate = Project_Duration_Estimator(hierarchy)
        return str(estimate.get_duration())
    except Exception as e:
        return f"unavailable ({e})"


def analyze_project(root: Path) -> None:
    """
    Takes in the path for a project folder.
    Prints analysis of the file including the file hierarchy, duration of the project,
    summary, type, language, framework etc.
    Can also output a json file for saving
    """
    print(f"\n[INFO] Analyzing: {root}\n")

    hierarchy = FileMetadataExtractor(root).file_hierarchy()
    duration = estimate_duration(hierarchy)
    resume = generate_resume_item(root, project_name=root.name)

    # --- detect individual contributions if collaborative ---
    contributors_data = None
    try:
        if resume.project_type == "collaborative" and detect_individual_contributions:
            contrib_result = detect_individual_contributions(root)
            # contrib_result looks like:
            # {"is_collaborative": True, "mode": "git" | "local", "contributors": {...}}
            contributors_data = contrib_result.get("contributors") or None
    except ValueError:
        # Raised if the project isn’t actually collaborative, etc.
        contributors_data = None
    except Exception as e:
        print(f"[WARN] Failed to detect individual contributions: {e}")
        contributors_data = None

    analysis = {
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
    if contributors_data:
        analysis["contributors"] = contributors_data

    analysis = convert_datetime_to_string(analysis)

    # --- "insight" entry for this analysis ---
    try:
        # If you later compute contributors, pass them here instead of None.
        insight = record_project_insight(
            analysis,
            contributors=contributors_data,
        )
        print(
            f"[INFO] Insight recorded for project '{insight.project_name}' "
            f"(id={insight.id})."
        )
    except Exception as e:
        # Never kill the CLI just because logging failed.
        print(f"[WARN] Failed to record project insight: {e}")

    print("[SUMMARY]")
    print(f"  Type       : {resume.project_type} (mode={resume.detection_mode})")
    print(f"  Languages  : {', '.join(resume.languages) or '—'}")
    print(f"  Frameworks : {', '.join(resume.frameworks) or '—'}")
    print(f"  Skills     : {', '.join(resume.skills) or '—'}")
    print(f"  Duration   : {duration}\n")
    print()

    if resume.summary:
        print(f"  Résumé line: {resume.summary}\n")

    # contributor breakdown (if we have it)
    if contributors_data:
        """
        Keep only contributors who actually own files and "<unattributed>" so 
        the user can still see how many files were in the project but not
        attributed to a specific person.
        """
        filtered: list[tuple[str, int]] = []
        for name, info in contributors_data.items():
            file_count = int(info.get("file_count", len(info.get("files_owned", []))))
            if file_count > 0 or name == "<unattributed>":
                filtered.append((name, file_count))

        if filtered:
            print("  Contributors:")
            for name, file_count in sorted(filtered, key=lambda kv: kv[1], reverse=True):
                print(f"    - {name}: {file_count} files")
            print()
        else:
            print("  Contributors: (no file ownership data)\n")

    elif resume.project_type == "collaborative":
        # Collaborative but we couldn’t compute contributions
        print("  Contributors: (could not detect)\n")

    export_json(root.name, analysis)


def convert_datetime_to_string(obj):
    """
    Recursively converts datetime objects to strings in a dictionary or list.
    Also handles timedelta objects.
    """
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, datetime.timedelta):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    else:
        return obj


def export_json(project_name: str, analysis: Dict[str, Any]) -> None:
    """
    Saves an analyzed project as a json file and to the database.
    Always saves to the default directory (User_config_files/project_insights).
    """
    ans = input("Save JSON report? (y/n): ").strip().lower() or "n"
    if ans.startswith("y"):
        # Always use default directory
        out_dir = Path(DEFAULT_SAVE_DIR).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = project_name + ".json"

        # Deep copy and convert datetime objects to strings for JSON serialization
        import copy

        analysis_copy = copy.deepcopy(analysis)
        analysis_serializable = convert_datetime_to_string(analysis_copy)

        # Save to filesystem
        saver = SaveFileAnalysisAsJSON()
        saver.saveAnalysis(project_name, analysis_serializable, str(out_dir))
        file_path = out_dir / filename
        print(f"[INFO] Saved to filesystem → {file_path}")

        # Save to database
        try:
            record_id = store.insert_json(filename, analysis_serializable)
            print(f"[INFO] Saved to database (ID: {record_id})")
        except Exception as e:
            print(f"[WARNING] Could not save to database: {e}")


def list_saved_projects(folder: Path) -> list[Path]:
    """
    Takes in a folder and returns a list of the files in that folder.
    Filters out config files like UserConfigs.json and default_user_configuration.json.
    To avoid breaking existing users, we also check the legacy location
    (the parent of the configured folder) so that previously saved analyses
    still show up after the DEFAULT_SAVE_DIR change.
    """
    candidate_dirs: list[Path] = []

    if folder.exists():
        candidate_dirs.append(folder)

    # Also include the legacy directory (parent of the new folder),
    # which holds older analyses written before the nested project_insights
    # structure was introduced.
    legacy_dir = folder.parent
    if legacy_dir.exists() and legacy_dir not in candidate_dirs:
        candidate_dirs.append(legacy_dir)

    if not candidate_dirs:
        return []

    all_files: list[Path] = []
    for d in candidate_dirs:
        all_files.extend(sorted(d.glob("*.json")))

    # Deduplicate paths in case the same file appears in multiple directories.
    seen = set()
    unique_files: list[Path] = []
    for f in all_files:
        resolved = f.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_files.append(f)

    # Exclude config files
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
    Displays the summary of the saved file.
    Takes in path to the file; outputs a printed summary.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {path.name}: {e}")
        return

    analysis = data if isinstance(data, dict) else {}
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
    summary = (analysis.get("resume_item", {}) or {}).get("summary", "—")

    contributors_raw = analysis.get("contributors") or {}
    contributors_list: list[tuple[str, int, dict]] = []

    if isinstance(contributors_raw, dict):
        tmp: list[tuple[str, int, dict]] = []
        for name, info in contributors_raw.items():
            file_count = int(info.get("file_count", len(info.get("files_owned", []))))
            if file_count > 0 or name == "<unattributed>":
                tmp.append((name, file_count, info))
        # sort by file_count descending
        contributors_list = sorted(tmp, key=lambda tup: tup[1], reverse=True)


    print(f"\n== {path.name} ==")
    print(f"Project root : {analysis.get('project_root', '—')}")
    print(f"Type         : {pt} (mode={mode})")
    print(f"Languages    : {', '.join(langs) or '—'}")
    print(f"Frameworks   : {', '.join(frws) or '—'}")
    print(f"Skills       : {', '.join(skills) or '—'}")
    print(f"Duration     : {duration}")

    # contributors from saved JSON
    if contributors_list:
        print("Contributors :")
        for name, file_count, _info in contributors_list:
            print(f"  - {name}: {file_count} files")
        print()

    # print
    if summary and summary != "—":
        print(f"Résumé line  : {summary}")
    print()

def get_saved_projects_from_db() -> list[tuple]:
    """
    Fetches all saved projects from the database.
    Returns a list of tuples: (id, filename, content, uploaded_at)
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, filename, content, uploaded_at "
            "FROM project_data ORDER BY uploaded_at DESC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def delete_from_database_by_id(record_id: int) -> bool:
    """
    Deletes a database record by ID.
    Returns True if a record was deleted, False otherwise.
    """
    return store.delete(record_id)


def delete_file_from_disk(filename: str) -> bool:
    """
    Deletes a file only if no remaining DB records reference it.
    Returns True if deleted, False otherwise.
    Supports both the new DEFAULT_SAVE_DIR and the legacy directory
    where analyses were previously stored.
    """
    try:
        base_dir = Path(DEFAULT_SAVE_DIR).expanduser().resolve()
        file_path = base_dir / filename

        # If file does not exist in the new location, try legacy location.
        if not file_path.exists():
            legacy_path = base_dir.parent / filename
            if legacy_path.exists():
                file_path = legacy_path
            else:
                # Nothing to delete in either location.
                return False

        # Check DB references
        try:
            refs = store.count_file_references(filename)
        except Exception as e:
            print(f"[WARNING] Could not check DB references for '{filename}': {e}")
            return False

        if refs > 0:
            print(
                f"[INFO] File '{filename}' is still referenced by {refs} record(s). "
                "Not deleting."
            )
            return False

        # Safe to delete
        file_path.unlink()
        return True

    except Exception as e:
        print(f"[WARNING] Failed to delete file '{filename}': {e}")
        return False


# ---------- Menus ----------
def settings_menu() -> None:
    cfg = ConfigLoader().load()
    ConfigurationForUsersUI(cfg).run_configuration_cli()


def analyze_project_menu() -> None:
    """
    Asks user if their project is in a directory or zip file.
    If zip project, uses extract_if_zip to send for extraction and then to analyze_project()
    for processing. If directory, will send directly to analyze_project() for processing.
    """
    while True:
        print("\n=== Analyze Project Menu ===")
        print("\nChoose input type:")

        print("  1) Directory")
        print("  2) ZIP file")
        print("  0) Exit to Main Menu")

        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                dir = _input_path("Enter path to project directory: ")
                return analyze_project(dir)
            elif choice == "2":
                zip = _input_path("Enter path to ZIP: ")
                extracted = extract_if_zip(zip)
                if not extracted:
                    print(
                        "[ERROR] Could not extract ZIP. Please check the file and "
                        "try again."
                    )
                    return None
                return analyze_project(extracted)
            elif choice == "0":
                return None
            else:
                print("Please choose a valid option (0–2).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
            return None
        except Exception as e:
            print(f"[ERROR] {e}")


def saved_projects_menu() -> None:
    """
    Displays all saved projects from the default User_config_files directory
    and the legacy location.
    """
    while True:
        print("\n=== Saved Project Menu ===")

        try:
            # Always use default directory; list_saved_projects will also search
            # the legacy location so old analyses still appear.
            folder = Path(DEFAULT_SAVE_DIR).resolve()
            items = list_saved_projects(folder)

            if not items:
                print("[INFO] No saved projects")
                input("Press Enter to return to main menu...")
                return

            print(f"\nSaved analyses:\n")
            for i, p in enumerate(items, start=1):
                print(f"{i}) {p.name}")

            sel = input(
                "\nChoose a file to view (or press 0 to exit to main menu): "
            ).strip()
            if not sel or sel == "0":
                return

            try:
                idx = int(sel) - 1
                if idx < 0 or idx >= len(items):
                    print("Invalid selection.")
                    continue

                show_saved_summary(items[idx])
                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a number.")
                continue

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return


def delete_analysis_menu() -> None:
    """
    Menu for deleting saved project analyses from the default
    User_config_files/project_insights directory and the database.
    Also respects legacy files from the parent directory.
    """
    while True:
        print("\n=== Delete Analysis Menu ===")

        try:
            folder = Path(DEFAULT_SAVE_DIR).resolve()
            projects = list_saved_projects(folder)

            if not projects:
                print("[INFO] No saved projects.")
                input("Press Enter to return to main menu...")
                return

            print("\nSaved projects:\n")
            for i, p in enumerate(projects, start=1):
                print(f"{i}) {p.name}")

            sel = input(
                "\nEnter the number of the project to delete (or 0 to exit): "
            ).strip()
            if not sel or sel == "0":
                return

            try:
                sel_idx = int(sel) - 1
            except ValueError:
                print("[ERROR] Please enter a number.")
                continue

            if sel_idx < 0 or sel_idx >= len(projects):
                print("[ERROR] Selection out of range.")
                continue

            file_path = projects[sel_idx]
            filename = file_path.name

            # Confirm deletion
            confirm = input(
                f"Are you sure you want to delete '{filename}' from disk "
                f"and any related DB records? (y/n): "
            ).strip().lower()
            if not confirm.startswith("y"):
                print("[INFO] Deletion cancelled.")
                continue

            # Delete from database
            try:
                db_rows = get_saved_projects_from_db()
            except Exception as e:
                print(f"[WARNING] Could not query database: {e}")
                db_rows = []

            matching_rows = [row for row in db_rows if row[1] == filename]

            if not matching_rows:
                print(f"[INFO] No database records reference '{filename}'.")
            else:
                deleted_any = False
                for row in matching_rows:
                    row_id = row[0]
                    try:
                        if delete_from_database_by_id(row_id):
                            print(
                                f"[SUCCESS] Deleted DB record id={row_id} "
                                f"for '{filename}'."
                            )
                            deleted_any = True
                        else:
                            print(
                                f"[WARNING] Could not delete DB record id={row_id}."
                            )
                    except Exception as e:
                        print(
                            f"[WARNING] Error deleting DB record id={row_id}: {e}"
                        )

                if not deleted_any:
                    print("[INFO] No DB records were deleted.")

                try:
                    file_deleted = delete_file_from_disk(filename)
                except Exception as e:
                    print(
                        f"[WARNING] Unexpected error while attempting to delete "
                        f"file '{filename}': {e}"
                    )
                    file_deleted = False

                if file_deleted:
                    print(
                        f"[SUCCESS] Deleted '{filename}' from filesystem!"
                    )
                else:
                    if file_path.exists():
                        print(f"[INFO] File remains on disk at: {file_path}")
                    else:
                        print(f"[INFO] File not found on disk.")

            another = input("\nDelete another analysis? (y/n): ").strip().lower()
            if not another.startswith("y"):
                return

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return


def main() -> int:
    while True:
        print("\n=== Main Menu ===")
        print("1) Settings")
        print("2) Analyze project")
        print("3) Saved projects")
        print("4) Delete analysis")
        print("0) Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                settings_menu()
            elif choice == "2":
                analyze_project_menu()
            elif choice == "3":
                saved_projects_menu()
            elif choice == "4":
                delete_analysis_menu()
            elif choice == "0":
                print("Goodbye!")
                return 0
            else:
                print("Please choose a valid option (0-4).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    # --- Startup: ask for user consent before doing anything ---
    try:
        consent_manager = UserConsent()
        proceed = consent_manager.ask_for_consent()
        if not proceed:
            print("[EXIT] User declined consent. Exiting.")
            sys.exit(1)
        # Save consent into user's configuration for future runs
        try:
            data = ConfigLoader().load()
            configure_json = configuration_for_users(data)
            configure_json.save_with_consent(
                consent_manager.has_external_consent,
                consent_manager.has_data_consent,
            )
            configure_json.save_config()
        except Exception as e:
            print(f"[WARN] Failed to persist consent to configuration: {e}")
        # proceed to main program
        sys.exit(main())
    finally:
        try:
            if "conn" in globals() and conn:
                conn.close()
        except Exception:
            pass
