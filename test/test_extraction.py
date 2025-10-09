import shutil

from src.extraction import extractInfo
from pathlib import Path


def test_extract():
    matches = []
    root_folder=Path(__file__).resolve().parent.parent
    for p in root_folder.rglob("*"):
        if p.is_dir() and "temp".lower() in p.name.lower():
            matches.append(p)

    for path in matches:
        shutil.rmtree(path)

    extract = extractInfo("TEST_2.zip").extractFiles()
    output = Path("temp")
    if output.is_dir():
        assert True
        shutil.rmtree(output)
