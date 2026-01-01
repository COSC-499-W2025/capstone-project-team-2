import json
import mysql.connector
from mysql.connector import Error
from typing import Union


class HelperFunct:
    """
    Handles all database operations for the project_data table.
    Stores and retrieves JSON contents.
    """

    def __init__(self, connection):
        if connection is None or not connection.is_connected():
            raise RuntimeError("ProjectDataStore was given an invalid MySQL connection.")
        self.conn = connection


    def insert_json(self, filename: str, data: dict, raw_bytes: bytes = None) -> int:
        """
        Insert JSON data into DB, storing both content and blob.
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


            # fetch

            # returns the contents of the json file by ID
    def fetch_by_id(self, row_id: int):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT content FROM project_data WHERE id = %s", (row_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
        finally:
            cursor.close()

            # returns the blob file by ID
    def fetch_file_blob_by_id(self, row_id: int) -> bytes:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT file_blob FROM project_data WHERE id = %s", (row_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            cursor.close()

            # returns all content
    def fetch_all(self):
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
        Update both content and file_blob so they always match.

        Args:
            input: Python dict or raw JSON bytes.
            filename: Optional new filename.

        Returns:
            True if row updated, False otherwise.
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


        # Delete
        
    def count_file_references(self, filename: str) -> int:
        """
        Count how many records in project_data reference a given filename.
        Returns the number of rows referencing the filename.
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
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM project_data WHERE id = %s", (row_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()