import pytest
import os
import shutil

from src.API.analysis_API import *
from src.API.general_API import app
from src.core.app_context import runtimeAppContext

from fastapi.testclient import TestClient

test_client = TestClient(app)

#I cannot get test to work without being able to upload
#def test_analysis_API_performed():
#    runtimeAppContext.currently_uploaded_path = Path(os.getcwd()).absolute().resolve() / "src" / "TEST.zip"
#    response = test_client.get("/analyze")
#    assert response.status_code == 200
#    assert response.json() == "finished"