from dataclasses import dataclass
from pathlib import Path

import mysql.connector
from mysql.connector import Error

from src.Docker_finder import DockerFinder
from src.db_helper_function import HelperFunct


@dataclass
class AppContext:
    conn: mysql.connector.MySQLConnection
    store: HelperFunct
    legacy_save_dir: Path
    default_save_dir: Path

    def close(self) -> None:
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass


def create_app_context() -> AppContext:
    """
    Initialize database connection, helper store, and shared paths.
    """
    port_number, host_ip = DockerFinder().get_mysql_host_information()
    conn = None

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
    )
