from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Set

# Map common file extensions to programming languages.
LANGUAGE_EXTENSIONS: Mapping[str, str] = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".go": "Go",
    ".rs": "Rust",
    ".swift": "Swift",
    ".kt": "Kotlin",
}

# Known Python web/data frameworks that might appear in requirement files.
PYTHON_FRAMEWORK_KEYWORDS: Mapping[str, str] = {
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "quart": "Quart",
    "streamlit": "Streamlit",
    "dash": "Dash",
}

# Known JavaScript frameworks keyed by dependency name.
JS_FRAMEWORK_KEYWORDS: Mapping[str, str] = {
    "react": "React",
    "next": "Next.js",
    "vue": "Vue.js",
    "nuxt": "Nuxt.js",
    "angular": "Angular",
    "@angular/core": "Angular",
    "svelte": "Svelte",
    "gatsby": "Gatsby",
}


def detect_project_stack(project_root: Path | str) -> Dict[str, List[str]]:
    """
    Analyze the given project directory and infer primary languages and frameworks.

    Args:
        project_root: Directory representing the project workspace.

    Returns:
        Dictionary containing sorted lists for the keys:
            - ``languages``: detected programming languages.
            - ``frameworks``: detected frameworks/libraries.
    """
    root = Path(project_root)
    if not root.exists():
        return {"languages": [], "frameworks": []}

    languages: Set[str] = set()
    frameworks: Set[str] = set()

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        ext = path.suffix.lower()
        if ext in LANGUAGE_EXTENSIONS:
            languages.add(LANGUAGE_EXTENSIONS[ext])

        filename = path.name.lower()
        if filename == "requirements.txt":
            frameworks.update(_scan_requirements(path))
        elif filename in {"pyproject.toml", "poetry.lock", "pdm.lock"}:
            frameworks.update(_scan_python_build_config(path))
        elif filename == "package.json":
            frameworks.update(_scan_package_json(path))
        elif filename == "composer.json":
            frameworks.update(_scan_composer_json(path))

    return {
        "languages": sorted(languages),
        "frameworks": sorted(frameworks),
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
