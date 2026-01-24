import json
import mysql.connector
from mysql.connector import Error
from typing import Union, Optional, List, Dict, Any
from datetime import datetime, timezone


class HelperFunct:
    """
    Handles all database operations for the project_data table.
    Stores and retrieves JSON contents.
    
    Tables managed:
    - project_data: Main project analysis storage
    - project_insights: Lightweight project metadata for quick queries
    - user_config: User configuration and consent settings

    """

    def __init__(self, connection):
        """
        Initialize the HelperFunct with an active MySQL database connection.
        Automatically ensure all required tables exist
        
        Args:
            connection: An active MySQL connection object that is already connected.

        Returns:
            None: This method initializes the database helper instance.
            
        Raises:
            RuntimeError: if connection is invalid or not connected
        """
        if connection is None or not connection.is_connected():
            raise RuntimeError("ProjectDataStore was given an invalid MySQL connection.")
        self.conn = connection
        self._ensure_tables_exist()


    def _ensure_tables_exist(self) -> None:
        """
        Create all required tables if they don't exist.
        Called automatically on initialization.
        """
        cursor = self.conn.cursor()
        try:
            # Main project data table (existing, but ensure it has all columns)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    content JSON NOT NULL,
                    file_blob LONGBLOB,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_filename (filename),
                    INDEX idx_uploaded_at (uploaded_at)
                )
            """)

            # Project insights table - lightweight metadata linked to project_data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_insights (
                    id VARCHAR(36) PRIMARY KEY,
                    project_data_id INT,
                    project_name VARCHAR(255) NOT NULL,
                    summary TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    languages JSON,
                    frameworks JSON,
                    skills JSON,
                    project_type VARCHAR(100) DEFAULT 'unknown',
                    detection_mode VARCHAR(50) DEFAULT 'local',
                    duration_estimate VARCHAR(100) DEFAULT 'unavailable',
                    contributors JSON,
                    stats JSON,
                    file_analysis JSON,
                    thumbnail JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_data_id) REFERENCES project_data(id) ON DELETE SET NULL,
                    INDEX idx_project_name (project_name),
                    INDEX idx_analyzed_at (analyzed_at),
                    INDEX idx_project_type (project_type)
                )
            """)

            # User configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_config (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_config_key (config_key)
                )
            """)

            self.conn.commit()
        finally:
            cursor.close()

    def insert_json(self, filename: str, data: dict, raw_bytes: bytes = None) -> int:
        """
        Insert JSON data into the database, storing both the structured JSON
        content and the raw binary representation.

        Args:
            filename: The name of the file associated with the JSON data.
            data: A dictionary representing the JSON content to store.
            raw_bytes: Optional raw byte representation of the JSON content.

        Returns:
            int: The database row ID of the newly inserted record.
        """

        if raw_bytes is None:
            raw_bytes = json.dumps(data).encode("utf-8")

        cursor = self.conn.cursor()
        try:
            cursor.execute(
            "INSERT INTO project_data (filename, content, file_blob) VALUES (%s, %s, %s)",
            (filename, json.dumps(data), raw_bytes)
            )
            self.conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def fetch_by_id(self, row_id: int) -> Optional[dict]:
        """
        Retrieve JSON content from the database using a row ID.

        Args:
            row_id: The unique database ID of the record to retrieve.

        Returns:
            dict | None: The parsed JSON content as a dictionary if found,
            or None if no matching record exists.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content FROM project_data WHERE id = %s", (row_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            cursor.close()

    def fetch_file_blob_by_id(self, row_id: int) -> bytes:
        """
        Retrieve the raw binary file blob from the database using a row ID.

        Args:
            row_id: The unique database ID of the record to retrieve.

        Returns:
            bytes | None: The raw file blob if found, or None if the record
            does not exist.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT file_blob FROM project_data WHERE id = %s", (row_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()

    def fetch_all(self):
        """
        Retrieve all JSON content entries stored in the database.

        Args:
            None: This method does not take any parameters.

        Returns:
            list: A list of dictionaries representing all stored JSON
            contents in the project_data table.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content FROM project_data")
            rows = cursor.fetchall()
            return [json.loads(r[0]) for r in rows]
        finally:
            cursor.close()
            
    def fetch_all_projects(self) -> List[tuple]:
        """
        Fetch all saved projects with metadata.

        Returns:
            list[tuple]: (id, filename, uploaded_at) rows ordered by upload date desc.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT id, filename, uploaded_at FROM project_data ORDER BY uploaded_at DESC"
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def update(self, row_id: int, input: Union[dict, bytes], filename: str = None) -> bool:
        """
        Update an existing database record so that the JSON content and
        binary file blob remain synchronized.

        Args:
            row_id: The unique database ID of the record to update.
            input: Either a dictionary containing JSON data or raw JSON bytes.
            filename: Optional new filename to associate with the record.

        Returns:
            bool: True if the record was successfully updated, False otherwise.
        """
        if isinstance(input, dict):
            content = input
            blob = json.dumps(input).encode("utf-8")
        elif isinstance(input, bytes):
            blob = input
            content = json.loads(input.decode("utf-8"))
        else:
            raise ValueError("new_input must be a dict or bytes")

        sql = "UPDATE project_data SET content=%s, file_blob=%s"
        params = [json.dumps(content), blob]

        if filename is not None:
            sql += ", filename=%s"
            params.append(filename)

        sql += " WHERE id=%s"
        params.append(row_id)

        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def count_file_references(self, filename: str) -> int:
        """
        Count how many database records reference a given filename.

        Args:
            filename: The filename to search for in the database.

        Returns:
            int: The number of records that reference the specified filename.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM project_data WHERE filename = %s",
                (filename,),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        finally:
            cursor.close()
            
    def delete(self, row_id: int) -> bool:
        """
        Delete a database record by its row ID.

        Args:
            row_id: The unique database ID of the record to delete.

        Returns:
            bool: True if the record was successfully deleted, False otherwise.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM project_data WHERE id = %s", (row_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            
    def insert_insight(
        self,
        insight_id: str,
        project_name: str,
        summary: str = "",
        analyzed_at: Optional[datetime] = None,
        languages: Optional[List[str]] = None,
        frameworks: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        project_type: str = "unknown",
        detection_mode: str = "local",
        duration_estimate: str = "unavailable",
        contributors: Optional[Dict[str, Any]] = None,
        stats: Optional[Dict[str, Any]] = None,
        file_analysis: Optional[Dict[str, Any]] = None,
        thumbnail: Optional[Dict[str, Any]] = None,
        project_data_id: Optional[int] = None,
    ) -> str:
        """
        Insert a new project insight record.

        Args:
            insight_id: UUID string for the insight.
            project_name: Name of the project.
            summary: Project summary text.
            analyzed_at: When the analysis was performed.
            languages: List of programming languages detected.
            frameworks: List of frameworks detected.
            skills: List of skills associated with the project.
            project_type: Type of project (e.g., 'web', 'cli', 'library').
            detection_mode: How the project type was detected.
            duration_estimate: Estimated project duration.
            contributors: Contributor data dictionary.
            stats: Aggregated statistics dictionary.
            file_analysis: File analysis results dictionary.
            thumbnail: Thumbnail metadata dictionary.
            project_data_id: Optional foreign key to project_data table.

        Returns:
            str: The insight_id of the inserted record.
        """
        if analyzed_at is None:
            analyzed_at = datetime.now(timezone.utc)

        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO project_insights (
                    id, project_data_id, project_name, summary, analyzed_at,
                    languages, frameworks, skills, project_type, detection_mode,
                    duration_estimate, contributors, stats, file_analysis, thumbnail
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    insight_id,
                    project_data_id,
                    project_name,
                    summary,
                    analyzed_at,
                    json.dumps(languages or []),
                    json.dumps(frameworks or []),
                    json.dumps(skills or []),
                    project_type,
                    detection_mode,
                    duration_estimate,
                    json.dumps(contributors or {}),
                    json.dumps(stats or {}),
                    json.dumps(file_analysis or {}),
                    json.dumps(thumbnail) if thumbnail else None,
                )
            )
            self.conn.commit()
            return insight_id
        finally:
            cursor.close()

    def fetch_insight_by_id(self, insight_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a project insight by its UUID.

        Args:
            insight_id: The UUID of the insight to retrieve.

        Returns:
            dict | None: The insight data as a dictionary, or None if not found.
        """
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM project_insights WHERE id = %s",
                (insight_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._parse_insight_row(row)
            return None
        finally:
            cursor.close()

    def fetch_all_insights(self, order_by: str = "analyzed_at", ascending: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve all project insights.

        Args:
            order_by: Column to sort by (default: analyzed_at).
            ascending: Sort order (default: True for oldest first).

        Returns:
            list[dict]: List of insight dictionaries.
        """
        direction = "ASC" if ascending else "DESC"
        # Whitelist allowed columns to prevent SQL injection
        allowed_columns = {"analyzed_at", "project_name", "project_type", "created_at"}
        if order_by not in allowed_columns:
            order_by = "analyzed_at"

        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute(
                f"SELECT * FROM project_insights ORDER BY {order_by} {direction}"
            )
            rows = cursor.fetchall()
            return [self._parse_insight_row(row) for row in rows]
        finally:
            cursor.close()

    def update_insight(self, insight_id: str, **kwargs) -> bool:
        """
        Update fields on an existing project insight.

        Args:
            insight_id: The UUID of the insight to update.
            **kwargs: Field names and values to update.

        Returns:
            bool: True if the record was updated, False otherwise.
        """
        if not kwargs:
            return False

        # Fields that should be JSON-encoded
        json_fields = {"languages", "frameworks", "skills", "contributors", "stats", "file_analysis", "thumbnail"}
        
        set_clauses = []
        params = []
        for key, value in kwargs.items():
            if key in json_fields:
                set_clauses.append(f"{key} = %s")
                params.append(json.dumps(value) if value is not None else None)
            else:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        params.append(insight_id)
        sql = f"UPDATE project_insights SET {', '.join(set_clauses)} WHERE id = %s"

        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, tuple(params))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def delete_insight(self, insight_id: str) -> bool:
        """
        Delete a project insight by its UUID.

        Args:
            insight_id: The UUID of the insight to delete.

        Returns:
            bool: True if the record was deleted, False otherwise.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM project_insights WHERE id = %s", (insight_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def _parse_insight_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a raw database row into a properly typed insight dictionary.
        Handles JSON deserialization for relevant fields.

        Args:
            row: Raw row dictionary from cursor.

        Returns:
            dict: Parsed insight dictionary with proper types.
        """
        json_fields = ["languages", "frameworks", "skills", "contributors", "stats", "file_analysis", "thumbnail"]
        result = dict(row)
        
        for field in json_fields:
            if field in result and result[field] is not None:
                if isinstance(result[field], str):
                    try:
                        result[field] = json.loads(result[field])
                    except json.JSONDecodeError:
                        result[field] = {} if field in ("contributors", "stats", "file_analysis", "thumbnail") else []
        
        # Convert datetime objects to ISO strings for consistency
        for dt_field in ["analyzed_at", "created_at", "updated_at"]:
            if dt_field in result and result[dt_field] is not None:
                if isinstance(result[dt_field], datetime):
                    result[dt_field] = result[dt_field].isoformat()
        
        return result

    # =========================================================================
    # USER CONFIG METHODS
    # =========================================================================

    def get_config(self, config_key: str = "user_settings") -> Optional[Dict[str, Any]]:
        """
        Retrieve user configuration by key.

        Args:
            config_key: The configuration key to retrieve (default: 'user_settings').

        Returns:
            dict | None: The configuration value as a dictionary, or None if not found.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT config_value FROM user_config WHERE config_key = %s",
                (config_key,)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return None
        finally:
            cursor.close()

    def save_config(self, config_data: Dict[str, Any], config_key: str = "user_settings") -> bool:
        """
        Save or update user configuration.
        Uses INSERT ... ON DUPLICATE KEY UPDATE for upsert behavior.

        Args:
            config_data: The configuration dictionary to save.
            config_key: The configuration key (default: 'user_settings').

        Returns:
            bool: True if the operation succeeded.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO user_config (config_key, config_value)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE config_value = VALUES(config_value)
                """,
                (config_key, json.dumps(config_data))
            )
            self.conn.commit()
            return True
        except Exception:
            return False
        finally:
            cursor.close()

    def delete_config(self, config_key: str = "user_settings") -> bool:
        """
        Delete a user configuration entry.

        Args:
            config_key: The configuration key to delete.

        Returns:
            bool: True if the record was deleted, False otherwise.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM user_config WHERE config_key = %s", (config_key,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def get_consent_settings(self) -> Dict[str, bool]:
        """
        Retrieve consent settings from user configuration.

        Returns:
            dict: Dictionary with 'external' and 'data_consent' boolean values.
        """
        config = self.get_config("user_settings")
        if config and "consented" in config:
            return {
                "external": config["consented"].get("external", False),
                "data_consent": config["consented"].get("Data consent", False),
            }
        return {"external": False, "data_consent": False}

    def save_consent_settings(self, external_consent: bool, data_consent: bool) -> bool:
        """
        Update consent settings within user configuration.

        Args:
            external_consent: Whether user consents to external services.
            data_consent: Whether user consents to data collection.

        Returns:
            bool: True if the operation succeeded.
        """
        config = self.get_config("user_settings") or {}
        config["consented"] = {
            "external": external_consent,
            "Data consent": data_consent,
        }
        return self.save_config(config, "user_settings")
