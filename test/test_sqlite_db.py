import unittest
import sqlite3
import os


class TestSQLiteSetup(unittest.TestCase):
    """
    Verifies that the SQLite database is correctly initialized with
    the expected tables, triggers, and indexes.
    """

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(":memory:")
        cls.conn.execute("PRAGMA foreign_keys = ON")
        schema_path = os.path.join(os.path.dirname(__file__), "..", "database.sql")
        with open(schema_path) as f:
            cls.conn.executescript(f.read())
        cls.cur = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_tables_exist(self):
        """Verify that both required tables exist."""
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in self.cur.fetchall()]
        self.assertIn("project_data", tables)
        self.assertIn("project_versions", tables)

    def test_trigger_exists(self):
        """Verify that the updated_at trigger exists."""
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
        triggers = [row[0] for row in self.cur.fetchall()]
        self.assertIn("update_project_data_timestamp", triggers)

    def test_indexes_exist(self):
        """Verify that the expected indexes exist."""
        self.cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in self.cur.fetchall()]
        self.assertIn("idx_project_versions", indexes)
        self.assertIn("idx_created_at", indexes)

    def test_foreign_keys_enabled(self):
        """Verify that foreign key enforcement is on."""
        self.cur.execute("PRAGMA foreign_keys")
        result = self.cur.fetchone()[0]
        self.assertEqual(result, 1)

    def test_project_data_columns(self):
        """Verify that project_data has the expected columns."""
        self.cur.execute("PRAGMA table_info(project_data)")
        columns = [row[1] for row in self.cur.fetchall()]
        for col in ["Pname", "content", "file_blob", "uploaded_at", "current_version", "updated_at"]:
            self.assertIn(col, columns)

    def test_project_versions_columns(self):
        """Verify that project_versions has the expected columns."""
        self.cur.execute("PRAGMA table_info(project_versions)")
        columns = [row[1] for row in self.cur.fetchall()]
        for col in ["id", "project_name", "project_uploaded_at", "version_number", "content", "file_blob", "created_at"]:
            self.assertIn(col, columns)

    def test_cascade_delete(self):
        """Verify that deleting a project cascades to its versions."""
        self.cur.execute(
            "INSERT INTO project_data (Pname, content) VALUES (?, ?)",
            ("test_cascade.json", '{"test": true}')
        )
        self.cur.execute("SELECT uploaded_at FROM project_data WHERE Pname = ?", ("test_cascade.json",))
        uploaded_at = self.cur.fetchone()[0]

        self.cur.execute(
            "INSERT INTO project_versions (project_name, project_uploaded_at, version_number, content) VALUES (?, ?, ?, ?)",
            ("test_cascade.json", uploaded_at, 1, '{"test": true}')
        )
        self.conn.commit()

        self.cur.execute("DELETE FROM project_data WHERE Pname = ?", ("test_cascade.json",))
        self.conn.commit()

        self.cur.execute("SELECT * FROM project_versions WHERE project_name = ?", ("test_cascade.json",))
        self.assertIsNone(self.cur.fetchone())


if __name__ == "__main__":
    unittest.main()