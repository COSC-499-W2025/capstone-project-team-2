from dataclasses import dataclass
from pathlib import Path
from fastapi import UploadFile
from types import SimpleNamespace
import os
import sqlite3
from typing import Optional

# Decide DB init behavior: default connect, but auto-skip when running pytest unless overridden.
_env_skip = os.getenv("SKIP_DB_INIT")
if _env_skip is None:
    argv = os.sys.argv if os.sys.argv else []
    if ("PYTEST_CURRENT_TEST" in os.environ) or any("pytest" in arg for arg in argv):
        os.environ["SKIP_DB_INIT"] = "1"
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.storage.db_helper_function import HelperFunct
class _NullStore:

    def insert_json(self, *args, **kwargs): 
        return None
    
    def fetch_by_name(self, *args, **kwargs): 
        return None
    
    def delete(self, *args, **kwargs): 
        return False

    def count_file_references(self, *args, **kwargs): 
        return 0
@dataclass
class AppContext:
    """
    Shared application handles for database access, default storage paths, and global settings variables.

    Attributes:
        conn (sqlite3.Connection): Live SQLite connection.
        store (HelperFunct): Helper wrapper for DB operations.
        legacy_save_dir (Path): Legacy config/insight base directory.
        default_save_dir (Path): Default nested directory for new insights.
        external_consent (bool): consent for external llm use
        currently_uploaded_file (Path | UploadFile): file currently uploaded, can be a file-like object or a file path
    """

    conn: sqlite3.Connection
    store: HelperFunct
    legacy_save_dir: Path
    default_save_dir: Path
    external_consent: bool
    data_consent: bool
    currently_uploaded_file: Path | UploadFile
    currently_uploaded_project_name: Optional[str] = None

    def close(self) -> None:
        """Close the DB connection safely."""
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass


def create_app_context(external_consent_value=False, data_consent_value=False) -> AppContext:
    """
    Initialize database connection, helper store, and shared paths.

    paramaters:
        external_consent_value: value of consent for external llm tools

    Returns:
        AppContext: Shared handles for DB access and filesystem targets.

    Raises:
        Exception: If connection cannot be established after retries.
    """
    root_folder = Path(__file__).absolute().resolve().parents[2]
    legacy_save_dir = root_folder / "User_config_files"
    default_save_dir = legacy_save_dir / "project_insights"
    if os.getenv("SKIP_DB_INIT") == "1":
        return AppContext(
            conn=None,
            store=_NullStore(),
            legacy_save_dir=legacy_save_dir,
            default_save_dir=default_save_dir,
            external_consent=external_consent_value,
            data_consent=data_consent_value,
            currently_uploaded_file=None,
            currently_uploaded_project_name=None,
        )

    db_path = root_folder / "appdb.db"
    schema_path = root_folder / "database.sql"

    if not db_path.exists():
        with open(schema_path, "r") as f:
            sql = f.read()
        temp_conn = sqlite3.connect(str(db_path))
        temp_conn.executescript(sql)
        temp_conn.close()
        print("✅ Database initialized from database.sql")
        
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode=WAL")
        if schema_path.exists():
            conn.executescript(schema_path.read_text())
        print("✅ Connected to SQLite successfully!")
    except Exception as e:
        raise Exception(f"❌ Could not connect to SQLite: {e}")

    store = HelperFunct(conn)

    return AppContext(
        conn=conn,
        store=store,
        legacy_save_dir=legacy_save_dir,
        default_save_dir=default_save_dir,
        external_consent=external_consent_value,
        data_consent=data_consent_value,
        currently_uploaded_file=None,
        currently_uploaded_project_name=None,
    )

#global variable so we don't need to pass the app context through the API for calls
runtimeAppContext = create_app_context()
