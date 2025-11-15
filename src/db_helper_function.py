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


    def insert_Json(self, filepath:str) -> int:
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