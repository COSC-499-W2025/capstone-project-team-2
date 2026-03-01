import json
import tempfile
import unittest
from pathlib import Path

from src.project_stack_detection import detect_project_stack


class TestProjectStackDetection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detects_python_flask_project(self):
        (self.project_path / "app.py").write_text("print('hello')", encoding="utf-8")
        (self.project_path / "requirements.txt").write_text(
            "Flask==2.3.2\nrequests==2.32.0\n", encoding="utf-8"
        )

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], ["Python"])
        self.assertEqual(result["frameworks"], ["Flask"])
        self.assertEqual(result["framework_sources"], {"Flask": ["requirements.txt"]})

    def test_detects_js_react_project(self):
        src_dir = self.project_path / "src"
        src_dir.mkdir()
        (src_dir / "index.js").write_text("console.log('hi');", encoding="utf-8")
        package_json = {
            "name": "dashboard",
            "version": "1.0.0",
            "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"},
        }
        (self.project_path / "package.json").write_text(
            json.dumps(package_json), encoding="utf-8"
        )

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], ["JavaScript"])
        self.assertEqual(result["frameworks"], ["React"])
        self.assertEqual(result["framework_sources"], {"React": ["package.json"]})

    def test_detects_node_express_project(self):
        api_dir = self.project_path / "api"
        api_dir.mkdir()
        (api_dir / "server.js").write_text("require('express');", encoding="utf-8")
        package_json = {
            "name": "api",
            "version": "1.0.0",
            "dependencies": {"express": "^4.19.0"},
        }
        (self.project_path / "package.json").write_text(
            json.dumps(package_json), encoding="utf-8"
        )

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], ["JavaScript"])
        self.assertEqual(result["frameworks"], ["Express"])
        self.assertEqual(result["framework_sources"], {"Express": ["package.json"]})

    def test_detects_c_and_cpp_sources(self):
        (self.project_path / "main.c").write_text("int main() {return 0;}", encoding="utf-8")
        (self.project_path / "lib.cpp").write_text("int add(int a, int b){return a+b;}", encoding="utf-8")
        (self.project_path / "header.hpp").write_text("#pragma once", encoding="utf-8")

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], ["C", "C++"])
        self.assertEqual(result["frameworks"], [])
        self.assertEqual(result["framework_sources"], {})

    def test_detects_infrastructure_frameworks(self):
        (self.project_path / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")
        (self.project_path / "docker-compose.yml").write_text("version: '3.9'", encoding="utf-8")
        infra = self.project_path / "infra"
        infra.mkdir()
        (infra / "main.tf").write_text("# terraform config", encoding="utf-8")

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], [])
        self.assertEqual(result["frameworks"], ["Docker", "Docker Compose", "Terraform"])
        self.assertEqual(
            result["framework_sources"],
            {
                "Docker": ["Dockerfile"],
                "Docker Compose": ["docker-compose.yml"],
                "Terraform": ["infra/main.tf"],
            },
        )

    def test_skips_ignored_directories(self):
        node_modules = self.project_path / "node_modules" / "react"
        node_modules.mkdir(parents=True)
        (node_modules / "index.js").write_text("console.log('ignored');", encoding="utf-8")

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], [])
        self.assertEqual(result["frameworks"], [])
        self.assertEqual(result["framework_sources"], {})

    def test_detects_multiple_languages_and_frameworks(self):
        (self.project_path / "backend").mkdir()
        (self.project_path / "backend" / "service.py").write_text(
            "import django\n", encoding="utf-8"
        )
        (self.project_path / "backend" / "requirements.txt").write_text(
            "Django>=4.0\n", encoding="utf-8"
        )
        frontend = self.project_path / "frontend"
        frontend.mkdir()
        (frontend / "main.ts").write_text("console.log('hi');", encoding="utf-8")
        (frontend / "utils.js").write_text("export {}", encoding="utf-8")
        package_json = {
            "name": "dashboard",
            "version": "1.0.0",
            "dependencies": {"vue": "^3.3.4"},
        }
        (frontend / "package.json").write_text(
            json.dumps(package_json), encoding="utf-8"
        )

        result = detect_project_stack(self.project_path)

        self.assertEqual(
            result["languages"], ["JavaScript", "Python", "TypeScript"]
        )
        self.assertEqual(result["frameworks"], ["Django", "Vue.js"])
        self.assertEqual(
            result["framework_sources"],
            {"Django": ["backend/requirements.txt"], "Vue.js": ["frontend/package.json"]},
        )

    def test_empty_project_returns_empty_lists(self):
        (self.project_path / "README.md").write_text("# Empty project", encoding="utf-8")

        result = detect_project_stack(self.project_path)

        self.assertEqual(result["languages"], [])
        self.assertEqual(result["frameworks"], [])
        self.assertEqual(result["framework_sources"], {})


if __name__ == "__main__":
    unittest.main()
