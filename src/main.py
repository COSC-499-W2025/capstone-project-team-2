# import psycopg2   for Docker
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Local module Imports
from src.CLI_Interface_for_user_config import ConfigurationForUsersUI
from src.Configuration import configuration_for_users
from src.data_extraction import FileMetadataExtractor
from src.extraction import extractInfo
from src.project_duration_estimation import Project_Duration_Estimator
from src.project_skill_insights import identify_skills
from src.project_stack_detection import detect_project_stack
from src.project_type_detection import detect_project_type
from src.resume_item_generator import generate_resume_item
from src.user_startup_config import ConfigLoader
from src.file_data_saving import SaveFileAnalysisAsJSON

# Docker setup
# conn = psycopg2.connect(
#     host="localhost",
#     port=5432,
#     database="appdb",
#     user="appuser",
#     password="apppassword"
# )

''' if you are to run a test for this code run: 

docker-compose up db 

in your terminal, output should look something like the following

[+] Running 2/2
 ✔ Network capstone-project-team-2_app_network  Created                                                                                                                                                                           0.2s 
 ✔ Container app_database                       Created                                                                                                                                                                           0.3s 
Attaching to app_database
app_database  |
app_database  | PostgreSQL Database directory appears to contain a database; Skipping initialization
app_database  |                                                                                                                                                                                                                        
app_database  | 2025-11-01 23:21:45.584 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
app_database  | 2025-11-01 23:21:45.586 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
app_database  | 2025-11-01 23:21:45.586 UTC [1] LOG:  listening on IPv6 address "::", port 5432
app_database  | 2025-11-01 23:21:45.600 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
app_database  | 2025-11-01 23:21:45.625 UTC [29] LOG:  database system was shut down at 2025-11-01 22:21:04 UTC
app_database  | 2025-11-01 23:21:45.656 UTC [1] LOG:  database system is ready to accept connections
app_database  | 2025-11-01 23:26:45.702 UTC [27] LOG:  checkpoint starting: time
app_database  | 2025-11-01 23:26:45.761 UTC [27] LOG:  checkpoint complete: wrote 3 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.014 s, sync=0.006 s, total=0.060 s; sync files=2, longest=0.003 s, average=0.003 s; distance=0 kB, estimate=0 kB

once we create the data base and wish to set up actual credentials

update the python code as well as lines 28-33 and run:

docker-compose down -v  # -v removes old data
docker-compose up db
 '''

DEFAULT_SAVE_DIR = Path("User_config_files")


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
    returns .../temp folder
    """

    out = extractInfo(str(zip_path)).runExtraction()
    return Path(out)
 
def estimate_duration(hierarchy: Dict[str, Any]) -> str:

    """
    Wraps project_duration_estimation.get_duration() 
    If successful returns duration estimate
    On error returns "unavailable"
    """
    try:
        estimate = Project_Duration_Estimator(hierarchy)
        return str(estimate.get_duration())
    except Exception as e:
        return f"unavailable ({e})"

def analyze_project(root: Path) -> None:
    """ 
    Takes in the path for the a project folder
    Returns an print analysis of the file including the file hierarchy, duration of the project,
    summary, type, language, framework etc.
    Can also output a json file for saving
    """

    print(f"\n[INFO] Analyzing: {root}\n")

    hierarchy = FileMetadataExtractor(root).file_hierarchy()
    duration = estimate_duration(hierarchy)
    resume = generate_resume_item(root, project_name=root.name)

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
    }

    print("[SUMMARY]")
    print(f"  Type       : {resume.project_type} (mode={resume.detection_mode})")
    print(f"  Languages  : {', '.join(resume.languages) or '—'}")
    print(f"  Frameworks : {', '.join(resume.frameworks) or '—'}")
    print(f"  Skills     : {', '.join(resume.skills) or '—'}")
    print(f"  Duration   : {duration}\n")

    export_json(root.name, analysis)

def export_json(project_name: str, analysis: Dict[str, Any]) -> None:
    """
    saves an analyzed project as a json file
    TODO: once safe data feature is implemented fix this so it actually saves somewhere
    """

    ans = (input("Save JSON report? (y/n) [n]: ").strip().lower() or "n")
    if ans.startswith("y"):
        out_dir_str = input(f"Output directory [{DEFAULT_SAVE_DIR}]: ").strip()
        out_dir = Path(out_dir_str or DEFAULT_SAVE_DIR).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        SaveFileAnalysisAsJSON.saveAnalysis(project_name, analysis, str(out_dir))
        print(f"[INFO] Saved → {out_dir / (project_name + '.json')}")

def list_saved_projects(folder: Path) -> list[Path]:
    """
    Takes in a folder and returns a list of the files that folder
    TODO: Once we have the save feature finished, this should automatically look where they get saved
    and/or should open the users file structure so they can select a folder from their local machine
    """

    if not folder.exists():
        return []
    return sorted(folder.glob("*.json"))

def show_saved_summary(path: Path) -> None:
    """
    Displays the summary of the saved file
    Takes in path to the file
    outputs print summary
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {path.name}: {e}")
        return

    analysis = data if isinstance(data, dict) else {}
    if "analysis" in analysis and isinstance(analysis["analysis"], dict):
        analysis = analysis["analysis"]

    pt = analysis.get("resume_item", {}).get("project_type") or analysis.get("project_type", {}).get("project_type", "—")
    mode = analysis.get("resume_item", {}).get("detection_mode") or analysis.get("project_type", {}).get("mode", "—")
    stack = analysis.get("resume_item", {}) or {}
    langs = stack.get("languages") or analysis.get("stack", {}).get("languages", [])
    frws  = stack.get("frameworks") or analysis.get("stack", {}).get("frameworks", [])
    skills = stack.get("skills") or analysis.get("skills", [])
    duration = analysis.get("duration_estimate", "—")
    summary = (analysis.get("resume_item", {}) or {}).get("summary", "—")

    print(f"\n== {path.name} ==")
    print(f"Project root : {analysis.get('project_root', '—')}")
    print(f"Type         : {pt} (mode={mode})")
    print(f"Languages    : {', '.join(langs) or '—'}")
    print(f"Frameworks   : {', '.join(frws) or '—'}")
    print(f"Skills       : {', '.join(skills) or '—'}")
    print(f"Duration     : {duration}")
    if summary and summary != '—':
        print(f"Résumé line  : {summary}")
    print()

# ---------- Menus ----------
def settings_menu() -> None:
    cfg = ConfigLoader().load()
    ConfigurationForUsersUI(cfg).run_configuration_cli()

def analyze_project_menu() -> Path:
    """
    asks user if their project is in a directory or zip file
    if zip project uses extract_if_zip to send for extraction
    if directory, will send for directory processing, but this part isn't dont yet
    TODO: once directory processing code is finished change else function to send directory path for processing
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
                return dir
            elif choice == "2":
                zip = _input_path("Enter path to ZIP: ")
                return analyze_project(extract_if_zip(zip))
            elif choice == "0":
                return
            else:
                print("Please choose a valid option (0–2).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
            return none
        except Exception as e:
            print(f"[ERROR] {e}")

def previous_projects_menu() -> None:
    while True:
        print("\n=== Previous Project Menu ===")
        folder_str = input(
            f"Enter folder to scan for saved analyses [{DEFAULT_SAVE_DIR}] or 0 to exit to main menu: "
        ).strip()

        if folder_str == "0":  
            return

        folder = Path(folder_str or DEFAULT_SAVE_DIR).expanduser().resolve()
        items = list_saved_projects(folder)
        if not items:
            print(f"[INFO] No saved projects in {folder}")
            return

        print("\nSaved analyses:")
        for i, p in enumerate(items, start=1):
            print(f"{i}) {p.name}")

        sel = input("Choose a file to view (or press 0 to exit to main menu): ").strip()
        if not sel:
            return
        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(items):
                print("Invalid selection.")
                return
            show_saved_summary(items[idx])
            # after showing, return to main menu
            return
        except ValueError:
            print("Please enter a number.")
            return
                    
def main() -> int:
    while True:
        print("\n=== Main Menu ===")
        print("1) Settings")
        print("2) Analyze project")
        print("3) Saved projects")
        print("0) Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                settings_menu()
            elif choice == "2":
                analyze_project_menu()
            elif choice == "3":
                previous_projects_menu()
            elif choice == "0":
                print("Goodbye!")
                return 0
            else:
                print("Please choose a valid option (0–3).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    sys.exit(main())