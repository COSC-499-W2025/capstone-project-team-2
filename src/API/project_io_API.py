from pathlib import Path
from fastapi import APIRouter, UploadFile
import zipfile
import copy

from src.storage import saved_projects
from src.storage.saved_projects import list_saved_projects
from src.core.app_context import runtimeAppContext

projectsRouter = APIRouter(
    prefix="/projects"
)

@projectsRouter.post("/upload")
async def upload_project(upload_file: UploadFile) -> str:
    """
    API call for uploading a file to the backend

    HTTP call is /projects/upload

    Args:
        upload_file (UploadFile): uploaded file through HTTP via form data. UploadFile.file contains file-like object
    
    Returns:
        str: returns an error string if the uploaded file isn't a zip file, otherswsie returns that upload succeeded
    """
    if not zipfile.is_zipfile(upload_file.file):
        return "Error, file is not a zip file!"
    runtimeAppContext.currently_uploaded_file = copy.deepcopy(upload_file)
    return "Upload Success"

def upload_project_path_CLI(upload_file: Path) -> str:
    """
    Temporary API method for use in the CLI to pass project Paths

    Checks that project is a directory or zip file

    Args:
        upload_file (Path): Path object representing a file path to a project

    Returns:
        str: returns if upload was a success or returns error stating path wasn't a project
    """
    if not (upload_file.is_dir() or zipfile.is_zipfile(str(upload_file))):
        return "Error, path is not a project"
    runtimeAppContext.currently_uploaded_file = upload_file
    return "Upload Success"

@projectsRouter.get("/")
def return_all_saved_projects() -> list:
    """
    API call for returning list of all saved projects

    HTTP call is /projects

    Args:
        None

    Returns:
        list: list of all saved project names
    """
    save_paths = list_saved_projects(runtimeAppContext.default_save_dir)    #Pulling paths of saved projects

    #Converting Path objects in project names
    saved_projects = list()
    for path in save_paths:
        saved_projects.append(path.stem)

    return saved_projects

#TODO What should I output?
@projectsRouter.get("/{id}")
def get_project_by_name(project_name: str):
    return id