from pathlib import Path
import json

# Menu flows for the CLI, delegating to analysis, saved-project, and portfolio helpers.
from src.CLI_Interface_for_user_config import ConfigurationForUsersUI
from src.analysis_service import (
    input_path,
    analyze_project,
    extract_if_zip,
)
from src.app_context import AppContext
from src.portfolio import display_portfolio_and_generate_pdf
from src.saved_projects import (
    delete_file_from_disk,
    delete_from_database_by_id,
    get_saved_projects_from_db,
    list_saved_projects,
    show_saved_summary,
)
from src.user_startup_config import ConfigLoader
from src.Generate_AI_Resume import GenerateProjectResume


def settings_menu() -> None:
    """Load config and launch the configuration CLI."""
    cfg = ConfigLoader().load()
    ConfigurationForUsersUI(cfg).run_configuration_cli()


def analyze_project_menu(ctx: AppContext) -> None:
    """
    Ask user if their project is in a directory or zip file and analyze it.

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

        try:
            if choice == "1":
                dir_path = input_path("Enter path to project directory: ")
                if dir_path:
                    return analyze_project(dir_path, ctx)
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
                return analyze_project(
                    extracted,
                    ctx,
                    project_label=zip_path.stem,
                )
            elif choice == "0":
                return None
            else:
                print("Please choose a valid option (0–2).")
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
        int: Exit code (0 on normal exit).
    """
    while True:
        print("\n=== Main Menu ===")
        print("1) Settings")
        print("2) Analyze project")
        print("3) Saved projects")
        print("4) Delete analysis")
        print("5) AI Portfolio Generator")
        print("6) AI Resume Line Generator")
        print("0) Exit")
        choice = input("Select an option: ").strip()

        try:
            if choice == "1":
                settings_menu()
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
        "\nChoose a file to generate an AI résumé line from (or 0 to cancel): "
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
        print(f"[ERROR] Could not generate AI résumé line: {e}")
        return

    # Print a tight résumé-style line + minimal context
    print("\n========================================")
    print(f"Project: {ai_item.project_title or Path(project_root).name}")
    print("----------------------------------------")
    print("Résumé line:")
    print(f"  • {ai_item.one_sentence_summary}")
    print("========================================\n")
