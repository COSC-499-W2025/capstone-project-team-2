import datetime
import json
import io
import tempfile
from dataclasses import dataclass
from pathlib import Path
import uuid
from fastapi import APIRouter, UploadFile, HTTPException, Query, status
from fastapi.responses import FileResponse
import zipfile
import pandas as pd
from src.core.project_duration_estimation import format_duration

from src.storage import saved_projects
from src.storage.saved_projects import list_saved_projects
from src.core.app_context import runtimeAppContext
from src.storage.saved_projects import *
from src.config.project_thumbnails import ThumbnailManager
from src.reporting.project_insights import (
    list_project_insights,
    remove_project_from_insights,
    update_thumbnail_in_insights,
    remove_thumbnail_from_insights,
)

projectsRouter = APIRouter(
    prefix="/projects"
)


@dataclass
class _ResolvedProjectIdentifier:
    """Resolved identifier info for thumbnail operations."""

    insight_id: str
    project_name: str


def _insights_storage_path() -> Path:
    """Return the path to project insights storage."""
    return Path(runtimeAppContext.legacy_save_dir) / "project_insights.json"


def _thumbnail_storage_dir() -> Path:
    """Return the directory where thumbnails are stored."""
    return Path(runtimeAppContext.legacy_save_dir) / "thumbnails"


def _resolve_project_identifier(identifier: str) -> _ResolvedProjectIdentifier:
    """
    Resolve a project identifier from insights by UUID first, then project name.

    Args:
        identifier: Insight UUID or project name.

    Returns:
        _ResolvedProjectIdentifier: Matched insight id and project name.

    """
    insights = list_project_insights(storage_path=_insights_storage_path())

    name_match: _ResolvedProjectIdentifier | None = None
    for insight in insights:
        if insight.id == identifier:
            return _ResolvedProjectIdentifier(
                insight_id=insight.id,
                project_name=insight.project_name,
            )
        if insight.project_name == identifier and name_match is None:
            name_match = _ResolvedProjectIdentifier(
                insight_id=insight.id,
                project_name=insight.project_name,
            )

    if name_match is not None:
        return name_match

    raise HTTPException(
        status_code=404,
        detail=(
            f"Project '{identifier}' was not found in insights. "
            "Analyze the project first to create an insight record."
        ),
    )

def _persist_uploaded_zip(upload_file: UploadFile, payload: bytes) -> Path:
    """
    Persist an uploaded ZIP payload to a temp file and return its path.

    Args:
        upload_file: Source upload metadata.
        payload: Raw ZIP bytes.

    Returns:
        Path: Filesystem path to persisted ZIP.
    """
    upload_dir = Path(tempfile.gettempdir()) / "devdoc_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    source_name = Path(upload_file.filename or "uploaded_project.zip").name
    source_stem = Path(source_name).stem or "uploaded_project"
    source_suffix = Path(source_name).suffix or ".zip"
    out_name = f"{source_stem}_{uuid.uuid4().hex[:8]}{source_suffix}"
    out_path = upload_dir / out_name
    out_path.write_bytes(payload)
    return out_path


def _allowed_project_save_dirs() -> tuple[Path, ...]:
    """Return canonical directories where project JSON files are allowed to live."""
    default_dir = Path(runtimeAppContext.default_save_dir).expanduser().resolve()
    legacy_dir = default_dir.parent.resolve()
    return (default_dir, legacy_dir)


def _is_path_within_allowed_dirs(path: Path, allowed_dirs: tuple[Path, ...]) -> bool:
    expanded = path.expanduser()
    resolved = expanded.parent.resolve() / expanded.name
    for d in allowed_dirs:
        if resolved == d:
            return True
        try:
            resolved.relative_to(d)
            return True
        except ValueError:
            pass
    return False

@projectsRouter.post("/upload")
async def upload_project(upload_file: UploadFile) -> dict:
    """
    Upload a ZIP project file (new snapshot) for later analysis.

    Stores the uploaded ZIP as a temporary file and tracks that path in
    ``runtimeAppContext.currently_uploaded_file`` for follow-up ``/analyze`` calls.
    """
    payload = await upload_file.read()
    await upload_file.close()
    if not payload or not zipfile.is_zipfile(io.BytesIO(payload)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file is not a zip file",
        )

    persisted_zip = _persist_uploaded_zip(upload_file, payload)
    source_stem = Path(upload_file.filename or "uploaded_project.zip").stem or "uploaded_project"
    runtimeAppContext.currently_uploaded_file = persisted_zip
    runtimeAppContext.currently_uploaded_project_name = source_stem
    return {
        "status": "ok",
        "filename": upload_file.filename,
        "stored_path": str(persisted_zip),
        "project_name": source_stem,
    }

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
    data = runtimeAppContext.store.fetch_by_name(project_filename)
    if data is not None:
        return {
            "project_name": project_stem,
            "source": "database",
            "analysis": data,
        }

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
    allowed_dirs = _allowed_project_save_dirs()
    if save_path_path is not None:
        save_file_name = save_path_path.name

        if is_internal_analysis_artifact(save_file_name):
            return {
                "dbstatus": f"[INFO] '{project_name}' DB deletion skipped.",
                "status": f"[INFO] '{save_file_name}' is an internal artifact and cannot be deleted.",
            }

        if save_file_name != project_name:
            return {
                "dbstatus": f"[INFO] '{project_name}' DB deletion skipped.",
                "status": (
                    f"[WARNING] save_path filename '{save_file_name}' must match requested "
                    f"project '{project_name}'."
                ),
            }

        if not _is_path_within_allowed_dirs(save_path_path, allowed_dirs):
            allowed_str = ", ".join(str(p) for p in allowed_dirs)
            return {
                "dbstatus": f"[INFO] '{project_name}' DB deletion skipped.",
                "status": (
                    f"[WARNING] Refusing to delete '{save_file_name}' outside allowed save "
                    f"directories: {allowed_str}."
                ),
            }

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

    # Remove from project_insights.json so the dashboard stays in sync.
    project_stem = Path(project_name).stem
    try:
        remove_project_from_insights(project_stem, storage_path=_insights_storage_path())
    except Exception:
        pass  # Non-critical — don't fail the whole delete if insights cleanup fails.

    return out_dict


@projectsRouter.get("/{id}/delete")
def delete_project_legacy(id: str, save_path: str | None = Query(default=None)) -> dict:
    """
    Legacy compatibility route for delete-by-GET.

    API call is ``GET /projects/{id}/delete`` and forwards to
    ``DELETE /projects/{id}`` behavior.
    """
    return delete_project(id=id, save_path=save_path)


@projectsRouter.post("/{id}/thumbnail")
async def upload_project_thumbnail(
    id: str,
    thumbnail: UploadFile,
    resize: bool = Query(default=True),
) -> dict:
    """
    Upload and associate a project thumbnail image.

    Args:
        id: Insight UUID or project name.
        thumbnail: Image file uploaded via multipart form-data.
        resize: Whether to resize to standard thumbnail dimensions.

    Returns:
        dict: Saved thumbnail metadata and association status.
    """
    resolved = _resolve_project_identifier(id)
    filename = thumbnail.filename or ""
    suffix = Path(filename).suffix.lower()
    if not suffix:
        raise HTTPException(
            status_code=400,
            detail="Thumbnail filename must include an image extension.",
        )

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            tmp.write(await thumbnail.read())

        manager = ThumbnailManager(storage_dir=_thumbnail_storage_dir())
        success, error, thumb_path = manager.add_thumbnail(
            project_id=resolved.insight_id,
            image_path=temp_path,
            resize=resize,
        )
        if not success or thumb_path is None:
            raise HTTPException(
                status_code=400,
                detail=error or "Failed to store thumbnail.",
            )

        linked = update_thumbnail_in_insights(
            resolved.insight_id,
            thumb_path,
            storage_path=_insights_storage_path(),
        )
        if not linked:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Thumbnail file was saved but could not be linked to "
                    "the project insight."
                ),
            )

        return {
            "status": "Thumbnail uploaded successfully",
            "project_id": resolved.insight_id,
            "project_name": resolved.project_name,
            "thumbnail": {
                "path": str(thumb_path),
                "filename": thumb_path.name,
            },
        }
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        await thumbnail.close()


@projectsRouter.get("/{id}/thumbnail")
def get_project_thumbnail(id: str) -> dict:
    """
    Retrieve thumbnail metadata for a project.

    Args:
        id: Insight UUID or project name.

    Returns:
        dict: Thumbnail metadata for the matched project.
    """
    resolved = _resolve_project_identifier(id)
    manager = ThumbnailManager(storage_dir=_thumbnail_storage_dir())
    thumb_path = manager.get_thumbnail_path(resolved.insight_id)
    if thumb_path is None:
        # Backward compatibility with older project-name thumbnail keys.
        thumb_path = manager.get_thumbnail_path(resolved.project_name)

    if thumb_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No thumbnail found for project '{resolved.project_name}'.",
        )

    return {
        "project_id": resolved.insight_id,
        "project_name": resolved.project_name,
        "thumbnail": {
            "path": str(thumb_path),
            "filename": thumb_path.name,
        },
    }


@projectsRouter.get("/{id}/thumbnail/image")
def get_project_thumbnail_image(id: str) -> FileResponse:
    """Serve the raw thumbnail image file for a project."""
    resolved = _resolve_project_identifier(id)
    manager = ThumbnailManager(storage_dir=_thumbnail_storage_dir())
    thumb_path = manager.get_thumbnail_path(resolved.insight_id)
    if thumb_path is None:
        thumb_path = manager.get_thumbnail_path(resolved.project_name)
    if thumb_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No thumbnail found for project '{resolved.project_name}'.",
        )
    return FileResponse(str(thumb_path))


@projectsRouter.delete("/{id}/thumbnail")
def delete_project_thumbnail(id: str) -> dict:
    """
    Delete a project's associated thumbnail image.

    Args:
        id: Insight UUID or project name.

    Returns:
        dict: Deletion status for thumbnail and insight metadata.
    """
    resolved = _resolve_project_identifier(id)
    manager = ThumbnailManager(storage_dir=_thumbnail_storage_dir())

    deleted = manager.delete_thumbnail(resolved.insight_id)
    if not deleted:
        # Backward compatibility with older project-name thumbnail keys.
        deleted = manager.delete_thumbnail(resolved.project_name)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No thumbnail found for project '{resolved.project_name}'.",
        )

    remove_thumbnail_from_insights(
        resolved.insight_id,
        storage_path=_insights_storage_path(),
    )

    return {
        "status": "Thumbnail deleted successfully",
        "project_id": resolved.insight_id,
        "project_name": resolved.project_name,
    }


@projectsRouter.post("/{id}/type")
def update_project_type(id: str, project_type: str) -> dict:
    """
    API endpoint for updating the project type of a given project

    API call is ''POST /projects/{id}/type?project_type=str

    Args:
        id (str): name of the project
        project_type (str): individual or collaborative project type

    Returns:
        dict: Success message and new project type
    
    Raises:
        404: When project is not found in database
    """

    id = id if id.endswith(".json") else f"{id}.json"
    dict_to_update: dict = runtimeAppContext.store.fetch_by_name(id)
    if not dict_to_update:
        raise HTTPException(
            status_code=404,
            detail=f"Project {id} not found",
        )
    dict_to_update["resume_item"]["project_type"] = project_type
    runtimeAppContext.store.update(id, dict_to_update)
    return {"message": "Updated successfully", "type": project_type}


@projectsRouter.post("/{id}/duration")
def update_project_duration(id: str, start: str, end: str) -> dict:
    """
    API endpoint for updating the project duration of a given project with start and end dates

    API call is ''POST /projects/{id}/duration?start=str&end=str

    Args:
        id (str): name of the project
        start (str): string representation of the start date
        end (str): string representation of the end date

    Returns:
        dict: Success message and new duration
    
    Raises:
        404: When project is not found in database
        400: When formatting date and converting to timedelta fails OR when start date is later than end date
    """

    id = id if id.endswith(".json") else f"{id}.json"
    dict_to_update: dict = runtimeAppContext.store.fetch_by_name(id)
    if not dict_to_update:
        raise HTTPException(
            status_code=404,
            detail=f"Project {id} not found",
        )
    try:
        end_date = datetime.datetime.strptime(end, '%Y-%m-%d').date()
        start_date = datetime.datetime.strptime(start, '%Y-%m-%d').date()
        if end_date == start_date:
            end_date += datetime.timedelta(days=1)
        duration = end_date - start_date
        str_duration = format_duration(duration)
        dict_to_update["duration_estimate"] = str_duration  #Converts project duration to timedelta using a pandas library
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    if duration < datetime.timedelta(seconds=0):
            raise HTTPException(
            status_code=400,
            detail=f"Start date must be before end date",
            )
    runtimeAppContext.store.update(id, dict_to_update)
    return {"message": "Updated successfully", "dur": str_duration}
