import shutil
import pytest
from pathlib import Path
import os
import json
from unittest.mock import Mock

from src.API.project_io_API import *
from src.API.general_API import app
from src.core.app_context import create_app_context, runtimeAppContext

from fastapi.testclient import TestClient

test_client = TestClient(app)

@pytest.fixture
def make_project_save_dir(monkeypatch, tmp_path):
    """
    Creates and patches runtime save dir for tests that need local project files.
    """
    def _make(relative: str = "project_insights") -> Path:
        save_dir = tmp_path / relative
        save_dir.mkdir(parents=True, exist_ok=True)
        import src.core.app_context as _ctx
        monkeypatch.setattr(_ctx.runtimeAppContext, "default_save_dir", save_dir)
        return save_dir
    return _make

def test_return_all_saved_projects_none():
    """
    Tests API returns no saved projects when no projects have been saved

    Also checks that response contains a list

    Args:
        None
    """
    response = test_client.get("/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  #Checks that list is still returned

def test_return_all_saved_projects():
    """
    Tests API returns a list that contains a project when a project exists

    Also checks that response contains a list

    Args:
        None
    """
    out_dir = Path(runtimeAppContext.default_save_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)  #Makes directory where we will save json file

    filename = "test.json"

    write_file = os.path.join(out_dir, filename)
    with open(write_file, 'w') as file:
        file.write("json_project")

    response = test_client.get("/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() != None #Checks that list is not empty

    shutil.rmtree(out_dir)  #Deletes files made by test

def test_upload_file_API():
    """
    Test that checks we can pass a zip file into the upload api
    """
    #Making a test file
    path = os.getcwd()
    path = os.path.join(path, "api_test.zip")
    with zipfile.ZipFile(path, "w") as f:
        f.writestr("dummy.txt", "test")

    fh = Path(path).open("rb")
    try:
        file = {"upload_file": fh}
        #Calls the API with the file to get a response from the upload, should return a success string
        response = test_client.post("/projects/upload", files=file)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["filename"] == "api_test.zip"
        assert body["project_name"] == "api_test"
    finally:
        fh.close()
        if os.path.exists(path):
            os.remove(path)

def test_upload_file_API_no_zip():
    """
    Test that passing a non-zip file returns the correct error
    """
    #Random directory for use as a non-zip file upload
    path = Path(os.getcwd()).absolute().resolve() / "test" / "TestZIPs" / "test.txt"

    #Calls the API with the file to get a response from the upload, should return a string error
    response = test_client.post("/projects/upload", files={"upload_file": path.open("rb")})
    assert response.status_code == 400
    body = response.json()
    assert "zip file" in body["detail"]

def test_upload_project_CLI_dir():
    """
    Test ensures adding a directory as an uploaded file through the CLI non-fastapi method
    """
    path = Path(os.getcwd())
    assert upload_project_path_CLI(path) == "Upload Success"

def test_upload_project_CLI_zip():
    """
    Test ensures adding a zip file as an uploaded file through the CLI non-fastapi method
    """
    path = Path(os.getcwd()).absolute().resolve() / "test" / "TestZIPs" / "TEST.zip"
    assert upload_project_path_CLI(path) == "Upload Success"

def test_get_project_by_name_prefers_database(monkeypatch):
    """
    Ensures GET /projects/{id} returns DB data when available.
    """
    expected = {"resume_item": {"project_name": "alpha"}}
    from src.core import app_context
    monkeypatch.setattr(
        app_context.runtimeAppContext.store,
        "fetch_by_name",
        lambda filename: expected if filename == "alpha.json" else None,
    )

    response = test_client.get("/projects/alpha")
    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "alpha"
    assert body["source"] == "database"
    assert body["analysis"] == expected

def test_get_project_by_name_uses_filesystem_fallback(monkeypatch, make_project_save_dir):
    """
    Ensures GET /projects/{id} falls back to filesystem when DB misses.
    """
    save_dir = make_project_save_dir()
    project_file = save_dir / "beta.json"
    expected = {"resume_item": {"project_name": "beta"}, "duration_estimate": "Unknown"}
    project_file.write_text(json.dumps(expected), encoding="utf-8")

    monkeypatch.setattr(runtimeAppContext.store, "fetch_by_name", lambda _name: None)

    response = test_client.get("/projects/beta")
    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "beta"
    assert body["source"] == "filesystem"
    assert body["analysis"] == expected

def test_get_project_by_name_invalid_json_returns_500(monkeypatch, make_project_save_dir):
    """
    Ensures malformed saved JSON returns HTTP 500.
    """
    save_dir = make_project_save_dir()
    bad_file = save_dir / "broken.json"
    bad_file.write_text("{bad json", encoding="utf-8")

    monkeypatch.setattr(runtimeAppContext.store, "fetch_by_name", lambda _name: None)

    response = test_client.get("/projects/broken")
    assert response.status_code == 500
    assert "Failed to parse saved project file 'broken.json'" in response.json()["detail"]

def test_get_project_by_name_not_found_returns_404(monkeypatch, make_project_save_dir):
    """
    Ensures GET /projects/{id} returns 404 when no project exists.
    """
    make_project_save_dir()
    monkeypatch.setattr(runtimeAppContext.store, "fetch_by_name", lambda _name: None)

    response = test_client.get("/projects/missing_project")
    assert response.status_code == 404
    assert "missing_project" in response.json()["detail"]

def test_delete_project_endpoint_calls_db_and_disk_helpers(monkeypatch):
    """
    Ensures DELETE /projects/{id} uses DB and disk helper functions.
    """
    mock_db_delete = Mock(return_value=True)
    mock_disk_delete = Mock(return_value=True)
    monkeypatch.setattr("src.API.project_io_API.delete_from_database_by_name", mock_db_delete)
    monkeypatch.setattr("src.API.project_io_API.delete_file_from_disk", mock_disk_delete)

    response = test_client.delete("/projects/demo_project")
    assert response.status_code == 200
    body = response.json()
    assert body["dbstatus"] == "[SUCCESS] Deleted DB records for 'demo_project.json'."
    assert body["status"] == "[SUCCESS] Deleted 'demo_project.json' from filesystem!"
    mock_db_delete.assert_called_once_with("demo_project.json")
    mock_disk_delete.assert_called_once_with("demo_project.json")

def test_delete_project_endpoint_blocks_internal_artifacts(monkeypatch):
    """
    Ensures DELETE /projects/{id} does not allow deleting internal artifacts.
    """
    mock_db_delete = Mock(return_value=True)
    mock_disk_delete = Mock(return_value=True)
    monkeypatch.setattr("src.API.project_io_API.delete_from_database_by_name", mock_db_delete)
    monkeypatch.setattr("src.API.project_io_API.delete_file_from_disk", mock_disk_delete)

    response = test_client.delete("/projects/dedup_index.json")
    assert response.status_code == 200
    body = response.json()
    assert body["dbstatus"] == "[INFO] 'dedup_index.json' is an internal artifact. DB deletion skipped."
    assert body["status"] == "[INFO] 'dedup_index.json' is an internal artifact and cannot be deleted."
    mock_db_delete.assert_not_called()
    mock_disk_delete.assert_not_called()

def test_delete_project_endpoint_rejects_mismatched_save_path(tmp_path, make_project_save_dir):
    """
    Ensures DELETE /projects/{id} rejects save_path filename mismatch.
    """
    make_project_save_dir()

    bad_path = tmp_path / "wrong_name.json"
    response = test_client.delete(f"/projects/right_name?save_path={bad_path}")

    assert response.status_code == 200
    body = response.json()
    assert "must match requested project 'right_name.json'" in body["status"]
    assert body["dbstatus"] == "[INFO] 'right_name.json' DB deletion skipped."

def test_delete_project_endpoint_rejects_outside_allowed_path(tmp_path, make_project_save_dir):
    """
    Ensures DELETE /projects/{id} rejects save_path outside allowed save dirs.
    """
    save_dir = make_project_save_dir("allowed/project_insights")

    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    outside_path = outside_dir / "outside_project.json"

    response = test_client.delete(f"/projects/outside_project?save_path={outside_path}")
    assert response.status_code == 200
    body = response.json()
    assert "Refusing to delete 'outside_project.json' outside allowed save directories" in body["status"]
    assert body["dbstatus"] == "[INFO] 'outside_project.json' DB deletion skipped."

def test_delete_project_endpoint_deletes_given_save_path(monkeypatch, make_project_save_dir):
    """
    Ensures DELETE /projects/{id}?save_path=... removes file when valid.
    """
    save_dir = make_project_save_dir()
    target = save_dir / "gamma.json"
    target.write_text("{}", encoding="utf-8")

    mock_db_delete = Mock(return_value=False)
    monkeypatch.setattr("src.API.project_io_API.delete_from_database_by_name", mock_db_delete)

    response = test_client.delete(f"/projects/gamma?save_path={target}")
    assert response.status_code == 200
    body = response.json()
    assert body["dbstatus"] == "[INFO] No DB records were found."
    assert body["status"] == "[SUCCESS] Deleted 'gamma.json' from filesystem!"
    assert not target.exists()
    mock_db_delete.assert_called_once_with("gamma.json")

def test_delete_project_legacy_route_forwards_to_delete(monkeypatch):
    """
    Ensures GET /projects/{id}/delete forwards to delete_project().
    """
    mock_delete = Mock(return_value={"status": "ok", "dbstatus": "ok"})
    monkeypatch.setattr("src.API.project_io_API.delete_project", mock_delete)

    response = test_client.get("/projects/legacy_proj/delete?save_path=/tmp/legacy_proj.json")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "dbstatus": "ok"}
    mock_delete.assert_called_once_with(id="legacy_proj", save_path="/tmp/legacy_proj.json")
def test_get_project_by_name_filesystem_success(monkeypatch, tmp_path):
    """
    Ensures GET /projects/{id} returns saved analysis JSON from local filesystem.
    """
    save_dir = tmp_path / "project_insights"
    save_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runtimeAppContext, "default_save_dir", save_dir)

    expected_analysis = {"summary": "ok", "skills": ["Python"]}
    (save_dir / "sample_project.json").write_text(
        json.dumps(expected_analysis),
        encoding="utf-8",
    )

    response = test_client.get("/projects/sample_project")

    assert response.status_code == 200
    body = response.json()
    assert body["project_name"] == "sample_project"
    assert body["source"] == "filesystem"
    assert body["analysis"] == expected_analysis

def test_get_project_by_name_not_found():
    """
    Ensures GET /projects/{id} returns 404 when project does not exist.
    """
    response = test_client.get("/projects/definitely_missing_project")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_update_project_duration_404():
    """
    Confirm that a project that isn't found returns a 404 status code
    """
    response = test_client.post("/projects/nan/duration?start=2020-01-01&end=2020-02-01")

    assert response.status_code == 404

def test_update_project_duration_bad_dates(monkeypatch):
    """
    Confirm that when invalid dates are used, that a 400 status code is returned
    """
    expected = {"duration_estimate": ""}
    monkeypatch.setattr(
        runtimeAppContext.store,
        "fetch_by_name",
        lambda filename: expected
    )
    response = test_client.post("/projects/this/duration?start=2020-01-aa&end=2020-aa-01")

    assert response.status_code == 400

def test_update_project_duration_late_dates(monkeypatch):
    """
    Confirm that when start date is later than end date, status code 400 returned
    """
    expected = {"duration_estimate": ""}
    monkeypatch.setattr(
        runtimeAppContext.store,
        "fetch_by_name",
        lambda filename: expected
    )
    response = test_client.post("/projects/this/duration?start=2020-01-02&end=2020-01-01")

    assert response.status_code == 400

def test_update_project_duration_normal(monkeypatch):
    """
    Confirms status code 200 and correct duration returned when normal input and project exists
    """
    expected = {"duration_estimate": ""}

    class MockAppContext:
        def fetch_by_name(id):
            return expected

        def update(id, dur):
            pass

    monkeypatch.setattr(
        "src.core.app_context.runtimeAppContext.store",
        MockAppContext
    )
    response = test_client.post("/projects/this/duration?start=2020-01-01&end=2020-01-02")

    assert response.status_code == 200
    assert response.json()["dur"] == "1 day"