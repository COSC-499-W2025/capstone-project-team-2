"""
CLI menus for configuration, consent aware analysis, saved reports, and project insights.

Entrypoints here stitch together user facing flows:
- settings: configure consent and defaults
- analyze: ingest a directory or ZIP (with optional AI analysis when consented)
- saved/delete: review or remove persisted analyses
- AI portfolio/resume: regenerate AI driven summaries when external services are permitted
- insights: view chronological projects/skills, rankings, and top summaries from stored insights
"""

from pathlib import Path
import json

# Menu flows for the CLI, delegating to analysis, saved-project, and portfolio helpers.
from src.API.analysis_API import perform_analysis_API
from src.API.project_io_API import return_all_saved_projects
from src.cli.CLI_Interface_for_user_config import ConfigurationForUsersUI
from src.core.analysis_service import (
    analyze_project,
    extract_if_zip,
)
from src.core.app_context import runtimeAppContext
from src.reporting.portfolio import display_portfolio_and_generate_pdf
from src.storage.saved_projects import (
    delete_file_from_disk,
    find_saved_file_path,
    delete_from_database_by_name,
    get_saved_projects_from_db,
    list_saved_projects,
    show_saved_summary,
)
from src.config.project_thumbnails import ThumbnailManager
from src.cli.menu_insights import project_insights_menu
from src.reporting.project_insights import (
    list_project_insights,
    update_thumbnail_in_insights,
    remove_thumbnail_from_insights,
)
from src.reporting.representation_preferences import (
    load_preferences,
    save_preferences,
)

from src.config.user_startup_config import ConfigLoader
from src.reporting.Generate_AI_Resume import GenerateProjectResume, GenerateLocalResume
from src.reporting.resume_pdf_generator import SimpleResumeGenerator
from src.cli.document_generator_menu import document_generator_menu
from src.API.consent_API import *
from multi_project_handler import multi_project_handler
import os


def settings_menu() -> None:
    """
    Display the settings menu with options for user configuration and external services.

    Provides a submenu allowing users to:
    1. Modify user profile settings (name, email, role, etc.)
    2. Toggle external services (Google Gemini AI) on or off mid-session

    Args:
        None

    Returns:
        None: Returns when user selects option 0 to go back to main menu.
    """
    while True:
        print("\n=== Settings Menu ===")
        print("1) User Configuration")
        print("2) Toggle External Services")
        print("3) Manage Thumbnails")
        print("4) Representation Preferences")
        print("0) Back to Main Menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            try:
                cfg = get_config_dict()
                ConfigurationForUsersUI(cfg).run_configuration_cli()
            except HTTPException as e:
                print(e)
        elif choice == "2":
            toggle_external_services()
        elif choice == "3":
            thumbnail_management_menu()
        elif choice == "4":
            representation_preferences_menu()
        elif choice == "0":
            return
        else:
            print("Please choose a valid option (0-4).")


def representation_preferences_menu() -> None:
    """Simple CLI to edit how projects are displayed."""
    prefs = load_preferences()

    def _available_project_names() -> list[str]:
        try:
            return sorted({p.project_name for p in list_project_insights()})
        except Exception:
            return []

    def _validate_names(candidates: list[str], available: list[str]) -> tuple[list[str], list[str]]:
        valid = [c for c in candidates if c in available]
        missing = [c for c in candidates if c not in available]
        return valid, missing

    while True:
        available = _available_project_names()
        print("\n=== Representation Preferences ===")
        print(f"Current project order: {prefs.get('project_order') or 'not set'}")
        print(f"Showcase projects: {prefs.get('showcase_projects') or 'none'}")
        print(f"Highlight skills: {prefs.get('highlight_skills') or 'none'}")
        if available:
            print(f"Available projects: {', '.join(available)}")
        else:
            print("Available projects: none recorded yet")
        print("1) Set project order (comma-separated names)")
        print("2) Set showcase projects (comma-separated names)")
        print("3) Set highlight skills (comma-separated list)")
        print("4) Add/Update chronology override (project, ISO datetime)")
        print("5) Reset to defaults")
        print("0) Back")

        choice = input("Select an option: ").strip()
        if choice == "1":
            raw = input("Project order (e.g., Alpha,Beta,Gamma): ").strip()
            order = [p.strip() for p in raw.split(",") if p.strip()]
            valid, missing = _validate_names(order, available)
            prefs["project_order"] = valid
            if missing:
                print(f"[WARN] Ignored unknown projects: {', '.join(missing)}")
            save_preferences(prefs)
        elif choice == "2":
            raw = input("Showcase projects (comma-separated): ").strip()
            showcases = [p.strip() for p in raw.split(",") if p.strip()]
            valid, missing = _validate_names(showcases, available)
            prefs["showcase_projects"] = valid
            if missing:
                print(f"[WARN] Ignored unknown projects: {', '.join(missing)}")
            save_preferences(prefs)
        elif choice == "3":
            raw = input("Highlight skills (comma-separated): ").strip()
            prefs["highlight_skills"] = [s.strip() for s in raw.split(",") if s.strip()]
            save_preferences(prefs)
        elif choice == "4":
            proj = input("Project name to override: ").strip()
            ts = input("Analyzed datetime (ISO, e.g., 2025-01-01T00:00:00Z): ").strip()
            prefs.setdefault("chronology_corrections", {})[proj] = {"analyzed_at": ts}
            save_preferences(prefs)
        elif choice == "5":
            prefs = {
                "project_order": [],
                "chronology_corrections": {},
                "comparison_attributes": ["languages", "frameworks", "duration_estimate"],
                "highlight_skills": [],
                "showcase_projects": [],
            }
            save_preferences(prefs)
        elif choice == "0":
            return
        else:
            print("Please choose a valid option (0-5).")


def toggle_external_services() -> None:
    """
    Toggle external services on or off during the current session.

    Allows users to enable or disable external API services (Google Gemini AI)
    without restarting the application. Changes are applied immediately to the
    current session and persisted to the UserConfigs.json file for future sessions.

    When external services are disabled:
    - AI Resume Generator (option 6) will be blocked
    - Analysis will use local processing only
    - Local Resume Generator (option 7) remains available

    Args:
        None

    Returns:
        None: Returns when user selects option 0 or after toggling.

    Side Effects:
        - Modifies ctx.external_consent in-place
        - Saves updated consent to User_config_files/UserConfigs.json
    """
    current_status = "ENABLED" if runtimeAppContext.external_consent else "DISABLED"
    print(f"\n=== External Services Toggle ===")
    print(f"Current status: {current_status}")
    print("\nExternal services include:")
    print("  - Google Gemini AI (resume generation)")

    if runtimeAppContext.external_consent:
        print("\n1) Disable External Services")
    else:
        print("\n1) Enable External Services")
    print("0) Back")

    choice = input("\nSelect an option: ").strip()

    if choice == "1":
        runtimeAppContext.external_consent = not runtimeAppContext.external_consent
        new_status = "ENABLED" if runtimeAppContext.external_consent else "DISABLED"

        # Save to config file
        try:
            consent_object = PrivacyConsentRequest(data_consent=runtimeAppContext.data_consent, external_consent=runtimeAppContext.external_consent)
            update_privacy_consent(consent_object)
            print(f"\n[SUCCESS] External services are now {new_status}")
        except Exception as e:
            print(f"\n[WARNING] Setting changed for this session but failed to save: {e}")
            print(f"External services are now {new_status}")
    elif choice == "0":
        return
    else:
        print("\n[INFO] Invalid option. No changes made.")
        
def prompt_thumbnail_upload(project_id: str, project_name: str) -> bool:
    """
    Prompt the user to upload a thumbnail for a project after analysis.

    Args:
        project_id: UUID for storing the thumbnail (used as file identifier).
        project_name: Human-readable project name (used for display messages).
        ctx: Application context containing storage paths.

    Returns:
        bool: True if thumbnail was successfully added, False otherwise.
    """
    print(f"\n=== Project Thumbnail ===")
    add_thumbnail = input(f"Would you like to add a thumbnail image for '{project_name}'? (y/n): ").strip().lower()
    
    if add_thumbnail != 'y':
        print("[INFO] You can add or update thumbnails later in Settings > Manage Project Thumbnails.")
        return False
    
    # Initialize thumbnail manager
    thumbnail_dir = Path(runtimeAppContext.legacy_save_dir) / "thumbnails"
    thumbnail_manager = ThumbnailManager(storage_dir=thumbnail_dir)
    
    max_attempts = 3
    attempts = 0
    
    while attempts < max_attempts:
        image_path_str = input("Enter path to thumbnail image (or 'cancel' to skip): ").strip()
        
        if image_path_str.lower() == 'cancel':
            print("[INFO] Thumbnail upload cancelled. You can add it later in Settings.")
            return False
        
        image_path = Path(image_path_str).expanduser().resolve()
        
        if not image_path.exists():
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"[ERROR] File not found: {image_path}")
                print(f"        {remaining} attempt(s) remaining.")
            continue
        
        # Validate and add thumbnail
        is_valid, error = thumbnail_manager.validate_image(image_path)
        if not is_valid:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"[ERROR] {error}")
                print(f"        {remaining} attempt(s) remaining.")
            continue
        
        # Add the thumbnail using project_id (UUID) as identifier
        success, error, thumb_path = thumbnail_manager.add_thumbnail(
            project_id=project_id,
            image_path=image_path,
            resize=True
        )
        
        if success:
            print(f"[SUCCESS] Thumbnail added for '{project_name}'")
            print(f"          Saved to: {thumb_path}")
            
            # Update project_insights.json with thumbnail info
            storage_path = Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"
            update_thumbnail_in_insights(project_id, thumb_path, storage_path)
            
            return True
        else:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"[ERROR] {error}")
                print(f"        {remaining} attempt(s) remaining.")
    
    print("[INFO] Maximum attempts reached. You can add a thumbnail later in Settings.")
    return False

def analyze_project_menu() -> None:
    """
    Ask user if their project is in a directory or zip file and analyze it.
    
    Supports analysis of Python, Java, C, and JavaScript projects. When external AI is
    disabled, the system will automatically run OOP analysis to detect classes, inheritance,
    encapsulation, and other object-oriented design patterns across all supported languages.

    Args:
        None

    Returns:
        None
    """
    while True:
        print("\n=== Analyze Project Menu ===")
        print("\nChoose input type:")
        print("  1) Directory")
        print("  2) ZIP file")
        print("  3) Multi-file upload")
        print("  0) Exit to Main Menu")

        choice = input("Select an option: ").strip()

        use_ai = False
        if runtimeAppContext.external_consent == True:
            use_ai = input("Add AI analysis? (y/n): ").strip().lower() == 'y'

        try:
            project_name = None
            if choice == "1":
                dir_path = input_path("Enter path to project directory: ")
                runtimeAppContext.currently_uploaded_file = dir_path
                status = perform_analysis_API(use_ai=use_ai)
            elif choice == "2":
                zip_path = input_path("Enter path to ZIP: ")
                if not zip_path:
                    print("[ERROR] ZIP path required.")
                    continue
                runtimeAppContext.currently_uploaded_file = zip_path
                status = perform_analysis_API(use_ai=use_ai)
            elif choice == "3":
                paths = []
                print("Enter project paths one by one (directory or zip). Empty line when done:")
                while True:
                    p = input_path("Path (or blank to finish): ")
                    if not p:
                        break
                    paths.append(p)

                    if paths:
                        multi_project_handler.multi_project_runner(paths, use_ai=use_ai)
                        return
            elif choice == "0":
                return
            else:
                print("Please choose a valid option (0–3).")
                continue
                
            if (status):
                print(status["status"])
            

            # After successful analysis, prompt for thumbnail upload
            if project_name:
                # Get the UUID from the newly created insight
                storage_path = Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"
                insights = list_project_insights(storage_path=storage_path)
                
                # Find the most recent insight matching this project name
                matching_insight = None
                for insight in reversed(insights):  # Most recent first
                    if insight.project_name == project_name:
                        matching_insight = insight
                        break
                
                if matching_insight:
                    prompt_thumbnail_upload(
                        project_id=matching_insight.id,
                        project_name=project_name
                    )
                else:
                    # Fallback if insight not found (shouldn't happen normally)
                    print("[WARNING] Could not find project insight. Skipping thumbnail prompt.")
            
            return
            
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
            return
        except Exception as e:
            raise
        
def saved_projects_menu() -> None:
    """
    Display all saved projects from the configured directory and legacy location.

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        None
    """
    while True:
        print("\n=== Saved Project Menu ===")

        try:
            items = return_all_saved_projects()

            if not items:
                print("[INFO] No saved projects")
                input("Press Enter to return to main menu...")
                return

            print(f"\nSaved analyses:\n")
            for i, p in enumerate(items, start=1):
                print(f"{i}) {p}")

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
    Menu for deleting saved project analyses from disk and the database.

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        None
    """
    while True:
        print("\n=== Delete Analysis Menu ===")

        try:
            projects = return_all_saved_projects()

            if not projects:
                print("[INFO] No saved projects.")
                input("Press Enter to return to main menu...")
                return

            print("\nSaved projects:\n")
            for i, p in enumerate(projects, start=1):
                print(f"{i}) {p}")

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

            filename = projects[sel_idx]

            confirm = input(
                f"Are you sure you want to delete '{filename}' from disk "
                f"and any related DB records? (y/n): "
            ).strip().lower()
            if not confirm.startswith("y"):
                print("[INFO] Deletion cancelled.")
                continue

            # Delete from database first (Pname is the filename without .json)
            full_filename = f"{filename}.json"
            deleted_from_db = delete_from_database_by_name(full_filename)
            if deleted_from_db:
                print(f"[INFO] Deleted '{full_filename}' from database.")

            # Delete from disk
            candidate_before = find_saved_file_path(full_filename)
            if delete_file_from_disk(full_filename):
                deleted_path = (
                    str(candidate_before)
                    if candidate_before is not None
                    else f"(resolved from configured save directories)"
                )
                print(f"[SUCCESS] Deleted '{full_filename}' from disk at: {deleted_path}")
            else:
                base_dir = Path(runtimeAppContext.default_save_dir).expanduser().resolve()
                primary = base_dir / full_filename
                legacy = base_dir.parent / full_filename
                if not deleted_from_db:
                    print(
                        f"[WARNING] Could not delete '{full_filename}'. "
                        f"Checked: '{primary}' and '{legacy}'."
                    )
                else:
                    print(
                        f"[INFO] No local file deleted for '{full_filename}'. "
                        f"Checked: '{primary}' and '{legacy}'."
                    )

            another = input("\nDelete another analysis? (y/n): ").strip().lower()
            if not another.startswith("y"):
                return

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return

def main_menu() -> int:
    """
    Top-level navigation loop for the CLI.

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        int: Exit code (0 on normal exit). Includes options for settings, analysis,
             saved/deletion flows, portfolio/resume generation, and insights viewing.
    """
    while True:
        print("\n=== Main Menu ===")
        print("1) Settings")
        print("2) Analyze project")
        print("3) Saved projects")
        print("4) Delete analysis")
        print("5) Document Generator (Resume & Portfolio)")
        print("6) Project insights")
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
            elif choice == "5":
                document_generator_menu()
            elif choice == "6":
                project_insights_menu()
            elif choice == "0":
                print("Goodbye!")
                return 0
            else:
                print("Please choose a valid option (0-6).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
        except Exception as e:
            raise
    
def thumbnail_management_menu() -> None:
    """
    Interactive menu for managing project thumbnails.
    
    Args:
        None
    """
    storage_path = Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"
    thumbnail_dir = Path(runtimeAppContext.legacy_save_dir) / "thumbnails"
    thumbnail_manager = ThumbnailManager(storage_dir=thumbnail_dir)
    
    if not storage_path.exists():
        print("[INFO] Initializing project insights from saved analyses...")
        _initialize_insights_from_saved_files(storage_path)
    
    while True:
        print("\n=== Thumbnail Management ===")
        print("1) Add/Update thumbnail for a project")
        print("2) Remove thumbnail from a project")
        print("0) Back to Main Menu")
        
        choice = input("\nSelect an option: ").strip()
        
        try:
            if choice == "1":
                _add_thumbnail_workflow(storage_path, thumbnail_manager)
            elif choice == "2":
                _remove_thumbnail_workflow(storage_path, thumbnail_manager)
            elif choice == "0":
                return
            else:
                print("[ERROR] Invalid option. Please choose 0-2.")
        
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to thumbnail menu...")
            continue
        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to continue...")

def _remove_thumbnail_workflow(
    storage_path: Path,
    thumbnail_manager: ThumbnailManager
) -> None:
    """Guide user through removing a thumbnail from a project."""
    insights = list_project_insights(storage_path=storage_path)
    
    # Check both JSON data and filesystem for thumbnails
    projects_with_thumbnails = []
    for insight in insights:
        has_in_json = insight.thumbnail and insight.thumbnail.get("exists")
        # Check filesystem with both UUID and project_name
        thumb_path_by_id = thumbnail_manager.get_thumbnail_path(insight.id)
        thumb_path_by_name = thumbnail_manager.get_thumbnail_path(insight.project_name)
        thumb_path = thumb_path_by_id or thumb_path_by_name
        if has_in_json or thumb_path:
            projects_with_thumbnails.append((insight, thumb_path))
    
    if not projects_with_thumbnails:
        print("\n[INFO] No projects have thumbnails to remove.")
        input("Press Enter to continue...")
        return
    
    print("\n=== Projects with Thumbnails ===\n")
    for i, (insight, thumb_path) in enumerate(projects_with_thumbnails, start=1):
        print(f"{i}) {insight.project_name}")
        if thumb_path:
            print(f"    Thumbnail: {thumb_path.name}")
        else:
            thumb_info = insight.thumbnail or {}
            thumb_name = Path(thumb_info.get("path", "unknown")).name if thumb_info.get("path") else "unknown"
            print(f"    Thumbnail: {thumb_name}")
        print()
    
    try:
        selection = input("Select a project number (or 0 to cancel): ").strip()
        if selection == "0":
            return
        
        idx = int(selection) - 1
        if idx < 0 or idx >= len(projects_with_thumbnails):
            print("[ERROR] Invalid selection.")
            input("Press Enter to continue...")
            return
        
        # Unpack the tuple to get the insight object
        selected_insight, _ = projects_with_thumbnails[idx]
        
    except ValueError:
        print("[ERROR] Please enter a valid number.")
        input("Press Enter to continue...")
        return
    
    confirm = input(
        f"\nAre you sure you want to remove the thumbnail for '{selected_insight.project_name}'? (y/n): "
    ).strip().lower()
    
    if confirm == 'y':
        # Try to delete using UUID first, then project_name
        deleted = thumbnail_manager.delete_thumbnail(selected_insight.id)
        if not deleted:
            deleted = thumbnail_manager.delete_thumbnail(selected_insight.project_name)
        
        if deleted:
            # Update project_insights.json
            remove_thumbnail_from_insights(selected_insight.id, storage_path)
            print(f"[SUCCESS] Thumbnail removed for '{selected_insight.project_name}'")
        else:
            print("[ERROR] Failed to remove thumbnail from filesystem.")
    else:
        print("[INFO] Cancelled.")
    
    input("\nPress Enter to continue...")
    
def _initialize_insights_from_saved_files(storage_path: Path) -> None:
    """
    Create project_insights.json from individual saved analysis files.
    This is called when project_insights.json doesn't exist but we have saved analyses.
    """
    from src.reporting.project_insights import record_project_insight
    
    folder = Path(runtimeAppContext.default_save_dir).resolve()
    saved_files = list_saved_projects(folder)
    
    if not saved_files:
        print("[INFO] No saved analyses found.")
        return
    
    count = 0
    for file_path in saved_files:
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            
            # Extract contributors if available
            contributors = data.get("contributors") or {}
            
            # Record the insight (this will create/append to project_insights.json)
            record_project_insight(
                data,
                storage_path=storage_path,
                contributors=contributors
            )
            count += 1
        except Exception as e:
            print(f"[WARNING] Couldn't import {file_path.name}: {e}")
    
    if count > 0:
        print(f"[SUCCESS] Initialized {count} project(s) into insights log.")

def _add_thumbnail_workflow(
    storage_path: Path,
    thumbnail_manager: ThumbnailManager
) -> None:
    """Guide user through adding a thumbnail to a project."""
    # Use list_project_insights to get UUIDs
    insights = list_project_insights(storage_path=storage_path)
    
    if not insights:
        print("[INFO] No projects found. Analyze a project first.")
        input("Press Enter to continue...")
        return
    
    print("\n=== Available Projects ===\n")
    for i, insight in enumerate(insights, start=1):
        # Check if thumbnail exists in the insight data OR on disk
        has_thumbnail_in_json = insight.thumbnail is not None and insight.thumbnail.get("exists")
        # Also check filesystem using both UUID and project_name as potential IDs
        has_thumbnail_on_disk = (
            thumbnail_manager.get_thumbnail_path(insight.id) is not None or
            thumbnail_manager.get_thumbnail_path(insight.project_name) is not None
        )
        has_thumbnail = has_thumbnail_in_json or has_thumbnail_on_disk
        thumbnail_status = "[YES]" if has_thumbnail else "[NO]"
        print(f"{i}) {insight.project_name} {thumbnail_status}")
    

    try:
        selection = input("\nSelect a project number (or 0 to cancel): ").strip()
        if selection == "0":
            return
        
        idx = int(selection) - 1
        if idx < 0 or idx >= len(insights):
            print("[ERROR] Invalid selection.")
            input("Press Enter to continue...")
            return
        
        selected_insight = insights[idx]
        
    except ValueError:
        print("[ERROR] Please enter a valid number.")
        input("Press Enter to continue...")
        return
    
    image_path_str = input("\nEnter path to thumbnail image: ").strip()
    if not image_path_str:
        print("[INFO] Cancelled.")
        input("Press Enter to continue...")
        return
    
    image_path = Path(image_path_str).expanduser().resolve()
    
    resize_input = input("Resize to standard thumbnail size (400x300)? (y/n) [y]: ").strip().lower()
    resize = resize_input != 'n'
    
    print("\n[INFO] Processing thumbnail...")
    
    # Use project UUID as thumbnail ID
    success, error, thumb_path = thumbnail_manager.add_thumbnail(
        selected_insight.id,  # Use UUID from insights
        image_path,
        resize=resize
    )
    
    if success:
        # Update project_insights.json with thumbnail info
        update_success = update_thumbnail_in_insights(
            selected_insight.id,
            thumb_path,
            storage_path
        )
        
        if update_success:
            print(f"[SUCCESS] Thumbnail added for '{selected_insight.project_name}'")
            print(f"[INFO] Saved to: {thumb_path}")
            print(f"[INFO] Updated project_insights.json")
        else:
            print(f"[WARNING] Thumbnail saved but could not update project_insights.json")
    else:
        print(f"[ERROR] Failed to add thumbnail: {error}")
    
    input("\nPress Enter to continue...")

def input_path(prompt: str, allow_blank: bool = False) -> Path | None:
    """
    Prompt user for a path until it exists.

    Args:
        prompt (str): Message shown to the user.
        allow_blank (bool): If True, empty input returns None.

    Returns:
        Path: Resolved path or None when blank is allowed.
    """

    while True:
        p = input(prompt).strip()
        if not p and allow_blank:
            return None
        path = Path(p).expanduser().resolve()
        if path.exists():
            return path
        print(f"[ERROR] Path not found: {path}")
