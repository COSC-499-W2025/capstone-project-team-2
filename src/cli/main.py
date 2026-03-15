import sys
from pathlib import Path
import time
import os
import signal
import shutil

# CLI entrypoint that wires consent/config into the shared menu flow.
#sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.app_context import runtimeAppContext
from src.cli.menus import main_menu
from src.config.user_consent import UserConsent
from src.API.general_API import app
from src.API.consent_API import *
import subprocess
from threading import Event

exit = Event()

def run() -> int:
    #Setting up variations of termination keybinds to quit safely and shutdown appropriate processes while in wait mode
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)

    #Run API command to start API in background
    uvicorn_instance = subprocess.Popen(["python", "-m", "uvicorn", "src.API.general_API:app", "--host", "0.0.0.0", "--port", "8000", "--reload" ])

    #Change directory to correctly run npm commands
    os.chdir("frontend/")

    #Run series of npm commands. Run waits for process to finish before next one continues while Popen will not wait since it's
    # needed to be an active process in the background
    subprocess.run([shutil.which("npm"), "install"])
    subprocess.run([shutil.which("npm"), "run", "build"])
    npm_instance = subprocess.Popen([shutil.which("npm"), "run", "dev"])

    #Sets up a wait for event, the wait is interrupted on event and does not wait 60s per check
    while not exit.is_set():
        exit.wait(60)

    #After wait is interrupted, send shutdown signal to active processes safely before exit
    npm_instance.terminate()
    uvicorn_instance.terminate()
    return 0

#Method for the event handler to handle starting shutdown
def quit(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit.set()

def run_deprecated() -> int:
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
