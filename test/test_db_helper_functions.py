import json
import os
import tempfile
import unittest


# set up

class TestProjectDataStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a single ProjectDataStore instance for the whole suite."""
        cls.store = ProjectDataStore(
            host="localhost",
            user="root",
            password="rootpassword",
            database="appdb"
        )

    @classmethod
    def tearDownClass(cls):
        cls.store.close()

    def setUp(self):
        """Clean DB before each test (replacement for the pytest fixture)."""
        cursor = self.store.conn.cursor()
        cursor.execute("DELETE FROM project_data;")
        self.store.conn.commit()
        cursor.close()

# Tests


