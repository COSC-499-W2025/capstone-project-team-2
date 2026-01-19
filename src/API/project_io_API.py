from fastapi import APIRouter, UploadFile

from src.storage import saved_projects
from src.storage.saved_projects import list_saved_projects
from src.core.app_context import runtimeAppContext

projectsRouter = APIRouter(
    prefix="/projects"
)

#TODO
@projectsRouter.post("/upload")
async def upload_project(upload_file: UploadFile):
    pass

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