import sys
from pathlib import Path

# CLI entrypoint that wires consent/config into the shared menu flow.
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.Configuration import configuration_for_users
from src.app_context import create_app_context
from src.menus import main_menu
from src.user_consent import UserConsent
from src.user_startup_config import ConfigLoader


def run() -> int:
    """
    Entry point for the CLI application.
    Handles consent, loads configuration, and dispatches to the main menu.

    Returns:
        int: Process exit code (0 on normal exit, non-zero on failure/decline).

    Raises:
        Exception: Propagates unexpected errors after closing context.
    """
    consent_manager = UserConsent()
    proceed = consent_manager.ask_for_consent()
    if not proceed:
        print("[EXIT] User declined consent. Exiting.")
        return 1

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

    ctx = create_app_context(external_consent_value=consent_manager.has_external_consent)
    try:
        return main_menu(ctx)
    finally:
        ctx.close()


if __name__ == "__main__":
    sys.exit(run())
