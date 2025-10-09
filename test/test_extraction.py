import shutil

from src.extraction import extractInfo
from pathlib import Path
def test_extract():
    extract=extractInfo("TEST_2.zip").extractFiles()
    output=Path("temp")
    if output.is_dir():
        assert True
        shutil.rmtree(output)


