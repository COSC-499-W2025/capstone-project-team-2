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
