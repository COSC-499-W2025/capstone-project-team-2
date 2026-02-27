import pytest
import os
import shutil
from pathlib import Path

from src.API.analysis_API import *
import src.API.analysis_API as analysis_api_mod
from src.API.general_API import app
from src.core.app_context import runtimeAppContext
import zipfile

from fastapi.testclient import TestClient

test_client = TestClient(app)

def test_analysis_API_performed():
    """
    Ensures that when passing a zip file to analysis API, analysis completes and returns dedup info.

    Args:
        None
    """
    runtimeAppContext.currently_uploaded_file = Path(os.getcwd()).absolute().resolve() / "src" / "TEST.zip"
    response = test_client.get("/analyze")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Analysis Finished and Saved"
    assert "dedup" in body
    assert "snapshots" in body

def test_analysis_API_performed_with_upload_file():
    """
    Esnures that when passing a zip file to analysis API through the upload API, that analysis is performed without error
    """
    #Making a test file
    path = Path(os.getcwd()).absolute().resolve() / "src" / "TEST.zip"
    file = {"upload_file": path.open("rb")}
    
    #Calls the API with the file to get a response from the upload, should return code 200
    response = test_client.post("/projects/upload", files=file)
    assert response.status_code == 200
    
    #Calls analysis using the now uploaded project
    response = test_client.get("/analyze")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "Analysis Finished and Saved"
    assert "dedup" in body


def test_analysis_API_remove_duplicates_query_passthrough(monkeypatch, tmp_path):
    """
    Ensure remove_duplicates query parameter is passed through to analysis_service.
    """
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    runtimeAppContext.currently_uploaded_file = project_dir

    captured = {"remove_duplicates": None}

    def fake_analyze(folder, use_ai_analysis=False, project_name=None, remove_duplicates=True):
        captured["remove_duplicates"] = remove_duplicates
        return {"dedup": {}, "snapshots": []}

    monkeypatch.setattr(analysis_api_mod, "analyze_project", fake_analyze)

    response = test_client.get("/analyze?remove_duplicates=false")
    assert response.status_code == 200
    assert response.json()["status"] == "Analysis Finished and Saved"
    assert captured["remove_duplicates"] is False

#Somehow we don't get an error raised here. Sam is handling this issue. Test needed for coverage.
#def test_API_invalid_project():
#    """
#    Ensures error is returned when invlaid file is presented
#    """
#    runtimeAppContext.currently_uploaded_file = Path(os.getcwd()).absolute().resolve() / "src" / "not_real"
#    response = test_client.get("/analyze")
#    assert response.status_code == 200
#    assert response.json() == "Error: Filepath not found"
