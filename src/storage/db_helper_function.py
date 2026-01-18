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

            # returns the blob file by ID
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