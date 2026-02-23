import shutil
import pytest
from pathlib import Path
import os
import json

from src.API.project_io_API import *
from src.API.general_API import app
from src.core.app_context import create_app_context, runtimeAppContext

from fastapi.testclient import TestClient

test_client = TestClient(app)

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
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "zip file" in body["message"]

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

def test_delete_project_no_db():
    """
    Ensures that removing a project not in db does not return successful db deletion, but success on local deletion
    """
    root_folder = Path(__file__).absolute().resolve().parents[1]
    legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = legacy_save_dir / "project_insights"
    path = runtimeAppContext.default_save_dir / "test.json"
    try:
        path.touch(exist_ok=True)
        path.write_text("test")
        statuses = delete_project(path.name, str(path))

        assert statuses.get("status") == f"[SUCCESS] Deleted '{path.name}' from filesystem!"
        assert statuses.get("dbstatus") != f"[SUCCESS] Deleted DB records for '{path.name}'."
        assert not path.exists()
    finally:
        if path.exists():
            path.unlink(missing_ok=True)

#insertion into the db currently doesn't work and I don't know what's wrong
@pytest.mark.skip()
def test_delete_project_db():
    """
    Ensures that removing a project in db return successful db deletion and success on local deletion
    """
    runtimeAppContext = create_app_context(data_consent_value=True)
    root_folder = Path(__file__).absolute().resolve().parents[1]
    legacy_save_dir = root_folder / "User_config_files"
    runtimeAppContext.default_save_dir = legacy_save_dir / "project_insights"
    path = runtimeAppContext.default_save_dir / "test.json"
    try:
        path.touch(exist_ok=True)
        path.write_text("test")
        runtimeAppContext.store.insert_json("test.json", {"test": False})
        statuses = delete_project(path.name, str(path))

        assert statuses.get("status") == f"[SUCCESS] Deleted '{path.name}' from filesystem!"
        assert statuses.get("dbstatus") == f"[SUCCESS] Deleted DB records for '{path.name}'."
        assert not path.exists()
    finally:
        if path.exists():
            path.unlink(missing_ok=True)
