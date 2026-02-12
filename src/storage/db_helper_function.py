import json
import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Union


class HelperFunct:
    """
    Handles all database operations for the project_data table.
    Stores and retrieves JSON contents.
    """

    def __init__(self, connection):
        """
        Initialize the HelperFunct with an active MySQL database connection.

        Args:
            connection: An active MySQL connection object that is already connected.

        Returns:
            None: This method initializes the database helper instance.
        """
        if connection is None or not connection.is_connected():
            raise RuntimeError("ProjectDataStore was given an invalid MySQL connection.")
        self.conn = connection


    def insert_json(self, filename: str, data: dict, raw_bytes: bytes = None) -> tuple[str, bool]:
        """
        Insert or update JSON data in the database, storing both the structured JSON
        content and the raw binary representation.

        Args:
            filename: The name of the file associated with the JSON data.
            data: A dictionary representing the JSON content to store.
            raw_bytes: Optional raw byte representation of the JSON content.

        Returns:
            tuple[str, bool]: A tuple containing:
                - The project name (filename) of the inserted/updated record
                - True if this was an update (project existed), False if new insert
        """

        if raw_bytes is None:
            raw_bytes = json.dumps(data).encode("utf-8")

        cursor = self.conn.cursor()
        try:
            # Check if project already exists
            cursor.execute("SELECT 1 FROM project_data WHERE Pname = %s", (filename,))
            was_update = cursor.fetchone() is not None

            project_name = filename

            # Get the current max version for this project
            cursor.execute(
                "SELECT COALESCE(MAX(version_number), 0) FROM project_versions WHERE project_name = %s",
                (project_name,)
            )
            max_version = cursor.fetchone()[0]
            new_version = max_version + 1

            # Use upsert to handle re-analysis of the same project
            # Also update current_version when updating
            cursor.execute(
                "INSERT INTO project_data (Pname, content, file_blob, current_version) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE content = VALUES(content), file_blob = VALUES(file_blob), current_version = %s",
                (filename, json.dumps(data), raw_bytes, new_version, new_version)
            )

            cursor.execute(
                "INSERT INTO project_versions (project_name, version_number, content, file_blob) "
                "VALUES (%s, %s, %s, %s)",
                (project_name, new_version, json.dumps(data), raw_bytes)
            )
            self.conn.commit()

            return project_name, was_update
        finally:
            cursor.close()

            # fetch

            # returns the contents of the json file by name
    def fetch_by_name(self, project_name: str):
        """
        Retrieve JSON content from the database using a project_name.

        Args:
           project_name: The unique project_name of the record to retrieve.

        Returns:
            dict | None: The parsed JSON content as a dictionary if found,
            or None if no matching record exists.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content FROM project_data WHERE Pname = %s", (project_name,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            cursor.close()

            # returns the blob file by name
    def fetch_file_blob_by_name(self, project_name: str) -> bytes:
        """
        Retrieve the raw binary file blob from the database using a project name.

        Args:
            project_name: The unique project name of the record to retrieve.

        Returns:
            bytes | None: The raw file blob if found, or None if the record
            does not exist.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT file_blob FROM project_data WHERE Pname = %s", (project_name,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()

            # returns all content
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

    def update(self, project_name: str, input: Union[dict, bytes]) -> bool:
            """
            Update an existing project with new content. The old version is 
            automatically saved to the versions table.

            Args:
                project_name: The project name to update.
                input: Either a dictionary containing JSON data or raw JSON bytes.

            Returns:
                bool: True if the record was successfully updated, False otherwise.
            """
            # Parse input
            if isinstance(input, dict):
                content = input
                blob = json.dumps(input).encode("utf-8")
            elif isinstance(input, bytes):
                blob = input
                content = json.loads(input.decode("utf-8"))
            else:
                raise ValueError("input must be a dict or bytes")

            cursor = self.conn.cursor()
            try:
                # Get current version
                cursor.execute(
                    "SELECT current_version FROM project_data WHERE Pname=%s FOR UPDATE", 
                    (project_name,)
                )
                row = cursor.fetchone()
                if not row:
                    return False
        
                new_version = row[0] + 1

                # Update project_data
                cursor.execute(
                    "UPDATE project_data SET content=%s, file_blob=%s, current_version=%s WHERE Pname=%s",
                    (json.dumps(content), blob, new_version, project_name)
                    )

                # Save new version
                cursor.execute(
                    "INSERT INTO project_versions (project_name, version_number, content, file_blob) "
                    "VALUES (%s, %s, %s, %s)",
                    (project_name, new_version, json.dumps(content), blob)
                    )

                self.conn.commit()
                return True
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
                "SELECT COUNT(*) FROM project_data WHERE Pname = %s",
                (filename,),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        finally:
            cursor.close()
            
        # Delete
    def delete(self, project_name: str) -> bool:
        """
        Delete a database record by its project name.

        Args:
            project_name: The unique project name of the record to delete.

        Returns:
            bool: True if the record was successfully deleted, False otherwise.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM project_data WHERE Pname = %s", (project_name,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def get_version_list(self, project_name: str) -> List[Dict]:
        """
        Get a simple list of all versions for display to the user.
        Perfect for showing a selection menu.

        Args:
            project_name: The unique prject name
        Returns:
            list: A list of dictionaries containing:
                - version_number: The version number
                - filename: Filename at that version
                - created_at: Timestamp when version was created
                - is_current: Whether this is the current active version
            
            Ordered from newest to oldest.
        
        Example:
            versions = helper.get_version_list(5)
            for v in versions:
                status = "(Current)" if v['is_current'] else ""
                print(f"Version {v['version_number']}: {v['filename']} - {v['created_at']} {status}")
        """
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    pv.version_number,
                    pv.created_at,
                    CASE 
                        WHEN pv.version_number = pd.current_version THEN TRUE
                        ELSE FALSE
                    END as is_current
                FROM project_versions pv
                JOIN project_data pd ON pv.project_name = pd.Pname
                WHERE pv.project_name = %s
                ORDER BY pv.version_number DESC
            """, (project_name,))
            
            versions = cursor.fetchall()
            
            # Convert is_current to boolean
            for version in versions:
                version['is_current'] = bool(version['is_current'])
                
            return versions
        finally:
            cursor.close()

    def retrieve_selected_version(self, project_name: str, version_number: int) -> Dict | None:
        """
        Retrieve the full data for a user-selected version.
        Returns everything needed to display or work with that version.

        Args:
            project_id: The unique database ID of the project.
            version_number: The version number the user selected.

        Returns:
            dict | None: A dictionary containing:
                - version_number: The version number
                - filename: Filename at that version
                - content: Parsed JSON content (dict)
                - file_blob: Raw binary data (bytes)
                - created_at: Timestamp when version was created
            Returns None if version doesn't exist.
        
        Example:
            selected = helper.retrieve_selected_version(5, 3)
            if selected:
                print(f"Loaded: {selected['filename']}")
                analysis_data = selected['content']
                raw_file = selected['file_blob']
        """
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    version_number,
                    content,
                    file_blob,
                    created_at
                FROM project_versions
                WHERE project_name = %s AND version_number = %s
            """, (project_name, version_number))
            
            version = cursor.fetchone()
            
            if version:
                # Parse the JSON content
                version['content'] = json.loads(version['content'])
                
            return version
        finally:
            cursor.close()

    def get_all_projects_with_versions(self) -> List[Dict]:
        """
        Get a list of all projects showing their version counts.
        Useful for displaying a master list of all projects.

        Args:
            None

        Returns:
            list: A list of dictionaries containing:
                - project_name: The project name 
                - current_version: Current version number 
                - current_version: Current version number
                - total_versions: Total number of saved versions
                - uploaded_at: When project was first created
                - updated_at: When project was last updated
        
        Example:
            projects = helper.get_all_projects_with_versions()
            for p in projects:
                print(f"{p['filename']}: Version {p['current_version']} ({p['total_versions']} total versions)")
        """
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    pd.Pname as project_name,
                    pd.current_version,
                    pd.uploaded_at,
                    pd.updated_at,
                    COUNT(pv.id) as total_versions
                FROM project_data pd
                LEFT JOIN project_versions pv ON pd.Pname = pv.project_name
                GROUP BY pd.Pname
                ORDER BY pd.updated_at DESC
            """)
            
            return cursor.fetchall()
        finally:
            cursor.close()
    
    def project_exists(self, project_name: str) -> bool:
        """
        Check if a project exists in the database.
    
        Args:
            project_name: The project name to check.
    
        Returns:
            bool: True if the project exists, False otherwise.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM project_data WHERE Pname = %s", (project_name,))
            return cursor.fetchone() is not None
        finally:
            cursor.close()
        
    def list_all_projects(self) -> List[str]:
        """
        Get a list of all project names in the database.
    
        Returns:
            list: A list of all project names.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT Pname FROM project_data ORDER BY updated_at DESC")
            return [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()

    def delete_old_versions(self, project_name: str, keep_last_n: int = 5) -> int:
        """
        Delete old versions, keeping only the most recent N versions.
    
        Args:
            project_name: The project name.
            keep_last_n: Number of recent versions to keep (default: 5).
    
        Returns:
            int: Number of versions deleted.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM project_versions
                WHERE project_name = %s
                AND version_number NOT IN (
                    SELECT version_number FROM (
                        SELECT version_number
                        FROM project_versions
                        WHERE project_name = %s
                        ORDER BY version_number DESC
                        LIMIT %s
                    ) as keep_versions
                )
            """, (project_name, project_name, keep_last_n))
        
            self.conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()