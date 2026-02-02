# conftest.py
import os
import sys
from types import SimpleNamespace

import pytest

# Add project root (one level up from test/) to Python path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


@pytest.fixture(autouse=True)
def isolate_dedup_side_effects(monkeypatch, tmp_path):
    """
    Stop tests from deleting real project files.
    - Stub deduplicate_project to a no-op result.
    - Point default_save_dir to a per-test temp directory.
    """
    import src.core.analysis_service as analysis_service

    monkeypatch.setattr(
        analysis_service,
        "deduplicate_project",
        lambda root, index_path, remove_duplicates=True: SimpleNamespace(
            unique_files=0,
            duplicate_files=0,
            duplicates=[],
            index_size=0,
            removed=0,
        ),
    )

    safe_save_dir = tmp_path / "project_insights"
    safe_save_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        analysis_service.runtimeAppContext,
        "default_save_dir",
        safe_save_dir,
        raising=False,
    )
