"""
CLI menus for configuration, consent aware analysis, saved reports, and project insights.

Entrypoints here stitch together user facing flows:
- settings: configure consent and defaults
- analyze: ingest a directory or ZIP (with optional AI analysis when consented)
- saved/delete: review or remove persisted analyses
- AI portfolio/resume: regenerate AI driven summaries when external services are permitted
- insights: view chronological projects/skills, rankings, and top summaries from stored insights

All data is now stored in MySQL database.
"""

from pathlib import Path
import os

# Menu flows for the CLI, delegating to analysis, saved-project, and portfolio helpers.
from src.cli.CLI_Interface_for_user_config import ConfigurationForUsersUI
from src.core.analysis_service import (
    analyze_project,
    extract_if_zip,
)
from src.core.app_context import AppContext
from src.reporting.portfolio import display_portfolio_and_generate_pdf
from src.storage.saved_projects import (
    delete_from_database_by_id,
    get_saved_projects_from_db,
    get_project_by_id,
    show_saved_summary,
)
from src.config.project_thumbnails import ThumbnailManager
from src.cli.menu_insights import project_insights_menu
from src.reporting.project_insights import (
    list_project_insights,
    update_thumbnail_in_insights,
    record_project_insight,
    remove_thumbnail_from_insights,
    delete_insight,
)

from src.config.Configuration import configuration_for_users
from src.reporting.Generate_AI_Resume import GenerateProjectResume, GenerateLocalResume
from src.reporting.resume_pdf_generator import SimpleResumeGenerator


def settings_menu(ctx: AppContext) -> None:
    """
    Display the settings menu with options for user configuration and external services.
    """
    while True:
        print("\n=== Settings Menu ===")
        print("1) User Configuration")
        print("2) Toggle External Services")
        print("3) Manage Thumbnails")
        print("0) Back to Main Menu")

        choice = input("Select an option: ").strip()

        if choice == "1":
            config = configuration_for_users()
            ConfigurationForUsersUI(config.config_data).run_configuration_cli()
        elif choice == "2":
            toggle_external_services(ctx)
        elif choice == "3":
            thumbnail_management_menu(ctx)
        elif choice == "0":
            return
        else:
            print("Please choose a valid option (0-3).")


def toggle_external_services(ctx: AppContext) -> None:
    """Toggle external services on or off during the current session."""
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

        try:
            config = configuration_for_users()
            data_consent = True
            config.save_with_consent(ctx.external_consent, data_consent)
            config.save_config()
            print(f"\n[SUCCESS] External services are now {new_status}")
        except Exception as e:
            print(f"\n[WARNING] Setting changed for this session but failed to save: {e}")
            print(f"External services are now {new_status}")
    elif choice == "0":
        return
    else:
        print("\n[INFO] Invalid option. No changes made.")


def prompt_thumbnail_upload(project_id: str, project_name: str, ctx: AppContext) -> bool:
    """Prompt the user to upload a thumbnail for a project after analysis."""
    print(f"\n=== Project Thumbnail ===")
    add_thumbnail = input(f"Would you like to add a thumbnail image for '{project_name}'? (y/n): ").strip().lower()

    if add_thumbnail != 'y':
        print("[INFO] You can add or update thumbnails later in Settings > Manage Project Thumbnails.")
        return False

    thumbnail_dir = Path.home() / ".project_analyzer" / "thumbnails"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
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

        is_valid, error = thumbnail_manager.validate_image(image_path)
        if not is_valid:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                print(f"[ERROR] {error}")
                print(f"        {remaining} attempt(s) remaining.")
            continue

        success, error, thumb_path = thumbnail_manager.add_thumbnail(
            project_id=project_id,
            image_path=image_path,
            resize=True
        )

        if success:
            print(f"[SUCCESS] Thumbnail added for '{project_name}'")
            print(f"          Saved to: {thumb_path}")
            update_thumbnail_in_insights(project_id, thumb_path)
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
    """Ask user if their project is in a directory or zip file and analyze it."""
    while True:
        print("\n=== Analyze Project Menu ===")
        print("\nChoose input type:")
        print("  1) Directory")
        print("  2) ZIP file")
        print("  0) Exit to Main Menu")

        choice = input("Select an option: ").strip()

        use_ai = False
        if ctx.external_consent:
            use_ai = input("Add AI analysis? (y/n): ").strip().lower() == "y"

        try:
            project_name = None

            if choice == "1":
                dir_path = input_path("Enter path to project directory: ")
                if dir_path:
                    project_name = dir_path.name
                    #  pass ctx into analyze_project
                    analyze_project(root=dir_path, use_ai_analysis=use_ai)

            elif choice == "2":
                zip_path = input_path("Enter path to ZIP: ")
                if not zip_path:
                    print("[ERROR] ZIP path required.")
                    continue

                extracted = extract_if_zip(zip_path)
                if not extracted:
                    print("[ERROR] Could not extract ZIP. Please check the file and try again.")
                    return None

                project_name = zip_path.stem
                # pass ctx into analyze_project
                analyze_project(root=extracted, use_ai_analysis=use_ai)

            elif choice == "0":
                return None

            else:
                print("Please choose a valid option (0-2).")
                continue

            # Thumbnail prompt (unchanged)
            if project_name:
                insights = list_project_insights()
                matching_insight = None
                for insight in reversed(insights):
                    if insight.project_name == project_name:
                        matching_insight = insight
                        break

                if matching_insight:
                    prompt_thumbnail_upload(
                        project_id=matching_insight.id,
                        project_name=project_name,
                        ctx=ctx,
                    )
                else:
                    print("[WARNING] Could not find project insight. Skipping thumbnail prompt.")

            return

        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
            return None
        except Exception as e:
            print(f"[ERROR] {e}")
            

def saved_projects_menu(ctx: AppContext) -> None:
    """Display all saved projects from the database."""
    while True:
        print("\n=== Saved Project Menu ===")

        try:
            projects = get_saved_projects_from_db(ctx)

            if not projects:
                print("[INFO] No saved projects")
                input("Press Enter to return to main menu...")
                return

            print(f"\nSaved analyses:\n")
            for i, (record_id, filename, uploaded_at) in enumerate(projects, start=1):
                timestamp = uploaded_at.strftime("%Y-%m-%d %H:%M") if uploaded_at else "Unknown"
                print(f"{i}) [{record_id}] {filename} (saved: {timestamp})")

            sel = input("\nChoose a file to view (or press 0 to exit to main menu): ").strip()
            if not sel or sel == "0":
                return

            try:
                idx = int(sel) - 1
                if idx < 0 or idx >= len(projects):
                    print("Invalid selection.")
                    continue

                record_id = projects[idx][0]
                filename = projects[idx][1]
                data = get_project_by_id(record_id, ctx)

                if data:
                    show_saved_summary(data, title=filename)
                else:
                    print(f"[ERROR] Could not load project data for ID {record_id}")

                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a number.")
                continue

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return


def delete_analysis_menu(ctx: AppContext) -> None:
    """Menu for deleting saved project analyses from the database."""
    while True:
        print("\n=== Delete Analysis Menu ===")

        try:
            projects = get_saved_projects_from_db(ctx)

            if not projects:
                print("[INFO] No saved projects.")
                input("Press Enter to return to main menu...")
                return

            print("\nSaved projects:\n")
            for i, (record_id, filename, uploaded_at) in enumerate(projects, start=1):
                timestamp = uploaded_at.strftime("%Y-%m-%d %H:%M") if uploaded_at else "Unknown"
                print(f"{i}) [{record_id}] {filename} (saved: {timestamp})")

            sel = input("\nEnter the number of the project to delete (or 0 to exit): ").strip()
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

            record_id = projects[sel_idx][0]
            filename = projects[sel_idx][1]

            confirm = input(f"Are you sure you want to delete '{filename}' (ID: {record_id})? (y/n): ").strip().lower()
            if not confirm.startswith("y"):
                print("[INFO] Deletion cancelled.")
                continue

            try:
                if delete_from_database_by_id(record_id, ctx):
                    print(f"[SUCCESS] Deleted project '{filename}' (ID: {record_id})")
                else:
                    print("[WARNING] Could not delete project record.")
            except Exception as e:
                print(f"[WARNING] Error deleting project: {e}")

            try:
                insights = list_project_insights()
                for insight in insights:
                    if insight.project_data_id == record_id:
                        delete_insight(insight.id)
                        print("[INFO] Also deleted associated project insight.")
                        break
            except Exception as e:
                print(f"[WARNING] Could not check/delete associated insight: {e}")

            another = input("\nDelete another analysis? (y/n): ").strip().lower()
            if not another.startswith("y"):
                return

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return


def get_portfolio_menu(ctx: AppContext) -> None:
    """Let the user select a saved project and generate a portfolio-style summary."""
    while True:
        print("\n=== Portfolio Generator ===")

        try:
            projects = get_saved_projects_from_db(ctx)

            if not projects:
                print("[INFO] No saved projects")
                input("Press Enter to return to main menu...")
                return

            print(f"\nSaved analyses:\n")
            for i, (record_id, filename, uploaded_at) in enumerate(projects, start=1):
                timestamp = uploaded_at.strftime("%Y-%m-%d %H:%M") if uploaded_at else "Unknown"
                print(f"{i}) [{record_id}] {filename} (saved: {timestamp})")

            sel = input("\nChoose a file to view (or press 0 to exit to main menu): ").strip()
            if not sel or sel == "0":
                return

            try:
                idx = int(sel) - 1
                if idx < 0 or idx >= len(projects):
                    print("Invalid selection.")
                    continue

                record_id = projects[idx][0]
                data = get_project_by_id(record_id, ctx)

                if data:
                    display_portfolio_and_generate_pdf(data, ctx)
                else:
                    print(f"[ERROR] Could not load project data for ID {record_id}")

                input("Press Enter to continue...")
            except ValueError:
                print("Please enter a number.")
                continue

        except Exception as e:
            print(f"[ERROR] {e}")
            input("Press Enter to return to main menu...")
            return


def main_menu(ctx: AppContext) -> int:
    """Top-level navigation loop for the CLI."""
    while True:
        print("\n=== Main Menu ===")
        print("1) Settings")
        print("2) Analyze project")
        print("3) Saved projects")
        print("4) Delete analysis")
        print("5) Portfolio Generator")
        print("6) AI Resume Line Generator")
        print("7) Local Resume Generator (No External AI)")
        print("8) Project insights")
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
                get_portfolio_menu(ctx)
            elif choice == "6":
                ai_resume_line_menu(ctx)
            elif choice == "7":
                local_resume_menu(ctx)
            elif choice == "8":
                project_insights_menu(ctx)
            elif choice == "0":
                print("Goodbye!")
                return 0
            else:
                print("Please choose a valid option (0-8).")
        except KeyboardInterrupt:
            print("\n[Interrupted] Returning to menu.")
        except Exception as e:
            print(f"[ERROR] {e}")


def ai_resume_line_menu(ctx: AppContext) -> None:
    """Let the user pick a saved project and show ONLY the Gemini resume line."""
    if not ctx.external_consent:
        print(
            "\n[AI RESUME] External services are disabled in your consent settings.\n"
            "Enable external services in your consent flow if you want to use Gemini.\n"
        )
        return

    projects = get_saved_projects_from_db(ctx)

    if not projects:
        print("[INFO] No saved projects.")
        input("Press Enter to return to main menu...")
        return

    print("\nSaved analyses:\n")
    for i, (record_id, filename, uploaded_at) in enumerate(projects, start=1):
        timestamp = uploaded_at.strftime("%Y-%m-%d %H:%M") if uploaded_at else "Unknown"
        print(f"{i}) [{record_id}] {filename} (saved: {timestamp})")

    sel = input("\nChoose a file to generate an AI resume line from (or 0 to cancel): ").strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(projects):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    record_id = projects[idx][0]
    data = get_project_by_id(record_id, ctx)

    if not data:
        print(f"[ERROR] Could not load project data for ID {record_id}")
        return

    project_root = data.get("project_root")
    if not project_root:
        print("[ERROR] Saved analysis does not contain 'project_root'.")
        return

    try:
        ai_item = GenerateProjectResume(project_root).generate(saveToJson=False)
    except Exception as e:
        print(f"[ERROR] Could not generate AI resume line: {e}")
        return

    print("\n========================================")
    print(f"Project: {ai_item.project_title or Path(project_root).name}")
    print("----------------------------------------")
    print("Resume line:")
    print(f"  - {ai_item.one_sentence_summary}")
    print("========================================\n")


def local_resume_menu(ctx: AppContext) -> None:
    """Generate a resume from local OOP analysis without external AI services."""
    projects = get_saved_projects_from_db(ctx)

    if not projects:
        print("[INFO] No saved projects.")
        input("Press Enter to return to main menu...")
        return

    print("\n=== Local Resume Generator (No External AI) ===")
    print("\nSaved analyses:\n")
    for i, (record_id, filename, uploaded_at) in enumerate(projects, start=1):
        timestamp = uploaded_at.strftime("%Y-%m-%d %H:%M") if uploaded_at else "Unknown"
        print(f"{i}) [{record_id}] {filename} (saved: {timestamp})")

    sel = input("\nChoose a project to generate a resume from (or 0 to cancel): ").strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(projects):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    record_id = projects[idx][0]
    filename = projects[idx][1]
    data = get_project_by_id(record_id, ctx)

    if not data:
        print(f"[ERROR] Could not load project data for ID {record_id}")
        return

    if "oop_analysis" not in data:
        print("[INFO] No OOP analysis data found. Generating basic resume.")
        print("[TIP] Re-analyze the project with external AI disabled for full OOP analysis.\n")

    project_name = filename[:-5] if filename.endswith('.json') else filename
    try:
        resume_item = GenerateLocalResume(data, project_name).generate()
    except Exception as e:
        print(f"[ERROR] Could not generate local resume: {e}")
        return

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
            print(f"  - {resp}")
    else:
        print("  - No specific responsibilities detected")

    print("\nSkills:")
    if resume_item.key_skills_used:
        print(f"  {', '.join(resume_item.key_skills_used)}")
    else:
        print("  No skills detected")

    print("\nImpact:")
    print(f"  {resume_item.impact}")

    if "oop_analysis" in data and resume_item.oop_principles_detected:
        print("\nOOP Principles Detected:")
        for name, principle in resume_item.oop_principles_detected.items():
            status = "Y" if principle.present else "N"
            print(f"  {status} {name.capitalize()}: {principle.description or 'Not detected'}")

    print("\n" + "=" * 50)

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


def thumbnail_management_menu(ctx: AppContext) -> None:
    """Interactive menu for managing project thumbnails."""
    thumbnail_dir = Path.home() / ".project_analyzer" / "thumbnails"
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_manager = ThumbnailManager(storage_dir=thumbnail_dir)

    while True:
        print("\n=== Thumbnail Management ===")
        print("1) Add/Update thumbnail for a project")
        print("2) Remove thumbnail from a project")
        print("0) Back to Main Menu")

        choice = input("\nSelect an option: ").strip()

        try:
            if choice == "1":
                _add_thumbnail_workflow(thumbnail_manager)
            elif choice == "2":
                _remove_thumbnail_workflow(thumbnail_manager)
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


def _add_thumbnail_workflow(thumbnail_manager: ThumbnailManager) -> None:
    """Guide user through adding a thumbnail to a project."""
    insights = list_project_insights()

    if not insights:
        print("[INFO] No projects found. Analyze a project first.")
        input("Press Enter to continue...")
        return

    print("\n=== Available Projects ===\n")
    for i, insight in enumerate(insights, start=1):
        has_thumbnail_in_db = insight.thumbnail is not None and insight.thumbnail.get("exists")
        has_thumbnail_on_disk = (
            thumbnail_manager.get_thumbnail_path(insight.id) is not None or
            thumbnail_manager.get_thumbnail_path(insight.project_name) is not None
        )
        has_thumbnail = has_thumbnail_in_db or has_thumbnail_on_disk
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

    success, error, thumb_path = thumbnail_manager.add_thumbnail(
        selected_insight.id,
        image_path,
        resize=resize
    )

    if success:
        update_success = update_thumbnail_in_insights(
            selected_insight.id,
            thumb_path,
        )

        if update_success:
            print(f"[SUCCESS] Thumbnail added for '{selected_insight.project_name}'")
            print(f"[INFO] Saved to: {thumb_path}")
        else:
            print(f"[WARNING] Thumbnail saved but could not update database")
    else:
        print(f"[ERROR] Failed to add thumbnail: {error}")

    input("\nPress Enter to continue...")


def _remove_thumbnail_workflow(thumbnail_manager: ThumbnailManager) -> None:
    """Guide user through removing a thumbnail from a project."""
    insights = list_project_insights()

    projects_with_thumbnails = []
    for insight in insights:
        has_in_db = insight.thumbnail and insight.thumbnail.get("exists")
        thumb_path_by_id = thumbnail_manager.get_thumbnail_path(insight.id)
        thumb_path_by_name = thumbnail_manager.get_thumbnail_path(insight.project_name)
        thumb_path = thumb_path_by_id or thumb_path_by_name
        if has_in_db or thumb_path:
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

        selected_insight, _ = projects_with_thumbnails[idx]

    except ValueError:
        print("[ERROR] Please enter a valid number.")
        input("Press Enter to continue...")
        return

    confirm = input(
        f"\nAre you sure you want to remove the thumbnail for '{selected_insight.project_name}'? (y/n): "
    ).strip().lower()

    if confirm == 'y':
        deleted = thumbnail_manager.delete_thumbnail(selected_insight.id)
        if not deleted:
            deleted = thumbnail_manager.delete_thumbnail(selected_insight.project_name)

        if deleted:
            remove_thumbnail_from_insights(selected_insight.id)
            print(f"[SUCCESS] Thumbnail removed for '{selected_insight.project_name}'")
        else:
            print("[ERROR] Failed to remove thumbnail from filesystem.")
    else:
        print("[INFO] Cancelled.")

    input("\nPress Enter to continue...")


def _initialize_insights_from_saved_projects(ctx: AppContext) -> None:
    """
    Create project_insights records from saved project_data records.
    This is called when project_insights table is empty but we have saved analyses.
    Useful for migrating existing project_data to the insights system.
    """
    projects = get_saved_projects_from_db(ctx)

    if not projects:
        print("[INFO] No saved analyses found.")
        return

    existing_insights = list_project_insights()
    existing_project_data_ids = {
        insight.project_data_id for insight in existing_insights
        if insight.project_data_id is not None
    }

    count = 0
    for record_id, filename, uploaded_at in projects:
        if record_id in existing_project_data_ids:
            continue

        try:
            data = get_project_by_id(record_id, ctx)
            if not data:
                continue

            contributors = data.get("contributors") or {}

            record_project_insight(
                data,
                contributors=contributors,
                project_data_id=record_id,
            )
            count += 1
        except Exception as e:
            print(f"[WARNING] Couldn't import {filename}: {e}")

    if count > 0:
        print(f"[SUCCESS] Initialized {count} project(s) into insights.")


def input_path(prompt: str, allow_blank: bool = False) -> Path | None:
    """Prompt user for a path until it exists."""
    while True:
        p = input(prompt).strip()
        if not p and allow_blank:
            return None
        path = Path(p).expanduser().resolve()
        if path.exists():
            return path
        print(f"[ERROR] Path not found: {path}")