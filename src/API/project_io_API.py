from fastapi import APIRouter, UploadFile
from src.storage.saved_projects import get_saved_projects_from_db, get_project_by_id
from src.core.app_context import runtimeAppContext

projectsRouter = APIRouter(prefix="/projects")


@projectsRouter.post("/upload")
async def upload_project(upload_file: UploadFile):
    # TODO: implement later
    return {"error": "Not implemented"}


@projectsRouter.get("/")
def return_all_saved_projects() -> list[dict]:
    """
    Returns all saved projects from the database.

    Output format:
      [
        {"id": 1, "name": "MyProject", "filename": "MyProject.json", "uploaded_at": "..."},
        ...
      ]
    """
    projects = get_saved_projects_from_db(runtimeAppContext)

    out: list[dict] = []
    for record_id, filename, uploaded_at in projects:
        name = filename[:-5] if filename.endswith(".json") else filename
        out.append(
            {
                "id": record_id,
                "name": name,
                "filename": filename,
                "uploaded_at": uploaded_at.isoformat() if uploaded_at else None,
            }
        )

    return out


@projectsRouter.get("/{project_id}")
def get_project_by_id_endpoint(project_id: int):
    """
    Returns a specific project by ID from the database.
    """
    return get_project_by_id(project_id, runtimeAppContext)