"""Tests for project thumbnail API endpoints."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from fastapi.testclient import TestClient

from src.API.general_API import app
from src.API import project_io_API
from src.core.app_context import runtimeAppContext

test_client = TestClient(app)


def _insight(project_id: str = "proj-uuid-123", name: str = "MyProject") -> SimpleNamespace:
    """Create a lightweight insight object for endpoint tests."""
    return SimpleNamespace(id=project_id, project_name=name)


def test_upload_thumbnail_success(monkeypatch, tmp_path):
    """POST /projects/{id}/thumbnail stores and links a thumbnail successfully."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    captured = {}

    class _FakeThumbnailManager:
        def __init__(self, storage_dir):
            self.storage_dir = storage_dir

        def add_thumbnail(self, project_id, image_path, resize=True):
            captured["project_id"] = project_id
            captured["resize"] = resize
            captured["image_exists"] = Path(image_path).exists()
            return True, None, Path("/tmp/proj-uuid-123.png")

    monkeypatch.setattr(project_io_API, "ThumbnailManager", _FakeThumbnailManager)
    monkeypatch.setattr(project_io_API, "update_thumbnail_in_insights", lambda *args, **kwargs: True)

    response = test_client.post(
        "/projects/MyProject/thumbnail?resize=false",
        files={"thumbnail": ("thumb.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Thumbnail uploaded successfully"
    assert body["project_id"] == "proj-uuid-123"
    assert body["project_name"] == "MyProject"
    assert body["thumbnail"]["filename"] == "proj-uuid-123.png"
    assert captured["project_id"] == "proj-uuid-123"
    assert captured["resize"] is False
    assert captured["image_exists"] is True


def test_upload_thumbnail_missing_extension_returns_400(monkeypatch, tmp_path):
    """POST thumbnail should reject files without an extension."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    response = test_client.post(
        "/projects/MyProject/thumbnail",
        files={"thumbnail": ("thumbnail", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 400
    assert "must include an image extension" in response.json()["detail"]


def test_upload_thumbnail_unknown_project_returns_404(monkeypatch, tmp_path):
    """POST thumbnail should return 404 when project insight cannot be resolved."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [])

    response = test_client.post(
        "/projects/UnknownProject/thumbnail",
        files={"thumbnail": ("thumb.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 404
    assert "Analyze the project first" in response.json()["detail"]


def test_upload_thumbnail_link_failure_returns_500(monkeypatch, tmp_path):
    """POST thumbnail returns 500 if file save succeeds but insight link fails."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    class _FakeThumbnailManager:
        def __init__(self, storage_dir):
            self.storage_dir = storage_dir

        def add_thumbnail(self, project_id, image_path, resize=True):
            return True, None, Path("/tmp/proj-uuid-123.png")

    monkeypatch.setattr(project_io_API, "ThumbnailManager", _FakeThumbnailManager)
    monkeypatch.setattr(project_io_API, "update_thumbnail_in_insights", lambda *args, **kwargs: False)

    response = test_client.post(
        "/projects/MyProject/thumbnail",
        files={"thumbnail": ("thumb.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 500
    assert "could not be linked" in response.json()["detail"]


def test_get_thumbnail_success(monkeypatch, tmp_path):
    """GET /projects/{id}/thumbnail returns thumbnail metadata when present."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    class _FakeThumbnailManager:
        def __init__(self, storage_dir):
            self.storage_dir = storage_dir

        def get_thumbnail_path(self, project_id):
            if project_id == "proj-uuid-123":
                return Path("/tmp/proj-uuid-123.png")
            return None

    monkeypatch.setattr(project_io_API, "ThumbnailManager", _FakeThumbnailManager)

    response = test_client.get("/projects/MyProject/thumbnail")

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == "proj-uuid-123"
    assert body["project_name"] == "MyProject"
    assert body["thumbnail"]["filename"] == "proj-uuid-123.png"


def test_get_thumbnail_missing_returns_404(monkeypatch, tmp_path):
    """GET thumbnail should return 404 when no thumbnail exists."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    class _FakeThumbnailManager:
        def __init__(self, storage_dir):
            self.storage_dir = storage_dir

        def get_thumbnail_path(self, _project_id):
            return None

    monkeypatch.setattr(project_io_API, "ThumbnailManager", _FakeThumbnailManager)

    response = test_client.get("/projects/MyProject/thumbnail")
    assert response.status_code == 404
    assert "No thumbnail found" in response.json()["detail"]


def test_delete_thumbnail_success(monkeypatch, tmp_path):
    """DELETE /projects/{id}/thumbnail removes file and insight metadata."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    deleted_ids = []

    class _FakeThumbnailManager:
        def __init__(self, storage_dir):
            self.storage_dir = storage_dir

        def delete_thumbnail(self, project_id):
            deleted_ids.append(project_id)
            return project_id == "proj-uuid-123"

    monkeypatch.setattr(project_io_API, "ThumbnailManager", _FakeThumbnailManager)
    mock_remove = Mock()
    monkeypatch.setattr(project_io_API, "remove_thumbnail_from_insights", mock_remove)

    response = test_client.delete("/projects/MyProject/thumbnail")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Thumbnail deleted successfully"
    assert body["project_id"] == "proj-uuid-123"
    assert "proj-uuid-123" in deleted_ids
    mock_remove.assert_called_once()


def test_delete_thumbnail_missing_returns_404(monkeypatch, tmp_path):
    """DELETE thumbnail should return 404 when no thumbnail exists."""
    monkeypatch.setattr(runtimeAppContext, "legacy_save_dir", tmp_path)
    monkeypatch.setattr(project_io_API, "list_project_insights", lambda storage_path: [_insight()])

    class _FakeThumbnailManager:
        def __init__(self, storage_dir):
            self.storage_dir = storage_dir

        def delete_thumbnail(self, _project_id):
            return False

    monkeypatch.setattr(project_io_API, "ThumbnailManager", _FakeThumbnailManager)

    response = test_client.delete("/projects/MyProject/thumbnail")
    assert response.status_code == 404
    assert "No thumbnail found" in response.json()["detail"]
