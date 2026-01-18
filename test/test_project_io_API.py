import shutil
from typing import assert_type
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
    assert_type(response.json(), list)
    assert not response.json() #Checks that list is empty

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
    assert response.json() #Checks that list is not empty

    shutil.rmtree(out_dir)  #Deletes files made by test