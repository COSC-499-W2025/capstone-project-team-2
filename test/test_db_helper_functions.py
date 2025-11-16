import unittest
import json
import os
import tempfile
import mysql.connector
from src.db_helper_function import HelperFunct


# set up

class TestHelperFunct(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a single MySQL connection and store object."""
        cls.conn = mysql.connector.connect(
            host="app_database",         
            port=3306,
            database="appdb",
            user="appuser",
            password="apppassword"
        )
        cls.store = HelperFunct(cls.conn)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def setUp(self):
        """Clean DB before each test."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_data;")
        self.conn.commit()
        cursor.close()

# Tests

    def test_insert_json_and_fetch_by_id(self):
        data = {"name": "alpha", "value": 123}
        row_id = self.store.insert_json("alpha.json", data)
        pulled = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled, data)

    def test_insert_json_file_with_blob(self):
        # Create temporary JSON file
        json_content = {"project": "demo", "ok": True}
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            f.write(json.dumps(json_content).encode("utf-8"))
            temp_path = f.name

        row_id = self.store.insert_json_file_with_blob(temp_path)

        # Test content column
        pulled_dict = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled_dict, json_content)

        # Test file_blob column
        pulled_bytes = self.store.fetch_file_blob_by_id(row_id)
        with open(temp_path, "rb") as f:
            original_bytes = f.read()
        self.assertEqual(pulled_bytes, original_bytes)

        os.remove(temp_path)

    def test_fetch_all(self):
        self.store.insert_json("a.json", {"a": 1})
        self.store.insert_json("b.json", {"b": 2})
        all_rows = self.store.fetch_all()
        self.assertIn({"a": 1}, all_rows)
        self.assertIn({"b": 2}, all_rows)
        self.assertEqual(len(all_rows), 2)

    def test_update_content(self):
        row_id = self.store.insert_json("up.json", {"before": True})
        updated = self.store.update(row_id, {"after": True})
        self.assertTrue(updated)
        pulled = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled, {"after": True})

    def test_delete_row(self):
        row_id = self.store.insert_json("delete.json", {"exists": True})
        deleted = self.store.delete(row_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.store.fetch_by_id(row_id))

