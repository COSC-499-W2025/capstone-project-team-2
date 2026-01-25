import pytest
import os
import shutil

from src.API.analysis_API import *
from src.API.general_API import app
from src.core.app_context import runtimeAppContext

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