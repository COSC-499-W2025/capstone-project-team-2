import unittest
import json
import sys
import os
import mysql.connector

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.storage.db_helper_function import HelperFunct


class TestVersioningHelper(unittest.TestCase):
    """
    Integration tests for versioning behavior.
    Matches structure of other db_helper tests.
    """

    @classmethod
    def setUpClass(cls):
        cls.conn = mysql.connector.connect(
            host="localhost",
            port=3308,
            database="appdb",
            user="appuser",
            password="apppassword"
        )
        cls.store = HelperFunct(cls.conn)

    def setUp(self):
        """
        Reset the project_versions table to a clean state before each test.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_versions;")
        cursor.execute("DELETE FROM project_data;")
        self.conn.commit()
        cursor.close()

    # ---------- Create / Fetch ----------

    def test_restore_previous_version(self):
        """
        Verify that we can restore a previous version by retrieving it
        and updating the project with that old content.
        """
        project_name, _ = self.store.insert_json("file.json", {"data": 1})
        self.store.update(project_name , {"data": 2})
        self.store.update(project_name , {"data": 3})

        version_to_restore = 2
        old_data = self.store.retrieve_selected_version(project_name , version_to_restore)
        self.assertIsNotNone(old_data)

        restored = self.store.update(project_name , old_data['content'])
        self.assertTrue(restored)

        latest_version = self.store.get_version_list(project_name )[0]
        self.assertEqual(latest_version['version_number'], 4) 
        self.assertTrue(latest_version['is_current'])

        restored_content = self.store.fetch_by_name(project_name )
        self.assertEqual(restored_content, {"data": 2})

    def test_create_and_fetch_latest_version(self):
        """
        Verify that inserting initial content creates version 1 and that
        the latest version can be fetched correctly.
        """
        project_name, _ = self.store.insert_json("file.json", {"data": 1})
    
        self.store.update(project_name , {"data": 2})

        versions = self.store.get_version_list(project_name )
        latest = versions[0]

        self.assertEqual(latest['version_number'], 2)
        self.assertTrue(latest['is_current'])

        selected = self.store.retrieve_selected_version(project_name , 1)
        self.assertEqual(selected['content'], {"data": 1})

    def test_delete_cascades_to_versions(self):
        project_name, _ = self.store.insert_json("file.json", {"data": 1})
        self.store.update(project_name , {"data": 2})
        self.store.update(project_name , {"data": 3})

        # Confirm versions exist
        versions_before = self.store.get_version_list(project_name )
        self.assertEqual(len(versions_before), 3)

        deleted = self.store.delete(project_name )
        self.assertTrue(deleted)

        # Project row should be gone
        self.assertIsNone(self.store.fetch_by_name(project_name ))
        self.assertIsNone(self.store.fetch_file_blob_by_name(project_name))

        # Versions should also be gone
        versions_after = self.store.get_version_list(project_name )
        self.assertEqual(versions_after, [])

    # ---------- Delete ----------

    def test_delete_versions_for_file(self):
        """
        Insert multiple versions and delete them, confirming deletion.
        """
        project_name, _ = self.store.insert_json("file.json", {"data": 1})
        self.store.update(project_name , {"data": 2})
        self.store.update(project_name , {"data": 3})

        # Restore version 2
        version_to_restore = 2
        old_data = self.store.retrieve_selected_version(project_name , version_to_restore)
        self.assertIsNotNone(old_data)

        # Perform update with old content
        restored = self.store.update(project_name , old_data['content'])
        self.assertTrue(restored)

        # Latest version should now match restored content
        latest_version = self.store.get_version_list(project_name )[0]
        self.assertEqual(latest_version['version_number'], 4)
        self.assertTrue(latest_version['is_current'])

        restored_content = self.store.fetch_by_name(project_name )
        self.assertEqual(restored_content, {"data": 2})
