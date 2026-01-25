import shutil
from typing import assert_type
from fastapi import responses
import pytest
from pathlib import Path
import os

from src.API.project_io_API import *
from src.API.general_API import app
from src.core.app_context import runtimeAppContext

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
    assert_type(response.json(), list) #Checks that list is still returned

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
    assert_type(response.json(), list)
    assert response.json() != None #Checks that list is not empty

    shutil.rmtree(out_dir)  #Deletes files made by test

def test_upload_file_API():
    """
    Test that checks we can pass a zip file into the upload api
    """
    #Making a test file
    path = os.getcwd()
    path = os.path.join(path, "api_test.zip")
    with zipfile.ZipFile(path, "w")as f:
        f.write("test")
    file = {"upload_file": Path(path).open("rb")}

    #Calls the API with the file to get a response from the upload, should return a success string
    response = test_client.post("/projects/upload", files=file)
    assert response.status_code == 200
    assert response.json() == "Upload Success"
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
    assert response.json() == "Error, file is not a zip file!"

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