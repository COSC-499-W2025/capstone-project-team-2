#import psycopg2
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Import Local modules

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

# ----------------------------- Helpers ----------------------------------------
DEFAULT_SAVE_DIR = Path("User_config_files")

def _input_path(prompt: str, allow_blank: bool = False) -> Optional[Path]:
    while True:
        p = input(prompt).strip()
        if not p and allow_blank:
            return None
        path = Path(p).expanduser().resolve()
        if path.exists():
            return path
        print(f"[ERROR] Path not found: {path}")

def _extract_if_zip(zip_path: Path) -> Path:
    """
    Uses your extractInfo to unpack a zip to ./temp and returns that directory.
    """
    runner = extractInfo(str(zip_path))
    err = runner.verifyZIP()
    if err is not None:
        raise ValueError(err)
    runner.extractFiles()
    return Path.cwd() / "temp"

def _choose_project_root() -> Path:
    print("\nChoose input type:")
    print("  1) Directory")
    print("  2) ZIP file")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "2":
        zp = _input_path("Enter path to ZIP: ")
        return _extract_if_zip(zp)  # type: ignore[arg-type]
    else:
        dp = _input_path("Enter path to project directory: ")
        return dp  # type: ignore[return-value]

def _run_hierarchy(root: Path) -> Dict[str, Any]:
    return FileMetadataExtractor(root).file_hierarchy()

def _estimate_duration(hierarchy: Dict[str, Any]) -> str:
    try:
        est = Project_Duration_Estimator(hierarchy)
        return str(est.get_duration())
    except Exception as e:
        return f"unavailable ({e})"

def _run_full_analysis(root: Path) -> Dict[str, Any]:
    hierarchy = _run_hierarchy(root)
    duration = _estimate_duration(hierarchy)
    proj_type = detect_project_type(root)
    stack = detect_project_stack(root)
    skills = identify_skills(root)
    resume = generate_resume_item(root, project_name=root.name)

    resume_dict = {
        "project_name": resume.project_name,
        "summary": resume.summary,
        "highlights": resume.highlights,
        "project_type": resume.project_type,
        "detection_mode": resume.detection_mode,
        "languages": resume.languages,
        "frameworks": resume.frameworks,
        "skills": resume.skills,
        "framework_sources": resume.framework_sources,
    }

    return {
        "project_root": str(root),
        "hierarchy": hierarchy,
        "duration_estimate": duration,
        "project_type": proj_type,
        "stack": stack,
        "skills": skills,
        "resume_item": resume_dict,
    }

def _maybe_export_json(project_name: str, analysis: Dict[str, Any]) -> None:
    ans = (input("Save JSON report? (y/n) [n]: ").strip().lower() or "n")
    if ans.startswith("y"):
        out_dir_str = input(f"Output directory [{DEFAULT_SAVE_DIR}]: ").strip()
        out_dir = Path(out_dir_str or DEFAULT_SAVE_DIR).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        SaveFileAnalysisAsJSON.saveAnalysis(project_name, analysis, str(out_dir))
        print(f"[INFO] Saved → {out_dir / (project_name + '.json')}")

def _list_saved_projects(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(folder.glob("*.json"))

def _show_saved_summary(path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {path.name}: {e}")
        return

    # handle either full analysis dict or nested under a key
    analysis = data if isinstance(data, dict) else {}
    # If someone saved a wrapper like {"analysis": {...}}
    if "analysis" in analysis and isinstance(analysis["analysis"], dict):
        analysis = analysis["analysis"]

    pt = analysis.get("project_type", {})
    st = analysis.get("stack", {})
    skills = analysis.get("skills", [])
    duration = analysis.get("duration_estimate", "—")
    resume = analysis.get("resume_item", {})

    print(f"\n== {path.name} ==")
    print(f"Project root : {analysis.get('project_root', '—')}")
    print(f"Type         : {pt.get('project_type', '—')} (mode={pt.get('mode', '—')})")
    print(f"Languages    : {', '.join(st.get('languages', [])) or '—'}")
    print(f"Frameworks   : {', '.join(st.get('frameworks', [])) or '—'}")
    print(f"Skills       : {', '.join(skills) or '—'}")
    print(f"Duration     : {duration}")
    if resume:
        print(f"Résumé line  : {resume.get('summary', '—')}")
    print()

# ----------------------------- Menu Actions -----------------------------------
def action_settings_menu() -> None:
    cfg = ConfigLoader().load()
    ConfigurationForUsersUI(cfg).run_configuration_cli()

def action_analyze_project() -> None:
    root = _choose_project_root()
    print(f"\n[INFO] Analyzing: {root}\n")
    analysis = _run_full_analysis(root)

    # brief summary
    pt = analysis.get("project_type", {})
    st = analysis.get("stack", {})
    print("[SUMMARY]")
    print(f"  Type       : {pt.get('project_type')} (mode={pt.get('mode')})")
    print(f"  Languages  : {', '.join(st.get('languages', [])) or '—'}")
    print(f"  Frameworks : {', '.join(st.get('frameworks', [])) or '—'}")
    print(f"  Skills     : {', '.join(analysis.get('skills', [])) or '—'}")
    print(f"  Duration   : {analysis.get('duration_estimate')}\n")

    _maybe_export_json(root.name, analysis)

def action_previous_projects() -> None:
    folder_str = input(f"Folder to scan for saved analyses [{DEFAULT_SAVE_DIR}]: ").strip()
    folder = Path(folder_str or DEFAULT_SAVE_DIR).expanduser().resolve()
    items = _list_saved_projects(folder)
    if not items:
        print(f"[INFO] No saved project JSON files in {folder}")
        return

    print("\nSaved analyses:")
    for i, p in enumerate(items, start=1):
        print(f"{i}) {p.name}")
    choice = input("Choose a file to view (or press Enter to cancel): ").strip()
    if not choice:
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(items):
            print("Invalid selection.")
            return
        _show_saved_summary(items[idx])
    except ValueError:
        print("Please enter a number.")

# ----------------------------- Main Menu Loop ---------------------------------
def main() -> int:
    while True:
        print("\n=== Main Menu ===")
        print("1) Settings menu")
        print("2) Analyze project")
        print("3) Previous projects")
        print("0) Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                action_settings_menu()
            elif choice == "2":
                action_analyze_project()
            elif choice == "3":
                action_previous_projects()
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