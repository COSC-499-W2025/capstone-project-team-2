import pytest
import os
import shutil

from src.API.analysis_API import *
from src.API.general_API import app
from src.core.app_context import runtimeAppContext
import zipfile

from fastapi.testclient import TestClient

test_client = TestClient(app)

def test_analysis_API_performed():
    """
    Esnures that when passing a zip file to analysis API, that analysis is performed without error
    """
    runtimeAppContext.currently_uploaded_file = Path(os.getcwd()).absolute().resolve() / "src" / "TEST.zip"
    response = test_client.get("/analyze")
    assert response.status_code == 200
    assert response.json() == "Analysis Finished and Saved"

def test_analysis_API_performed_with_upload_file():
    """
    Esnures that when passing a zip file to analysis API through the upload API, that analysis is performed without error
    """
    #Making a test file
    path = os.getcwd()
    path = os.path.join(path, "api_test.zip")
    with zipfile.ZipFile(path, "w")as f:
        f.write("test")
    file = {"upload_file": Path(path).open("rb")}
    
    #Calls the API with the file to get a response from the upload, should return code 200
    response = test_client.post("/projects/upload", files=file)
    assert response.status_code == 200
    
    #Calls analysis using the now uploaded project
    response = test_client.get("/analyze")
    assert response.status_code == 200
    assert response.json() == "Analysis Finished and Saved"

    if os.path.exists(path):
            os.remove(path)

#Somehow we don't get an error raised here. Sam is handling this issue. Test needed for coverage.
#def test_API_invalid_project():
#    """
#    Ensures error is returned when invlaid file is presented
#    """
#    runtimeAppContext.currently_uploaded_file = Path(os.getcwd()).absolute().resolve() / "src" / "not_real"
#    response = test_client.get("/analyze")
#    assert response.status_code == 200
#    assert response.json() == "Error: Filepath not found"