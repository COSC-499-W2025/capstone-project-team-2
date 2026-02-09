import sys
from pathlib import Path

# CLI entrypoint that wires consent/config into the shared menu flow.
#sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.app_context import runtimeAppContext
from src.cli.menus import main_menu
from src.config.user_consent import UserConsent
from src.API.general_API import app
from src.API.consent_API import *

def run() -> int:
    """
    Entry point for the CLI application.
    Handles consent, loads configuration, and dispatches to the main menu.

    Returns:
        int: Process exit code (0 on normal exit, non-zero on failure/decline).

    Raises:
        Exception: Propagates unexpected errors after closing context.
    """

    #Considered CLI since we can place our consent .md in our webpage files
    consent_manager = UserConsent()
    proceed = consent_manager.ask_for_consent()
    if not proceed:
        print("[EXIT] User declined consent. Exiting.")
        return 1

    try:
        consent_object = PrivacyConsentRequest(data_consent=consent_manager.has_data_consent, external_consent=consent_manager.has_external_consent)
        update_privacy_consent(consent_object)
    except Exception as e:
        print(f"[WARN] Failed to persist consent to configuration: {e}")

    return main_menu()


if __name__ == "__main__":
    sys.exit(run())
