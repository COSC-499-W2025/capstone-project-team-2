from dataclasses import dataclass
from pathlib import Path

import mysql.connector
from mysql.connector import Error
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.Docker_finder import DockerFinder
from src.db_helper_function import HelperFunct


@dataclass
class AppContext:
    """
    Shared application handles for database access, default storage paths, and global settings variables.

    Attributes:
        conn (mysql.connector.MySQLConnection): Live MySQL connection.
        store (HelperFunct): Helper wrapper for DB operations.
        legacy_save_dir (Path): Legacy config/insight base directory.
        default_save_dir (Path): Default nested directory for new insights.
        external_consent (bool): 
    """

    conn: mysql.connector.MySQLConnection
    store: HelperFunct
    legacy_save_dir: Path
    default_save_dir: Path
    external_consent: bool

    def close(self) -> None:
        """Close the DB connection safely."""
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass


def create_app_context(external_consent_value: bool) -> AppContext:
    """
    Initialize database connection, helper store, and shared paths.

    paramaters:
        external_consent_value: value of consent for external llm tools

    Returns:
        AppContext: Shared handles for DB access and filesystem targets.

    Raises:
        Exception: If connection cannot be established after retries.
    """
    port_number, host_ip = DockerFinder().get_mysql_host_information()
    conn = None

    # Retry a handful of times in case the MySQL container is still coming up.
    for _ in range(5):
        try:
            conn = mysql.connector.connect(
                host=host_ip,
                port=port_number,
                database="appdb",
                user="appuser",
                password="apppassword",
            )

            if conn.is_connected():
                print("✅ Connected to MySQL successfully!")
                break
        except Error as e:
            print(f"MySQL not ready yet: {e}")

    if conn is None or not conn.is_connected():
        raise Exception("❌ Could not connect to MySQL after 5 attempts.")

    store = HelperFunct(conn)

    root_folder = Path(__file__).absolute().resolve().parents[1]
    legacy_save_dir = root_folder / "User_config_files"
    default_save_dir = legacy_save_dir / "project_insights"

    return AppContext(
        conn=conn,
        store=store,
        legacy_save_dir=legacy_save_dir,
        default_save_dir=default_save_dir,
        external_consent=external_consent_value
    )
