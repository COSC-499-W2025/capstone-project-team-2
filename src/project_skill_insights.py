from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Mapping, Optional, Set
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.project_stack_detection import detect_project_stack

"""
project_skill_insights.py
-------------------------
Builds on the project stack detector to infer higher-level skill categories.

- Converts detected languages/frameworks into general skills
- Recognizes domain-specific packages (data analysis, ML, testing)
- Adds DevOps and IaC skills for infrastructure frameworks
- Provides a list of human-readable skill labels
"""

# --------------------------- PACKAGE → SKILL MAP ------------------------------

PACKAGE_SKILL_MAP: Mapping[str, str] = {
    "numpy": "Data Analysis",
    "pandas": "Data Analysis",
    "polars": "Data Analysis",
    "matplotlib": "Data Visualization",
    "seaborn": "Data Visualization",
    "plotly": "Data Visualization",
    "scikit-learn": "Machine Learning",
    "sklearn": "Machine Learning",
    "tensorflow": "Machine Learning",
    "keras": "Machine Learning",
    "torch": "Machine Learning",
    "pytorch": "Machine Learning",
    "pytest": "Testing",
    "unittest": "Testing",
    "jest": "Testing",
    "cypress": "Testing",
}

# --------------------------- FRAMEWORK GROUPS ---------------------------------

WEB_FRAMEWORKS: Set[str] = {
    "Flask",
    "Django",
    "FastAPI",
    "Quart",
    "React",
    "Vue.js",
    "Angular",
    "Svelte",
    "Next.js",
    "Nuxt.js",
    "Express",
    "NestJS",
    "Koa",
}

VISUALIZATION_FRAMEWORKS: Set[str] = {
    "Dash",
    "Streamlit",
}

INFRA_TO_SKILL: Mapping[str, str] = {
    "Docker": "DevOps",
    "Docker Compose": "DevOps",
    "Terraform": "Infrastructure as Code",
}

# --------------------------- MAIN API FUNCTION -------------------------------


def identify_skills(project_root: Path | str) -> List[str]:
    """
    Derive high-level skills demonstrated within a project workspace.

    Combines language detection, framework discovery, and package analysis to produce
    a curated list of skill labels (sorted alphabetically).
    """
    root = Path(project_root)
    if not root.exists():
        return []

    stack_info = detect_project_stack(root)
    detected_languages = set(stack_info.get("languages", []))
    detected_frameworks = set(stack_info.get("frameworks", []))

    skills: Set[str] = set()
    skills.update(detected_languages)
    skills.update(detected_frameworks)

    if detected_frameworks & WEB_FRAMEWORKS:
        skills.add("Web Development")
    if detected_frameworks & VISUALIZATION_FRAMEWORKS:
        skills.add("Data Visualization")

    # Infrastructure → DevOps/IaC
    for framework in detected_frameworks & set(INFRA_TO_SKILL.keys()):
        skills.add(INFRA_TO_SKILL[framework])

    skills.update(_scan_additional_skills(root))

    return sorted(skills)


def _scan_additional_skills(root: Path) -> Set[str]:
    """
    Inspect dependency files for domain-specific skills (e.g., data analysis, testing).
    """
    detected: Set[str] = set()

    for requirements in root.rglob("requirements.txt"):
        detected.update(_skills_from_requirements(requirements))

    for pyproject in root.rglob("pyproject.toml"):
        detected.update(_skills_from_text_file(pyproject))

    for package_json in root.rglob("package.json"):
        detected.update(_skills_from_package_json(package_json))

    for composer_json in root.rglob("composer.json"):
        detected.update(_skills_from_package_json(composer_json))

    return detected


def _skills_from_requirements(path: Path) -> Set[str]:
    detected: Set[str] = set()
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return detected

    for line in content.splitlines():
        name = _extract_package_name(line)
        if not name:
            continue

        skill = PACKAGE_SKILL_MAP.get(name.lower())
        if skill:
            detected.add(skill)
    return detected


def _skills_from_text_file(path: Path) -> Set[str]:
    """
    Lightweight keyword matching for build configuration files (e.g., pyproject.toml).
    """
    detected: Set[str] = set()
    try:
        text = path.read_text(encoding="utf-8").lower()
    except OSError:
        return detected

    for package, skill in PACKAGE_SKILL_MAP.items():
        if package in text:
            detected.add(skill)
    return detected


def _skills_from_package_json(path: Path) -> Set[str]:
    detected: Set[str] = set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return detected

    dependencies = data.get("dependencies", {})
    dev_dependencies = data.get("devDependencies", {})
    detected.update(_skills_from_dep_mapping(dependencies))
    detected.update(_skills_from_dep_mapping(dev_dependencies))
    return detected


def _skills_from_dep_mapping(dependencies: Optional[Mapping[str, str]]) -> Set[str]:
    detected: Set[str] = set()
    if not dependencies:
        return detected

    for name in dependencies.keys():
        # Normalise scoped packages like "@types/jest"
        normalized = name.split("/")[-1].lower()
        skill = PACKAGE_SKILL_MAP.get(normalized)
        if skill:
            detected.add(skill)
    return detected


def _extract_package_name(line: str) -> Optional[str]:
    """
    Extract the package name from a dependency line.
    Handles common requirement specifiers (==, >=, <=, ~=, extras).
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    match = re.match(r"([A-Za-z0-9_\-\.]+)", stripped)
    if not match:
        return None
    return match.group(1)


__all__ = ["identify_skills"]
