import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mysql.connector
from mysql.connector import Error

from src.storage.db_helper_function import HelperFunct

@dataclass
class AppContext:
    conn: mysql.connector.MySQLConnection
    store: HelperFunct
    external_consent: bool
    currently_uploaded_path: Optional[Path]

    def close(self) -> None:
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
        except Exception:
            pass

    def reload_consent_from_db(self) -> None:
        """
        Reload external consent settings from the database.
        """
        try:
            consent = self.store.get_consent_settings()
            self.external_consent = consent.get("external", False)
        except Exception:
            pass


def create_app_context(external_consent_value: Optional[bool] = None) -> AppContext:
    """
    Initialize database connection and helper store.

    Connection priority:
      1) Environment variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
      2) Defaults suitable for Docker Compose network (app_database:3306)

    Notes:
      - Inside Docker: DB_HOST should be 'app_database', DB_PORT '3306'
      - On your laptop: DB_HOST '127.0.0.1', DB_PORT '3309' (because of 3309:3306 mapping)
    """

    # --- Read connection settings from environment (preferred) ---
    host = os.getenv("DB_HOST", "app_database")
    db_name = os.getenv("DB_NAME", "appdb")
    user = os.getenv("DB_USER", "appuser")
    password = os.getenv("DB_PASSWORD", "apppassword")

    # DB_PORT can be missing or malformed; handle safely
    port_raw = os.getenv("DB_PORT", "3306")
    try:
        port = int(port_raw)
    except ValueError:
        # Fallback to default MySQL port if env var is junk
        port = 3306

    retries = int(os.getenv("DB_CONNECT_RETRIES", "10"))
    delay_s = float(os.getenv("DB_CONNECT_DELAY_SECONDS", "1.0"))

    conn = None
    last_err: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                database=db_name,
                user=user,
                password=password,
            )

            if conn.is_connected():
                print(f"✅ Connected to MySQL successfully! ({host}:{port}/{db_name})")
                last_err = None
                break

        except Error as e:
            last_err = e
            print(f"MySQL not ready yet (attempt {attempt}/{retries}): {e}")
            time.sleep(delay_s)

    if conn is None or not conn.is_connected():
        detail = f"{last_err}" if last_err else "unknown error"
        raise Exception(
            f"❌ Could not connect to MySQL after {retries} attempts "
            f"({host}:{port}/{db_name}). Last error: {detail}"
        )

    store = HelperFunct(conn)

    # --- Determine external consent value ---
    if external_consent_value is None:
        try:
            consent = store.get_consent_settings() or {}
            external_consent_value = bool(consent.get("external", False))
        except Exception:
            external_consent_value = False

    return AppContext(
        conn=conn,
        store=store,
        external_consent=external_consent_value,
        currently_uploaded_path=None,
    )

runtimeAppContext = create_app_context()