import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException, Query
import zipfile
import copy

from src.storage import saved_projects
from src.storage.saved_projects import list_saved_projects
from src.core.app_context import runtimeAppContext
from src.storage.saved_projects import *

projectsRouter = APIRouter(
    prefix="/projects"
)

@projectsRouter.post("/upload")
async def upload_project(upload_file: UploadFile) -> str:
    """
    Upload a ZIP project file for later analysis.

    API call is ``POST /projects/upload``.

    Args:
        upload_file (UploadFile): Uploaded file from multipart form-data.

    Returns:
        str: ``"Upload Success"`` when the file is a ZIP, otherwise
            ``"Error, file is not a zip file!"``.
    """
    if not zipfile.is_zipfile(upload_file.file):
        return "Error, file is not a zip file!"
    runtimeAppContext.currently_uploaded_file = copy.deepcopy(upload_file)
    return "Upload Success"

def upload_project_path_CLI(upload_file: Path) -> str:
    """
    CLI helper for setting the current project path.

    Accepts either a directory path or a ZIP file path.

    Args:
        upload_file (Path): Filesystem path to a project directory or ZIP.

    Returns:
        str: ``"Upload Success"`` when valid, otherwise
            ``"Error, path is not a project"``.
    """
    if not (upload_file.is_dir() or zipfile.is_zipfile(str(upload_file))):
        return "Error, path is not a project"
    runtimeAppContext.currently_uploaded_file = upload_file
    return "Upload Success"

@projectsRouter.get("/")
def return_all_saved_projects() -> list:
    """
    List saved project analysis names.

    API call is ``GET /projects``.

    Returns:
        list: Project names (filename stems), not full file paths.
    """
    save_paths = list_saved_projects(runtimeAppContext.default_save_dir)    #Pulling paths of saved projects

    #Converting Path objects in project names
    saved_projects = list()
    for path in save_paths:
        saved_projects.append(path.stem)

    return saved_projects

@projectsRouter.get("/{id}")
def get_project_by_name(id: str) -> dict:
    """
    Retrieve one saved project analysis by project name.

    API call is ``GET /projects/{id}``.

    Args:
        id (str): Project name from path, with or without ``.json`` suffix.

    Returns:
        dict: ``{"project_name", "source", "analysis"}``.

    Raises:
        HTTPException: ``404`` if not found, ``500`` if local JSON cannot be parsed.
    """
    project_filename = id if id.endswith(".json") else f"{id}.json"
    project_stem = Path(project_filename).stem

    # Prefer DB source when available.
    try:
        data = runtimeAppContext.store.fetch_by_name(project_filename)
        if data is not None:
            return {
                "project_name": project_stem,
                "source": "database",
                "analysis": data,
            }
    except Exception:
        pass

    # Fallback to local files.
    candidate_paths = [
        Path(runtimeAppContext.default_save_dir) / project_filename,
        Path(runtimeAppContext.default_save_dir).parent / project_filename,
    ]
    for path in candidate_paths:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to parse saved project file '{path.name}': {e}",
                )
            return {
                "project_name": project_stem,
                "source": "filesystem",
                "analysis": data,
            }

    raise HTTPException(
        status_code=404,
        detail=f"Project '{project_stem}' was not found.",
    )

@projectsRouter.delete("/{id}")
def delete_project(id: str, save_path: str | None = Query(default=None)) -> dict:
    """
    Delete a project from DB and local filesystem.

    API call is ``DELETE /projects/{id}``.

    Args:
        id (str): Project name with or without ``.json`` suffix.
        save_path (str | None): Optional direct local file path override.

    Returns:
        dict: Status dictionary with keys ``dbstatus`` and ``status``.
    """
    project_name = id if id.endswith(".json") else f"{id}.json"
    if is_internal_analysis_artifact(project_name):
        return {
            "dbstatus": f"[INFO] '{project_name}' is an internal artifact. DB deletion skipped.",
            "status": f"[INFO] '{project_name}' is an internal artifact and cannot be deleted.",
        }
    save_path_path = Path(save_path) if save_path else None
    out_dict = {}

    # Delete DB record by Pname.
    try:
        deleted = delete_from_database_by_name(project_name)
        out_dict["dbstatus"] = (
            f"[SUCCESS] Deleted DB records for '{project_name}'."
            if deleted
            else "[INFO] No DB records were found."
        )
    except Exception as e:
        out_dict["dbstatus"] = f"[WARNING] Could not query database: {e}"

    # Delete from filesystem.
    if save_path_path is not None:
        try:
            save_path_path.unlink()
            out_dict["status"] = f"[SUCCESS] Deleted '{project_name}' from filesystem!"
        except Exception as e:
            out_dict["status"] = (
                f"[WARNING] Unexpected error while attempting to delete file "
                f"'{project_name}': {e}"
            )
    else:
        deleted_file = delete_file_from_disk(project_name)
        out_dict["status"] = (
            f"[SUCCESS] Deleted '{project_name}' from filesystem!"
            if deleted_file
            else f"[INFO] No local file was deleted for '{project_name}'."
        )

    return out_dict


@projectsRouter.get("/{id}/delete")
def delete_project_legacy(id: str, save_path: str | None = Query(default=None)) -> dict:
    """
    Legacy compatibility route for delete-by-GET.

    API call is ``GET /projects/{id}/delete`` and forwards to
    ``DELETE /projects/{id}`` behavior.
    """
    return delete_project(id=id, save_path=save_path)
