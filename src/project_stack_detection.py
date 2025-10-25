from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Set

"""
project_stack_detection.py
--------------------------
Analyzes a project directory and infers the primary technology stack,
including programming languages, frameworks, and infrastructure tools.

This module is responsible for low-level evidence gathering:
- Scans file extensions → programming languages
- Scans dependency files → frameworks/libraries
- Scans infrastructure files → DevOps/IaC tools

Used by: project_skill_insights.py to map technologies → skill categories
"""

# --------------------------- LANGUAGE EXTENSIONS ------------------------------

LANGUAGE_EXTENSIONS: Mapping[str, str] = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cxx": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".java": "Java",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".kt": "Kotlin",
}

# --------------------------- FRAMEWORK KEYWORDS -------------------------------

PYTHON_FRAMEWORK_KEYWORDS: Mapping[str, str] = {
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "quart": "Quart",
    "streamlit": "Streamlit",
    "dash": "Dash",
}

JS_FRAMEWORK_KEYWORDS: Mapping[str, str] = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue.js",
    "nuxt": "Nuxt.js",
    "angular": "Angular",
    "@angular/core": "Angular",
    "svelte": "Svelte",
    "gatsby": "Gatsby",
    "ember": "Ember.js",
    "express": "Express",
    "koa": "Koa",
    "nestjs": "NestJS",
    "@nestjs/core": "NestJS",
}

# --------------------------- INFRASTRUCTURE FILES -----------------------------

INFRASTRUCTURE_FILES: Mapping[str, str] = {
    "dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
}

IGNORED_DIRS: Set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
}

# --------------------------- MAIN API FUNCTION -------------------------------


def detect_project_stack(
    project_root: Path | str,
) -> Dict[str, List[str] | Dict[str, List[str]]]:
    """
    Analyze the given project directory and infer its primary languages,
    frameworks, and infrastructure tools.

    Args:
        project_root (Path | str): Path to the project root folder.

    Returns:
        dict: A dictionary with three keys:
            - "languages": List of detected programming languages.
            - "frameworks": List of detected frameworks/tools.
            - "framework_sources": Mapping of each framework/tool → file paths
              where it was discovered.
    """
    root = Path(project_root)
    if not root.exists():
        return {"languages": [], "frameworks": [], "framework_sources": {}}

    languages: Set[str] = set()
    frameworks: Set[str] = set()
    framework_sources: Dict[str, Set[str]] = defaultdict(set)

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue

        rel_path = str(path.relative_to(root))
        ext = path.suffix.lower()
        filename = path.name.lower()

        # --- Language inference
        if ext in LANGUAGE_EXTENSIONS:
            languages.add(LANGUAGE_EXTENSIONS[ext])

        # --- Infrastructure detection
        if filename == "dockerfile" or filename.endswith(".dockerfile"):
            frameworks.add("Docker")
            framework_sources["Docker"].add(rel_path)
        infra_framework = INFRASTRUCTURE_FILES.get(filename)
        if infra_framework:
            frameworks.add(infra_framework)
            framework_sources[infra_framework].add(rel_path)
        if ext == ".tf":
            frameworks.add("Terraform")
            framework_sources["Terraform"].add(rel_path)

        # --- Dependency/config file scans
        if filename == "requirements.txt":
            for framework in _scan_requirements(path):
                frameworks.add(framework)
                framework_sources[framework].add(rel_path)
        elif filename in {"pyproject.toml", "poetry.lock", "pdm.lock"}:
            for framework in _scan_python_build_config(path):
                frameworks.add(framework)
                framework_sources[framework].add(rel_path)
        elif filename == "package.json":
            for framework in _scan_package_json(path):
                frameworks.add(framework)
                framework_sources[framework].add(rel_path)
        elif filename == "composer.json":
            for framework in _scan_composer_json(path):
                frameworks.add(framework)
                framework_sources[framework].add(rel_path)

    return {
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
        "framework_sources": {
            name: sorted(paths) for name, paths in framework_sources.items()
        },
    }


def _scan_requirements(requirements_path: Path) -> Set[str]:
    """Find known frameworks listed in a requirements-style text file."""
    detected: Set[str] = set()
    try:
        content = requirements_path.read_text(encoding="utf-8")
    except OSError:
        return detected

    for line in content.splitlines():
        normalized = line.strip().lower()
        if not normalized or normalized.startswith("#"):
            continue

        for keyword, framework in PYTHON_FRAMEWORK_KEYWORDS.items():
            if keyword in normalized:
                detected.add(framework)
    return detected


def _scan_python_build_config(path: Path) -> Set[str]:
    """
    Inspect pyproject.toml-like files for known frameworks.

    Instead of fully parsing TOML, rely on simple keyword search which is sufficient
    for identifying common frameworks called out in dependency listings.
    """
    detected: Set[str] = set()
    try:
        text = path.read_text(encoding="utf-8").lower()
    except OSError:
        return detected

    for keyword, framework in PYTHON_FRAMEWORK_KEYWORDS.items():
        if keyword in text:
            detected.add(framework)
    return detected


def _scan_package_json(package_path: Path) -> Set[str]:
    """Inspect JavaScript package manifest for framework dependencies."""
    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    detected: Set[str] = set()
    dependencies = package_data.get("dependencies", {})
    dev_dependencies = package_data.get("devDependencies", {})
    detected.update(_scan_js_dependencies(dependencies))
    detected.update(_scan_js_dependencies(dev_dependencies))
    return detected


def _scan_js_dependencies(deps: Optional[Mapping[str, str]]) -> Set[str]:
    """Return frameworks matched within a dependency mapping."""
    if not deps:
        return set()

    detected: Set[str] = set()
    for dep_name in deps.keys():
        lower_dep = dep_name.lower()
        for keyword, framework in JS_FRAMEWORK_KEYWORDS.items():
            if keyword in lower_dep:
                detected.add(framework)
    return detected


def _scan_composer_json(composer_path: Path) -> Set[str]:
    """Detect frameworks (e.g., Laravel) from PHP composer manifest."""
    try:
        composer_data = json.loads(composer_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()

    detected: Set[str] = set()
    require_sections: Iterable[Mapping[str, str]] = (
        composer_data.get("require", {}),
        composer_data.get("require-dev", {}),
    )
    for section in require_sections:
        for name in section:
            if "laravel" in name.lower():
                detected.add("Laravel")
    return detected


__all__ = ["detect_project_stack"]
