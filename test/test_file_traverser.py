import pytest
from pathlib import Path
import os

from src.analysis.file_traverser import ProjectTraversalModule

def test_traverser_init():
    """
    Tests to ensure class can successfully be initialized
    """
    test_folder = Path(os.getcwd()).absolute().resolve() / "docs" / "peer_testing_files" / "Test Document"
    try:
        traverser = ProjectTraversalModule(test_folder)
        assert traverser.root_dir   #Pass if root_dir created in traverser class
    except: #Fail test if error occurs
        pytest.fail("Error raised in creating class.")

def test_traverser_traverse():
    """
    Test ensures that a dictionary is returned without error
    """
    test_folder = Path(os.getcwd()).absolute().resolve() / "docs" / "peer_testing_files" / "Test Document"
    traverser = ProjectTraversalModule(test_folder)
    analysis = traverser.build_analysis_with_project()
    assert isinstance(analysis, dict)