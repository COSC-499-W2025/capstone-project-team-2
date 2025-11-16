import unittest
import json
import tempfile
from pathlib import Path
import mysql.connector
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.db_helper_function import HelperFunct


class TestHelperFunct(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a single MySQL connection and HelperFunct instance."""
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
        """Clean the table before each test."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_data;")
        self.conn.commit()
        cursor.close()

    # -------------------- Insert & Fetch --------------------
    def test_insert_json_dict_and_fetch_by_id(self):
        """Insert a dict and fetch by ID."""
        data = {"name": "alpha", "value": 123}
        row_id = self.store.insert_json("alpha.json", data)
        pulled = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled, data)

        # Blob should match serialized dict
        pulled_bytes = self.store.fetch_file_blob_by_id(row_id)
        self.assertEqual(pulled_bytes, json.dumps(data).encode("utf-8"))

    def test_insert_json_bytes_and_fetch_by_id(self):
        """Insert raw bytes and ensure content and blob are synced."""
        data = {"project": "demo", "ok": True}
        raw_bytes = json.dumps(data).encode("utf-8")
        row_id = self.store.insert_json("demo.json", data, raw_bytes=raw_bytes)

        # Fetch content
        pulled_dict = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled_dict, data)

        # Fetch blob
        pulled_bytes = self.store.fetch_file_blob_by_id(row_id)
        self.assertEqual(pulled_bytes, raw_bytes)

    def test_fetch_all(self):
        """Insert multiple rows and fetch all."""
        self.store.insert_json("a.json", {"a": 1})
        self.store.insert_json("b.json", {"b": 2})
        all_rows = self.store.fetch_all()
        self.assertIn({"a": 1}, all_rows)
        self.assertIn({"b": 2}, all_rows)
        self.assertEqual(len(all_rows), 2)

    # -------------------- Update --------------------
    def test_update_with_dict(self):
        """Update a row using a dict; content and blob should match."""
        row_id = self.store.insert_json("up.json", {"before": True})
        updated = self.store.update(row_id, {"after": True})
        self.assertTrue(updated)

        # Check content and blob
        pulled = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled, {"after": True})
        pulled_blob = self.store.fetch_file_blob_by_id(row_id)
        self.assertEqual(pulled_blob, json.dumps({"after": True}).encode("utf-8"))

    def test_update_with_bytes(self):
        """Update a row using raw bytes; content and blob should match."""
        row_id = self.store.insert_json("up.json", {"before": True})
        new_data = {"updated": 42}
        new_bytes = json.dumps(new_data).encode("utf-8")
        updated = self.store.update(row_id, new_bytes)
        self.assertTrue(updated)

        pulled = self.store.fetch_by_id(row_id)
        self.assertEqual(pulled, new_data)
        pulled_blob = self.store.fetch_file_blob_by_id(row_id)
        self.assertEqual(pulled_blob, new_bytes)

    # -------------------- Delete --------------------
    def test_delete_row(self):
        """Insert a row and then delete it."""
        row_id = self.store.insert_json("delete.json", {"exists": True})
        deleted = self.store.delete(row_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.store.fetch_by_id(row_id))
        self.assertIsNone(self.store.fetch_file_blob_by_id(row_id))


if __name__== "__main__":
    unittest.main()
