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
from src.cli.CLI_Interface_for_user_config import ConfigurationForUsersUI
from src.core.analysis_service import (
    analyze_project,
    extract_if_zip,
)
from src.core.app_context import AppContext
from src.reporting.portfolio import display_portfolio_and_generate_pdf
from src.storage.saved_projects import (
    delete_file_from_disk,
    delete_from_database_by_id,
    get_saved_projects_from_db,
    list_saved_projects,
    show_saved_summary,
)
from src.config.project_thumbnails import ThumbnailManager
from src.cli.menu_insights import project_insights_menu
from src.reporting.project_insights import (
    list_project_insights,
    update_thumbnail_in_insights,
    record_project_insight,
    remove_thumbnail_from_insights,
)

from src.config.user_startup_config import ConfigLoader
from src.config.Configuration import configuration_for_users
from src.reporting.Generate_AI_Resume import GenerateProjectResume, GenerateLocalResume
from src.reporting.resume_pdf_generator import SimpleResumeGenerator
from src.cli.document_generator_menu import document_generator_menu
import os


def settings_menu(ctx: AppContext) -> None:
    """
    Display the settings menu with options for user configuration and external services.

    Provides a submenu allowing users to:
    1. Modify user profile settings (name, email, role, etc.)
    2. Toggle external services (Google Gemini AI) on or off mid-session

    Args:
        ctx (AppContext): Shared application context containing database connection,
            storage paths, and the current external_consent setting.

    Returns:
        None: Returns when user selects option 0 to go back to main menu.
    """
    while True:
        print("\n=== Settings Menu ===")
        print("1) User Configuration")
        print("2) Toggle External Services")
        print("3) Manage Thumbnails")
        print("0) Back to Main Menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            cfg = ConfigLoader().load()
            ConfigurationForUsersUI(cfg).run_configuration_cli()
        elif choice == "2":
            toggle_external_services(ctx)
        elif choice == "3":
            thumbnail_management_menu(ctx)
        elif choice == "0":
            return
        else:
            print("Please choose a valid option (0-3).")


def toggle_external_services(ctx: AppContext) -> None:
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
        ctx (AppContext): Shared application context. The external_consent
            attribute will be modified in-place when toggled.

    Returns:
        None: Returns when user selects option 0 or after toggling.

    Side Effects:
        - Modifies ctx.external_consent in-place
        - Saves updated consent to User_config_files/UserConfigs.json
    """
    current_status = "ENABLED" if ctx.external_consent else "DISABLED"
    print(f"\n=== External Services Toggle ===")
    print(f"Current status: {current_status}")
    print("\nExternal services include:")
    print("  - Google Gemini AI (resume generation)")

    if ctx.external_consent:
        print("\n1) Disable External Services")
    else:
        print("\n1) Enable External Services")
    print("0) Back")

    choice = input("\nSelect an option: ").strip()

    if choice == "1":
        ctx.external_consent = not ctx.external_consent
        new_status = "ENABLED" if ctx.external_consent else "DISABLED"

        # Save to config file
        try:
            cfg = ConfigLoader().load()
            configure_json = configuration_for_users(cfg)
            # Preserve data consent, update external consent
            data_consent = True  # Data consent must be true if app is running
            configure_json.save_with_consent(ctx.external_consent, data_consent)
            configure_json.save_config()
            print(f"\n[SUCCESS] External services are now {new_status}")
        except Exception as e:
            print(f"\n[WARNING] Setting changed for this session but failed to save: {e}")
            print(f"External services are now {new_status}")
    elif choice == "0":
        return
    else:
        print("\n[INFO] Invalid option. No changes made.")
        
def prompt_thumbnail_upload(project_id: str, project_name: str, ctx: AppContext) -> bool:
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
    thumbnail_dir = Path(ctx.legacy_save_dir) / "thumbnails"
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
            storage_path = Path(ctx.legacy_save_dir) / "project_insights.json"
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

def analyze_project_menu(ctx: AppContext) -> None:
    """
    Ask user if their project is in a directory or zip file and analyze it.
    
    Supports analysis of Python, Java, C, and JavaScript projects. When external AI is
    disabled, the system will automatically run OOP analysis to detect classes, inheritance,
    encapsulation, and other object-oriented design patterns across all supported languages.

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        None
    """
    while True:
        print("\n=== Analyze Project Menu ===")
        print("\nChoose input type:")

        print("  1) Directory")
        print("  2) ZIP file")
        print("  0) Exit to Main Menu")

        choice = input("Select an option: ").strip()

        use_ai = False
        if ctx.external_consent == True:
            use_ai = input("Add AI analysis? (y/n): ").strip().lower() == 'y'

        try:
            project_name = None
            if choice == "1":
                dir_path = input_path("Enter path to project directory: ")
                if dir_path:
                    analyze_project(dir_path, use_ai_analysis=use_ai)
            elif choice == "2":
                zip_path = input_path("Enter path to ZIP: ")
                if not zip_path:
                    print("[ERROR] ZIP path required.")
                    continue
                extracted = extract_if_zip(zip_path)
                if not extracted:
                    print(
                        "[ERROR] Could not extract ZIP. Please check the file and "
                        "try again."
                    )
                    return None
                project_name = zip_path.stem
                
                analyze_project(
                    extracted,
                    use_ai_analysis=use_ai
                )
            elif choice == "0":
                return None
            else:
                print("Please choose a valid option (0–2).")
                continue
            
            print("Analysis successful, saved to saved projects.")

            # After successful analysis, prompt for thumbnail upload
            if project_name:
                # Get the UUID from the newly created insight
                storage_path = Path(ctx.legacy_save_dir) / "project_insights.json"
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
                        project_name=project_name,
                        ctx=ctx
                    )
                else:
                    # Fallback if insight not found (shouldn't happen normally)
                    print("[WARNING] Could not find project insight. Skipping thumbnail prompt.")
            
            return
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
            return None
        except Exception as e:
            print(f"[ERROR] {e}")


def saved_projects_menu(ctx: AppContext) -> None:
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
            folder = Path(ctx.default_save_dir).resolve()
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


def delete_analysis_menu(ctx: AppContext) -> None:
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
            folder = Path(ctx.default_save_dir).resolve()
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

            confirm = input(
                f"Are you sure you want to delete '{filename}' from disk "
                f"and any related DB records? (y/n): "
            ).strip().lower()
            if not confirm.startswith("y"):
                print("[INFO] Deletion cancelled.")
                continue

            try:
                db_rows = get_saved_projects_from_db(ctx)
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
                        if delete_from_database_by_id(row_id, ctx):
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
                file_deleted = delete_file_from_disk(filename, ctx)
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


def get_portfolio_menu(ctx: AppContext) -> None:
    """
    Let the user select a saved project and generate a portfolio-style summary.

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        None
    """
    while True:
        print("\n=== Portfolio Generator ===")

        try:
            folder = Path(ctx.default_save_dir).resolve()
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

                display_portfolio_and_generate_pdf(items[idx], ctx)
                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a number.")
                continue

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return


def main_menu(ctx: AppContext) -> int:
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
                settings_menu(ctx)
            elif choice == "2":
                analyze_project_menu(ctx)
            elif choice == "3":
                saved_projects_menu(ctx)
            elif choice == "4":
                delete_analysis_menu(ctx)
            elif choice == "5":
                document_generator_menu()
            elif choice == "6":
                project_insights_menu(ctx)
            elif choice == "0":
                print("Goodbye!")
                return 0
            else:
                print("Please choose a valid option (0-6).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
        except Exception as e:
            print(f"[ERROR] {e}")

def ai_resume_line_menu(ctx: AppContext) -> None:
    """
    Let the user pick a saved project and show ONLY the Gemini résumé line
    (plus a bit of context), without the full portfolio PDF flow.
    """

    # Check external consent
    config_path = ctx.legacy_save_dir / "UserConfigs.json"
    try:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        has_external = config_data.get("consented", {}).get("external", False)
    except Exception as e:
        print(f"[WARN] Could not read user config, assuming no external consent: {e}")
        has_external = False

    if not has_external:
        print(
            "\n[AI RESUME] External services are disabled in your consent settings.\n"
            "Enable external services in your consent flow if you want to use Gemini.\n"
        )
        return

    # Let the user choose which analysis to base the résumé on
    folder = Path(ctx.default_save_dir).resolve()
    items = list_saved_projects(folder)

    if not items:
        print("[INFO] No saved projects.")
        input("Press Enter to return to main menu...")
        return

    print("\nSaved analyses:\n")
    for i, p in enumerate(items, start=1):
        print(f"{i}) {p.name}")

    sel = input(
        "\nChoose a file to generate an AI resume line from (or 0 to cancel): "
    ).strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(items):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    chosen_path = items[idx]
    try:
        data = json.loads(chosen_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {chosen_path.name}: {e}")
        return

    project_root = data.get("project_root")
    if not project_root:
        print("[ERROR] Saved analysis does not contain 'project_root'.")
        return

    # Run Gemini on the project folder
    try:
        ai_item = GenerateProjectResume(project_root).generate(saveToJson=False)
    except Exception as e:
        print(f"[ERROR] Could not generate AI resume line: {e}")
        return

    # Print a tight résumé-style line + minimal context
    print("\n========================================")
    print(f"Project: {ai_item.project_title or Path(project_root).name}")
    print("----------------------------------------")
    print("Resume line:")
    print(f"  • {ai_item.one_sentence_summary}")
    print("========================================\n")


def local_resume_menu(ctx: AppContext) -> None:
    """
    Generate a resume from local OOP analysis without external AI services.
    Uses the GenerateLocalResume class to build resume content from saved analysis data.

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        None
    """
    folder = Path(ctx.default_save_dir).resolve()
    items = list_saved_projects(folder)

    if not items:
        print("[INFO] No saved projects.")
        input("Press Enter to return to main menu...")
        return

    print("\n=== Local Resume Generator (No External AI) ===")
    print("\nSaved analyses:\n")
    for i, p in enumerate(items, start=1):
        print(f"{i}) {p.name}")

    sel = input(
        "\nChoose a project to generate a resume from (or 0 to cancel): "
    ).strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(items):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    chosen_path = items[idx]
    try:
        data = json.loads(chosen_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {chosen_path.name}: {e}")
        return

    # Check if OOP analysis exists - warn but continue with basic resume
    if "oop_analysis" not in data:
        print("[INFO] No OOP analysis data found. Generating basic resume.")
        print("[TIP] Re-analyze the project with external AI disabled for full OOP analysis.\n")

    # Generate resume from local analysis
    project_name = chosen_path.stem
    try:
        resume_item = GenerateLocalResume(data, project_name).generate()
    except Exception as e:
        print(f"[ERROR] Could not generate local resume: {e}")
        return

    # Display the resume
    print("\n" + "=" * 60)
    print(f"  LOCAL RESUME: {resume_item.project_title}")
    print("=" * 60)

    print("\n" + "-" * 60)
    print("  ONE-LINE RESUME SUMMARY")
    print("-" * 60)
    print(f"\n  {resume_item.one_sentence_summary}\n")
    print("-" * 60)
    print(f"\nTech Stack: {resume_item.tech_stack}")

    print("\nKey Responsibilities:")
    if resume_item.key_responsibilities:
        for resp in resume_item.key_responsibilities:
            print(f"  • {resp}")
    else:
        print("  • No specific responsibilities detected")

    print("\nSkills:")
    if resume_item.key_skills_used:
        print(f"  {', '.join(resume_item.key_skills_used)}")
    else:
        print("  No skills detected")

    print("\nImpact:")
    print(f"  {resume_item.impact}")

    # Only show OOP principles if OOP analysis exists
    if "oop_analysis" in data and resume_item.oop_principles_detected:
        print("\nOOP Principles Detected:")
        for name, principle in resume_item.oop_principles_detected.items():
            status = "✓" if principle.present else "✗"
            print(f"  {status} {name.capitalize()}: {principle.description or 'Not detected'}")

    print("\n" + "=" * 50)

    # Offer PDF generation
    generate_pdf = input("\nWould you like to generate a PDF resume? (y/n): ").strip().lower()
    if generate_pdf == "y":
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            folder_path = input("Enter the folder path to save the PDF: ").strip()
            if os.path.exists(folder_path):
                break
            else:
                attempts += 1
                if attempts < max_attempts:
                    print(f"Folder does not exist. ({attempts}/{max_attempts} attempts)")
                else:
                    print("Maximum attempts reached. Returning to menu.")
                    return

        file_name = input("Enter PDF filename (or press Enter for 'LocalResume'): ").strip() or "LocalResume"

        try:
            SimpleResumeGenerator(folder_path, data=resume_item, fileName=file_name).display_resume_line()
        except Exception as e:
            print(f"[ERROR] Could not generate PDF: {e}")

    input("\nPress Enter to return to main menu...")
    
def thumbnail_management_menu(ctx) -> None:
    """
    Interactive menu for managing project thumbnails.
    
    Args:
        ctx: Application context with storage paths
    """
    storage_path = Path(ctx.legacy_save_dir) / "project_insights.json"
    thumbnail_dir = Path(ctx.legacy_save_dir) / "thumbnails"
    thumbnail_manager = ThumbnailManager(storage_dir=thumbnail_dir)
    
    if not storage_path.exists():
        print("[INFO] Initializing project insights from saved analyses...")
        _initialize_insights_from_saved_files(ctx, storage_path)
    
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
    
def _initialize_insights_from_saved_files(ctx: AppContext, storage_path: Path) -> None:
    """
    Create project_insights.json from individual saved analysis files.
    This is called when project_insights.json doesn't exist but we have saved analyses.
    """
    from src.reporting.project_insights import record_project_insight
    
    folder = Path(ctx.default_save_dir).resolve()
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
