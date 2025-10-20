import json
import tempfile
import unittest
from pathlib import Path

from src import project_skill_insights


class TestProjectSkillInsights(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_identifies_python_data_skills(self):
        # Arrange: Python analysis project with data packages
        (self.project_root / "analysis").mkdir()
        (self.project_root / "analysis" / "pipeline.py").write_text(
            "import pandas as pd", encoding="utf-8"
        )
        (self.project_root / "requirements.txt").write_text(
            "pandas==2.2.1\nnumpy>=1.26\nscikit-learn\n", encoding="utf-8"
        )

        # Act
        skills = project_skill_insights.identify_skills(self.project_root)

        # Assert
        self.assertEqual(
            skills,
            ["Data Analysis", "Machine Learning", "Python"],
        )

    def test_identifies_react_skills(self):
        # Arrange: JavaScript React project with testing dependency
        src_dir = self.project_root / "src"
        src_dir.mkdir()
        (src_dir / "App.jsx").write_text("export default () => null;", encoding="utf-8")
        package_json = {
            "name": "dashboard",
            "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
            "devDependencies": {"jest": "^29.7.0"},
        }
        (self.project_root / "package.json").write_text(
            json.dumps(package_json), encoding="utf-8"
        )

        # Act
        skills = project_skill_insights.identify_skills(self.project_root)

        # Assert
        self.assertEqual(
            skills,
            ["JavaScript", "React", "Testing", "Web Development"],
        )

    def test_identifies_fullstack_skills(self):
        # Arrange: Mixed project with Python FastAPI backend and Vue frontend
        backend = self.project_root / "backend"
        backend.mkdir()
        (backend / "app.py").write_text("from fastapi import FastAPI", encoding="utf-8")
        (backend / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

        frontend = self.project_root / "frontend"
        frontend.mkdir()
        (frontend / "main.ts").write_text("console.log('ts');", encoding="utf-8")
        package_json = {"dependencies": {"vue": "^3.3.4"}}
        (frontend / "package.json").write_text(
            json.dumps(package_json), encoding="utf-8"
        )

        # Act
        skills = project_skill_insights.identify_skills(self.project_root)

        # Assert (alphabetical order expected)
        self.assertEqual(
            skills,
            ["FastAPI", "Python", "TypeScript", "Vue.js", "Web Development"],
        )


if __name__ == "__main__":
    unittest.main()
