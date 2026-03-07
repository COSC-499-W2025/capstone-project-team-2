import unittest
import json
import tempfile
from pathlib import Path
import sqlite3
import sys
import os


# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from src.storage.db_helper_function import HelperFunct


"""
For testing output should reflect the following 

time="2025-11-15T17:18:48-08:00" level=warning msg="The \"DISPLAY\" variable is not set. Defaulting to a blank string." 
[+] Running 1/1 ✔ Container app_database Started 0.6s ...... 
---------------------------------------------------------------------- 
Ran 6 tests in 0.302s v View in Docker Desktop o View Config w Enable Watch 
OK

"""


class TestHelperFunct(unittest.TestCase):
    """
    Unit test suite for validating database operations performed by the
    HelperFunct class, including insert, fetch, update, and delete behavior
    against a SQLite-backed project_data table.
    """
    

    @classmethod
    def setUpClass(cls):
        """
        utilize SQLite database connection and HelperFunct instance
        used across all tests in this test suite.

        Args:
            None: This class method does not take any parameters.

        Returns:
            None: Initializes shared database resources for the test class.
        """
       cls.conn = sqlite3.connect(":memory:")
      schema_path = os.path.join(os.path.dirname(__file__), "..", "database.sql")
      with open(schema_path) as  f:
          cls.conn.executescript(f.read())
       cls.conn.row_factory = sqlite3.Row
       cls.store = HelperFunct(cls.conn)
          
      
        cls.store = HelperFunct(cls.conn)

    @classmethod
    def tearDownClass(cls):
        """
        Close the SQLite database connection after all tests have run.

        Args:
            None: This class method does not take any parameters.

        Returns:
            None: Cleans up shared database resources.
        """
        cls.conn.close()

    def setUp(self):
        """
        Reset the project_data table to a clean state before each test runs.

        Args:
            None: This method does not take any parameters.

        Returns:
            None: Ensures each test runs with an empty database table.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_data;")
        self.conn.commit()
        cursor.close()

    # -------------------- Insert & Fetch --------------------
    def test_insert_json_dict_and_fetch_by_name(self):
        """
        Verify that inserting JSON content as a dictionary and fetching it
        by row ID returns the correct structured data and matching binary blob.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        data = {"name": "alpha", "value": 123}
        project_name, _ = self.store.insert_json("alpha.json", data)
        pulled = self.store.fetch_by_name(project_name)
        self.assertEqual(pulled, data)

        # Blob should match serialized dict
        pulled_bytes = self.store.fetch_file_blob_by_name(project_name)
        self.assertEqual(pulled_bytes, json.dumps(data).encode("utf-8"))

    def test_insert_json_bytes_and_fetch_by_name(self):
        """
        Verify that inserting raw JSON bytes results in synchronized content
        and file blob storage that can be correctly retrieved.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        data = {"project": "demo", "ok": True}
        raw_bytes = json.dumps(data).encode("utf-8")
        project_name, _ = self.store.insert_json("demo.json", data, raw_bytes=raw_bytes)

        # Fetch content
        pulled_dict = self.store.fetch_by_name(project_name)
        self.assertEqual(pulled_dict, data)

        # Fetch blob
        pulled_bytes = self.store.fetch_file_blob_by_name(project_name)
        self.assertEqual(pulled_bytes, raw_bytes)

    def test_fetch_all(self):
        """
        Verify that multiple inserted records can be retrieved using the
        fetch_all method and that all stored JSON entries are returned.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        self.store.insert_json("a.json", {"a": 1})
        self.store.insert_json("b.json", {"b": 2})
        all_rows = self.store.fetch_all()
        self.assertIn({"a": 1}, all_rows)
        self.assertIn({"b": 2}, all_rows)
        self.assertEqual(len(all_rows), 2)

    # -------------------- Update --------------------
    def test_update_with_dict(self):
        """
        Verify that updating a database record using a dictionary correctly
        updates both the JSON content and binary blob fields.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_name, _ = self.store.insert_json("up.json", {"before": True})
        updated = self.store.update(project_name, {"after": True})
        self.assertTrue(updated)

        # Check content and blob
        pulled = self.store.fetch_by_name(project_name)
        self.assertEqual(pulled, {"after": True})
        pulled_blob = self.store.fetch_file_blob_by_name(project_name)
        self.assertEqual(pulled_blob, json.dumps({"after": True}).encode("utf-8"))

    def test_update_with_bytes(self):
        """
        Verify that updating a database record using raw JSON bytes correctly
        synchronizes the stored content and binary blob.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_name, _ = self.store.insert_json("up.json", {"before": True})
        new_data = {"updated": 42}
        new_bytes = json.dumps(new_data).encode("utf-8")
        updated = self.store.update(project_name, new_bytes)
        self.assertTrue(updated)

        pulled = self.store.fetch_by_name(project_name)
        self.assertEqual(pulled, new_data)
        pulled_blob = self.store.fetch_file_blob_by_name(project_name)
        self.assertEqual(pulled_blob, new_bytes)

    # -------------------- Delete --------------------
    def test_delete_row(self):
        """
        Verify that deleting a database record removes both its JSON content
        and associated binary blob from the database.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_name, _ = self.store.insert_json("delete.json", {"exists": True})
        deleted = self.store.delete(project_name)
        self.assertTrue(deleted)
        self.assertIsNone(self.store.fetch_by_name(project_name))
        self.assertIsNone(self.store.fetch_file_blob_by_name(project_name))


    # Project exists 

    def test_project_exists(self):
        """
        Verify that project_exists correctly identifies whether a project
        is present in the database.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        self.assertFalse(self.store.project_exists("nonexist.json"))
    
        # Insert a project
        project_name, _ = self.store.insert_json("exist.json", {"data": 1})
        self.assertTrue(self.store.project_exists(project_name))
    
        self.store.delete(project_name)
        self.assertFalse(self.store.project_exists(project_name))

    def test_list_all_projects(self):
        """
        Verify that list_all_projects returns all project names in the database,
        ordered by most recently updated first.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        projects = self.store.list_all_projects()
        self.assertEqual(projects, [])
    
        # Insert multiple projects
        self.store.insert_json("project1.json", {"data": 1})
        self.store.insert_json("project2.json", {"data": 2})
        self.store.insert_json("project3.json", {"data": 3})
    
        # return
        projects = self.store.list_all_projects()
        self.assertEqual(len(projects), 3)
        self.assertIn("project1.json", projects)
        self.assertIn("project2.json", projects)
        self.assertIn("project3.json", projects)
        
        self.store.update("project1.json", {"data": 100})
        projects = self.store.list_all_projects()
        self.assertEqual(projects[0], "project1.json")

    def test_delete_old_versions(self):
        """
        Verify that delete_old_versions keeps only the most recent N versions
        and removes older versions from the database.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create a project with multiple versions
        project_name, _ = self.store.insert_json("versioned.json", {"version": 1})
        self.store.update(project_name, {"version": 2})
        self.store.update(project_name, {"version": 3})
        self.store.update(project_name, {"version": 4})
        self.store.update(project_name, {"version": 5})
        self.store.update(project_name, {"version": 6})
        self.store.update(project_name, {"version": 7})
        versions = self.store.get_version_list(project_name)
        self.assertEqual(len(versions), 7)
    
        # Keep only last 3 versions
        deleted_count = self.store.delete_old_versions(project_name, keep_last_n=3)
        self.assertEqual(deleted_count, 4)
        versions = self.store.get_version_list(project_name)
        self.assertEqual(len(versions), 3)
    
        version_numbers = [v['version_number'] for v in versions]
        self.assertEqual(sorted(version_numbers), [5, 6, 7])
    
        # retrieve versions
        v5 = self.store.retrieve_selected_version(project_name, 5)
        v7 = self.store.retrieve_selected_version(project_name, 7)
        self.assertIsNotNone(v5)
        self.assertIsNotNone(v7)
        self.assertEqual(v5['content'], {"version": 5})
        self.assertEqual(v7['content'], {"version": 7})
    
        # Old versions removed
        v1 = self.store.retrieve_selected_version(project_name, 1)
        v2 = self.store.retrieve_selected_version(project_name, 2)
        self.assertIsNone(v1)
        self.assertIsNone(v2)

if __name__== "__main__":
    unittest.main()
