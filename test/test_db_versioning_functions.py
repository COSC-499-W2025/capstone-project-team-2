import unittest
import json
import mysql.connector
from helper_funct import HelperFunct


class TestVersioningFunctionality(unittest.TestCase):
    """
    Unit test suite for validating versioning operations performed by the
    HelperFunct class, including version creation, retrieval, restoration,
    and cleanup operations against a MySQL-backed database.
    """

    @classmethod
    def setUpClass(cls):
        """
        Create a shared MySQL database connection and HelperFunct instance
        used across all tests in this test suite.

        Args:
            None: This class method does not take any parameters.

        Returns:
            None: Initializes shared database resources for the test class.
        """
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
        """
        Close the shared MySQL database connection after all tests have run.

        Args:
            None: This class method does not take any parameters.

        Returns:
            None: Cleans up shared database resources.
        """
        cls.conn.close()

    def setUp(self):
        """
        Reset both project_data and project_versions tables to a clean state
        before each test runs.

        Args:
            None: This method does not take any parameters.

        Returns:
            None: Ensures each test runs with empty database tables.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_versions;")
        cursor.execute("DELETE FROM project_data;")
        self.conn.commit()
        cursor.close()

    def tearDown(self):
        """
        Clean up after each test by removing any test data created.

        Args:
            None: This method does not take any parameters.

        Returns:
            None: Ensures no test data persists between tests.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM project_versions;")
        cursor.execute("DELETE FROM project_data;")
        self.conn.commit()
        cursor.close()

    # -------------------- Version Creation --------------------

    def test_insert_creates_version_1(self):
        """
        Verify that inserting a new project automatically creates version 1
        in the project_versions table.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        data = {"project": "test", "status": "new"}
        project_id = self.store.insert_json("test.json", data)
        
        # Verify version 1 exists
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]['version_number'], 1)
        self.assertTrue(versions[0]['is_current'])
        self.assertEqual(versions[0]['filename'], "test.json")

    def test_update_creates_new_version(self):
        """
        Verify that updating a project saves the old state as a version and
        increments the version number.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Insert initial project
        data_v1 = {"version": 1, "data": "original"}
        project_id = self.store.insert_json("update.json", data_v1)
        
        # Update to create version 2
        data_v2 = {"version": 2, "data": "updated"}
        updated = self.store.update(project_id, data_v2)
        self.assertTrue(updated)
        
        # Verify we have 2 versions
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 2)
        
        # Verify version 2 is current
        self.assertEqual(versions[0]['version_number'], 2)
        self.assertTrue(versions[0]['is_current'])
        
        # Verify version 1 is historical
        self.assertEqual(versions[1]['version_number'], 1)
        self.assertFalse(versions[1]['is_current'])

    def test_multiple_updates_create_version_chain(self):
        """
        Verify that multiple updates create a proper version history chain.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create project and update 3 times
        project_id = self.store.insert_json("chain.json", {"v": 1})
        self.store.update(project_id, {"v": 2})
        self.store.update(project_id, {"v": 3})
        self.store.update(project_id, {"v": 4})
        
        # Should have 4 versions
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 4)
        
        # Verify ordering (newest first)
        self.assertEqual(versions[0]['version_number'], 4)
        self.assertEqual(versions[1]['version_number'], 3)
        self.assertEqual(versions[2]['version_number'], 2)
        self.assertEqual(versions[3]['version_number'], 1)

    # -------------------- Get Version List --------------------

    def test_get_version_list_returns_correct_structure(self):
        """
        Verify that get_version_list returns all required fields with
        correct data types.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("structure.json", {"test": True})
        self.store.update(project_id, {"test": False})
        
        versions = self.store.get_version_list(project_id)
        
        # Verify structure of each version
        for v in versions:
            self.assertIn('version_number', v)
            self.assertIn('filename', v)
            self.assertIn('created_at', v)
            self.assertIn('is_current', v)
            
            # Verify types
            self.assertIsInstance(v['version_number'], int)
            self.assertIsInstance(v['filename'], str)
            self.assertIsInstance(v['is_current'], bool)

    def test_get_version_list_only_one_current(self):
        """
        Verify that only one version is marked as current regardless of
        how many versions exist.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("current.json", {"v": 1})
        self.store.update(project_id, {"v": 2})
        self.store.update(project_id, {"v": 3})
        
        versions = self.store.get_version_list(project_id)
        current_count = sum(1 for v in versions if v['is_current'])
        
        self.assertEqual(current_count, 1)
        # The first in list (newest) should be current
        self.assertTrue(versions[0]['is_current'])

    def test_get_version_list_empty_for_nonexistent_project(self):
        """
        Verify that get_version_list returns an empty list for a project
        that doesn't exist.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        versions = self.store.get_version_list(99999)
        self.assertEqual(versions, [])

    # -------------------- Retrieve Selected Version --------------------

    def test_retrieve_selected_version_gets_correct_data(self):
        """
        Verify that retrieve_selected_version returns the correct data
        for a specific version number.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create 3 distinct versions
        data_v1 = {"name": "alpha", "score": 10}
        data_v2 = {"name": "beta", "score": 20}
        data_v3 = {"name": "gamma", "score": 30}
        
        project_id = self.store.insert_json("retrieve.json", data_v1)
        self.store.update(project_id, data_v2)
        self.store.update(project_id, data_v3)
        
        # Retrieve version 2
        v2 = self.store.retrieve_selected_version(project_id, 2)
        
        self.assertIsNotNone(v2)
        self.assertEqual(v2['version_number'], 2)
        self.assertEqual(v2['content'], data_v2)
        self.assertEqual(v2['filename'], "retrieve.json")

    def test_retrieve_selected_version_returns_all_fields(self):
        """
        Verify that retrieve_selected_version returns all required fields.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("fields.json", {"data": True})
        version = self.store.retrieve_selected_version(project_id, 1)
        
        self.assertIn('version_number', version)
        self.assertIn('filename', version)
        self.assertIn('content', version)
        self.assertIn('file_blob', version)
        self.assertIn('created_at', version)

    def test_retrieve_selected_version_returns_none_for_invalid(self):
        """
        Verify that retrieve_selected_version returns None for non-existent
        versions.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("invalid.json", {"test": True})
        
        # Try to get version that doesn't exist
        result = self.store.retrieve_selected_version(project_id, 99)
        self.assertIsNone(result)
        
        # Try with invalid project_id
        result = self.store.retrieve_selected_version(99999, 1)
        self.assertIsNone(result)

    # -------------------- Fetch Version Content/Blob --------------------

    def test_fetch_version_content_by_number(self):
        """
        Verify that fetch_version_content_by_number returns just the
        parsed JSON content for a specific version.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        data_v1 = {"stage": "alpha"}
        data_v2 = {"stage": "beta"}
        
        project_id = self.store.insert_json("content.json", data_v1)
        self.store.update(project_id, data_v2)
        
        # Get version 1 content
        content = self.store.fetch_version_content_by_number(project_id, 1)
        self.assertEqual(content, data_v1)
        
        # Get version 2 content
        content = self.store.fetch_version_content_by_number(project_id, 2)
        self.assertEqual(content, data_v2)

    def test_fetch_version_blob_by_number(self):
        """
        Verify that fetch_version_blob_by_number returns the raw binary
        data for a specific version.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        data = {"blob": "test"}
        expected_blob = json.dumps(data).encode("utf-8")
        
        project_id = self.store.insert_json("blob.json", data)
        
        blob = self.store.fetch_version_blob_by_number(project_id, 1)
        self.assertEqual(blob, expected_blob)

    def test_fetch_version_methods_return_none_for_invalid(self):
        """
        Verify that version fetch methods return None for non-existent versions.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("none.json", {"test": True})
        
        content = self.store.fetch_version_content_by_number(project_id, 99)
        self.assertIsNone(content)
        
        blob = self.store.fetch_version_blob_by_number(project_id, 99)
        self.assertIsNone(blob)

    # -------------------- Get All Projects With Versions --------------------

    def test_get_all_projects_with_versions(self):
        """
        Verify that get_all_projects_with_versions returns all projects
        with their version counts.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create 3 projects with different version counts
        p1 = self.store.insert_json("p1.json", {"p": 1})
        
        p2 = self.store.insert_json("p2.json", {"p": 2})
        self.store.update(p2, {"p": 2.1})
        
        p3 = self.store.insert_json("p3.json", {"p": 3})
        self.store.update(p3, {"p": 3.1})
        self.store.update(p3, {"p": 3.2})
        
        projects = self.store.get_all_projects_with_versions()
        
        # Should have exactly 3 projects
        self.assertEqual(len(projects), 3)
        
        # Find our projects
        p1_data = next((p for p in projects if p['project_id'] == p1), None)
        p2_data = next((p for p in projects if p['project_id'] == p2), None)
        p3_data = next((p for p in projects if p['project_id'] == p3), None)
        
        # Verify version counts
        self.assertEqual(p1_data['total_versions'], 1)
        self.assertEqual(p2_data['total_versions'], 2)
        self.assertEqual(p3_data['total_versions'], 3)

    def test_get_all_projects_returns_correct_structure(self):
        """
        Verify that get_all_projects_with_versions returns all required fields.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        self.store.insert_json("structure.json", {"test": True})
        projects = self.store.get_all_projects_with_versions()
        
        self.assertGreater(len(projects), 0)
        
        project = projects[0]
        self.assertIn('project_id', project)
        self.assertIn('filename', project)
        self.assertIn('current_version', project)
        self.assertIn('total_versions', project)
        self.assertIn('uploaded_at', project)
        self.assertIn('updated_at', project)

    # -------------------- Restore Version --------------------

    def test_restore_version_restores_old_data(self):
        """
        Verify that restore_version correctly restores a previous version
        and that the restored data becomes the current state.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create 3 versions
        v1_data = {"stage": "alpha", "value": 1}
        v2_data = {"stage": "beta", "value": 2}
        v3_data = {"stage": "gamma", "value": 3}
        
        project_id = self.store.insert_json("restore.json", v1_data)
        self.store.update(project_id, v2_data)
        self.store.update(project_id, v3_data)
        
        # Current should be v3
        current = self.store.fetch_by_id(project_id)
        self.assertEqual(current, v3_data)
        
        # Restore to v1
        success = self.store.restore_version(project_id, 1)
        self.assertTrue(success)
        
        # Current should now be v1 data
        restored = self.store.fetch_by_id(project_id)
        self.assertEqual(restored, v1_data)

    def test_restore_version_creates_new_version(self):
        """
        Verify that restore_version saves the current state before restoring,
        creating a new version.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("restore.json", {"v": 1})
        self.store.update(project_id, {"v": 2})
        self.store.update(project_id, {"v": 3})
        
        # Should have 3 versions
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 3)
        
        # Restore to v1
        self.store.restore_version(project_id, 1)
        
        # Should now have 4 versions (saved v3 before restore)
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 4)

    def test_restore_version_returns_false_for_invalid(self):
        """
        Verify that restore_version returns False when trying to restore
        a non-existent version.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("invalid.json", {"test": True})
        
        # Try to restore non-existent version
        success = self.store.restore_version(project_id, 99)
        self.assertFalse(success)

    # -------------------- Delete Old Versions --------------------

    def test_delete_old_versions_keeps_latest_n(self):
        """
        Verify that delete_old_versions keeps only the specified number
        of most recent versions.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create 10 versions
        project_id = self.store.insert_json("cleanup.json", {"v": 1})
        for i in range(2, 11):
            self.store.update(project_id, {"v": i})
        
        # Should have 10 versions
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 10)
        
        # Keep only last 3
        deleted_count = self.store.delete_old_versions(project_id, keep_latest=3)
        self.assertEqual(deleted_count, 7)
        
        # Should now have only 3 versions
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 3)
        
        # Should be versions 10, 9, and 8
        self.assertEqual(versions[0]['version_number'], 10)
        self.assertEqual(versions[1]['version_number'], 9)
        self.assertEqual(versions[2]['version_number'], 8)

    def test_delete_old_versions_returns_zero_when_under_limit(self):
        """
        Verify that delete_old_versions returns 0 when version count is
        already under the keep limit.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        project_id = self.store.insert_json("under.json", {"v": 1})
        self.store.update(project_id, {"v": 2})
        
        # Only 2 versions, keep 10
        deleted_count = self.store.delete_old_versions(project_id, keep_latest=10)
        self.assertEqual(deleted_count, 0)
        
        # Should still have 2 versions
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 2)

    # -------------------- Delete Cascade --------------------

    def test_delete_project_removes_all_versions(self):
        """
        Verify that deleting a project also deletes all its versions
        due to CASCADE constraint.

        Args:
            None: This test does not take any parameters.

        Returns:
            None: Assertions are used to validate expected behavior.
        """
        # Create project with multiple versions
        project_id = self.store.insert_json("cascade.json", {"v": 1})
        self.store.update(project_id, {"v": 2})
        self.store.update(project_id, {"v": 3})
        
        # Verify versions exist
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 3)
        
        # Delete project
        deleted = self.store.delete(project_id)
        self.assertTrue(deleted)
        
        # Versions should be gone too
        versions = self.store.get_version_list(project_id)
        self.assertEqual(len(versions), 0)


if __name__ == "__main__":
    unittest.main()