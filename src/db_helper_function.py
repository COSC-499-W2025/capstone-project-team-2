import json
import mysql.connector
from mysql.connector import Error

class HelperFunct:
    """
    Handles all database operations for the project_data table.
    Stores and retrieves JSON contents.
    """

    def __init__(self, connection):
        if connection is None or not connection.is_connected():
            raise RuntimeError("ProjectDataStore was given an invalid MySQL connection.")
        self.conn = connection


    def insert_json(self, filepath:str) -> int:
        """
        Insert a JSON file into the database, storing both:
        1. The dictionary content in the 'content' column.
        2. The raw file bytes in the 'file_blob' column.
        """ 
        # Load JSON content as dictionary 
        with open(filepath, "r") as f:
            data_dict = json.load(f)

        # Read raw bytes of the same file
        with open(filepath, "rb") as f:
            file_bytes = f.read()

        # Extract only the filename
        filename = filepath.split("/")[-1]

        # Insert into database
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO project_data (filename, content, file_blob) VALUES (%s, %s, %s)",
                (filename, json.dumps(data_dict), file_bytes)
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
    def update(self, row_id: int, new_content: dict) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "UPDATE project_data SET content = %s WHERE id = %s",
                (json.dumps(new_content), row_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()

        # Delete
    def delete(self, row_id: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM project_data WHERE id = %s", (row_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()