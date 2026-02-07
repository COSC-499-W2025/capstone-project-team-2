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
            "INSERT INTO project_data (Pname, content, file_blob) VALUES (%s, %s, %s)",
            (filename, json.dumps(data), raw_bytes)
            )

            project_name = filename

            cursor.execute(
                "INSERT INTO project_versions (project_name, version_number, content, file_blob) "
                "VALUES (%s, 1, %s, %s)",
                (project_name, filename, json.dumps(data), raw_bytes)
            )
            self.conn.commit()
            
            return project_name
        finally:
            cursor.close()


            # fetch

            # returns the contents of the json file by ID
    def fetch_by_id(self, row_id: int):
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
            cursor.execute("SELECT content FROM project_data WHERE Pname = %s", (row_id,))
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

        # Update, update all content and json file info
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

        cursor = self.conn.cursor()

        try:
            # Get current version
            cursor.execute(
                "SELECT current_version, filename FROM project_data WHERE id=%s FOR UPDATE", (row_id,)
            )
            row = cursor.fetchone()
            if not row:
                return False
            current_version, old_filename = row
            new_version = current_version + 1

            # Update project_data with new content
            sql = "UPDATE project_data SET content=%s, file_blob=%s, current_version=%s"
            params = [json.dumps(content), blob, new_version]

            if filename is not None:
                sql += ", filename=%s"
                params.append(filename)

            sql += " WHERE id=%s"
            params.append(row_id)

            cursor.execute(sql, tuple(params))

            # Insert new version into project_versions
            cursor.execute(
                "INSERT INTO project_versions (project_id, version_number, filename, content, file_blob) "
                "VALUES (%s, %s, %s, %s, %s)",
                (row_id, new_version, filename or old_filename, json.dumps(content), blob)
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