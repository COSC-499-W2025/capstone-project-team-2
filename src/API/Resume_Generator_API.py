"""
FastAPI endpoints for resume generation and editing via RenderCV.

Provides a RESTFUL API for creating, reading, updating, and deleting
resume documents backed by RenderCV YAML files. Resumes are identified
by a unique ID (name + UUID suffix) returned in the X-Resume-ID header
upon generation.

Endpoints:
    POST   /resume/generate                          - Create a new resume
    GET    /resume/{id}                              - Retrieve full resume data as JSON
    POST   /resume/{id}/render/{format}              - Re-render and return as file response
    POST   /resume/{id}/export/{format}              - Render and export to default directory
    POST   /resume/{id}/export/{format}/custom       - Render and export to a custom directory
    POST   /resume/{id}/edit                         - Modify a field on an existing section item
    POST   /resume/{id}/add/project/{project_name}   - Add a project entry
    DELETE /resume/{id}/project/{project_name}        - Remove a project entry
    POST   /resume/{id}/add/education                - Add an education entry
    DELETE /resume/{id}/education/{institution_name} - Remove an education entry
    POST   /resume/{id}/add/experience               - Add an experience entry
    DELETE /resume/{id}/experience/{company_name}    - Remove an experience entry
    DELETE /resume/{id}                              - Delete the resume YAML file entirely
"""

from typing import Optional, List, Any
from pathlib import Path
import uuid
import shutil
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument,
    Project,
    Education,
    Experience,
)
from src.core.app_context import runtimeAppContext

RENDERED_OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "User_config_files" / "Generate_render_CV_files" / "rendered_outputs"


resumeRouter = APIRouter(tags=["Resume"])

ALLOWED_CONTACT_FIELDS = {"email", "phone", "location", "website", "name"}


class GenerateResumeRequest(BaseModel):
    """Payload for creating a new resume."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "John_Doe",
        "theme": "sb2nov",
        "overwrite": False,
    }})
    name: str
    theme: Optional[str] = 'sb2nov'
    overwrite: bool = False


class EditItem(BaseModel):
    """A single field edit on a resume section item."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "section": "contact",
        "item_name": "",
        "field": "email",
        "new_value": "john.doe@example.com",
    }})
    section: str
    item_name: str
    field: str
    new_value: Any

class EditResumeRequest(BaseModel):
    """Payload containing one or more resume edits."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "edits": [
            {"section": "contact", "item_name": "", "field": "email", "new_value": "john.doe@example.com"},
            {"section": "contact", "item_name": "", "field": "phone", "new_value": "555-123-4567"},
            {"section": "summary", "item_name": "", "field": "", "new_value": "Software engineer with 5 years of experience."},
            {"section": "experience", "item_name": "Software Engineer", "field": "company", "new_value": "Acme Corp"},
            {"section": "projects", "item_name": "MyProject", "field": "summary", "new_value": "Built a REST API with FastAPI."},
            {"section": "theme", "item_name": "", "field": "", "new_value": "classic"},
        ]
    }})
    edits: List[EditItem]

class ProjectRequest(BaseModel):
    """Optional overrides when adding a project from the database."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "My Capstone Project",
        "start_date": "2024-09",
        "end_date": "2025-04",
        "location": "Kelowna, BC",
        "summary": "Built a developer portfolio generation tool using FastAPI and RenderCV.",
        "highlights": ["Designed REST API with FastAPI", "Integrated RenderCV for PDF generation"],
    }})
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None

class EducationRequest(BaseModel):
    """Payload for adding a new education entry."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "institution": "University of British Columbia",
        "area": "Computer Science",
        "degree": "BSc",
        "start_date": "2021-09",
        "end_date": "2025-04",
        "location": "Kelowna, BC",
        "gpa": "3.8",
        "highlights": ["Dean's List", "Capstone project on AI resume generation"],
    }})
    institution: str
    area: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    gpa: Optional[str] = None
    highlights: Optional[List[str]] = None


class ExperienceRequest(BaseModel):
    """Payload for adding a new experience entry."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "company": "Acme Corp",
        "position": "Software Engineer",
        "start_date": "2023-05",
        "end_date": "present",
        "location": "Vancouver, BC",
        "highlights": ["Built REST APIs with FastAPI", "Reduced latency by 40%"],
    }})
    company: str
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[List[str]] = None


class SaveRequest(BaseModel):
    """Payload for saving a rendered file to a custom location."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "path": "/home/user/Documents/resumes",
    }})
    path: str


SUPPORTED_FORMATS = {"pdf", "html", "markdown"}
EXTENSIONS = {"pdf": "pdf", "html": "html", "markdown": "md"}

"""-------Helper Methods-------"""

def _load_resume(name: str) -> RenderCVDocument:
    """Load an existing resume YAML by name.

    Args:
        name: The resume identifier (name + UUID suffix).

    Returns:
        RenderCVDocument: The loaded resume document.

    Raises:
        HTTPException: 404 if the resume YAML file does not exist.
    """
    doc = RenderCVDocument(doc_type="resume")
    try:
        doc.load(name=name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Resume '{name}' not found")
    return doc

def _validate_format(format: str) -> str:
    """Validate and normalize the output format string."""
    fmt = format.strip().lower()
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{format}'. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}")
    return fmt

def _render_and_get_path(doc: RenderCVDocument, fmt: str) -> Path:
    """Render a document and return the output file path."""
    status, outputs = doc.render_outputs([fmt])
    paths = outputs.get(fmt, [])
    if not paths:
        raise HTTPException(status_code=500, detail=status)
    return paths[0]

def _check_result(result: str):
    """Validate the result string from a RenderCVDocument operation.

    Args:
        result: Status message returned by a RenderCVDocument method.

    Returns:
        str: The result string if it indicates success.

    Raises:
        HTTPException: 400 if the result does not contain 'successfully'.
    """
    if "successfully" not in result.lower():
        raise HTTPException(status_code=400, detail=result)
    return result


@resumeRouter.post("/resume/generate")
def generate_resume(payload: GenerateResumeRequest):
    """Create a new resume YAML from a starter template.

    Generates a unique resume ID by appending a UUID suffix to the provided name.
    The YAML file is created and optionally themed. Use POST /resume/{id}/render
    to produce a PDF (default), or POST /resume/{id}/render/{format} to specify
    the output format ('pdf', 'html', or 'markdown').

    Args:
        payload: GenerateResumeRequest with name, optional theme, and overwrite flag.

    Returns:
        dict: {"resume_id": "<id>", "status": "created"} on success.

    Raises:
        HTTPException: 409 if resume already exists and overwrite is False.
    """
    doc = RenderCVDocument(doc_type="resume")
    resume_id = str(uuid.uuid4())[:8]
    full_name = f"{payload.name}_{resume_id}"

    gen_result = doc.generate(name=full_name, overwrite=payload.overwrite)

    if gen_result == "Skipping generation":
        raise HTTPException(status_code=409,
                            detail=f"Resume '{payload.name}' already exists. Set overwrite=true to replace it.",
                            )
    doc.load(name=full_name)

    if payload.theme and payload.theme != 'sb2nov':
        try:
            doc.update_theme(payload.theme)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"resume_id": full_name, "status": "Resume created successfully"}


@resumeRouter.get("/resume/{id}")
def get_resume(id: str):
    """Retrieve the full resume data as JSON.

    Returns all sections of the resume including contact info, theme,
    summary, experience, education, projects, skills, and connections.

    Args:
        id: The resume identifier (name + UUID suffix from generation).

    Returns:
        dict: JSON object containing all resume sections.

    Raises:
        HTTPException: 404 if the resume does not exist.
    """
    doc = _load_resume(id)
    return {
        "name": id,
        "contact": doc.get_contact_info(),
        "theme": doc.get_theme(),
        "summary": doc.get_summary(),
        "experience": doc.get_experience(),
        "education": doc.get_education(),
        "projects": doc.get_projects(),
        "skills": doc.get_skills(),
        "connections": doc.get_connections(),
    }


@resumeRouter.post("/resume/{id}/edit")
def edit_resume(id: str, payload: EditResumeRequest):
    """Edit one or more fields on an existing resume.

    Supports batch editing multiple fields across different sections in a single
    API call. Each edit in the list is applied sequentially.

    Args:
        id: The resume identifier.
        payload: EditResumeRequest with a list of edits to apply.

    Returns:
        dict: {"results": [...]} with the status of each edit.

    Raises:
        HTTPException: 400 if an unknown section is specified or theme is invalid.
        HTTPException: 404 if the resume does not exist.

    Example - Single edit:
        ```json
        {
            "edits": [
                {"section": "summary", "item_name": "", "field": "", "new_value": "Senior software engineer with 10 years experience"}
            ]
        }
        ```

    Example - Multiple edits in one call:
        ```json
        {
            "edits": [
                {"section": "contact", "item_name": "", "field": "email", "new_value": "new@example.com"},
                {"section": "contact", "item_name": "", "field": "phone", "new_value": "555-1234"},
                {"section": "summary", "item_name": "", "field": "", "new_value": "Updated summary text"},
                {"section": "skills", "item_name": "Python", "field": "", "new_value": "Python 3.12"},
                {"section": "experience", "item_name": "Software Engineer", "field": "company", "new_value": "New Company Inc."},
                {"section": "education", "item_name": "BSc Computer Science", "field": "institution", "new_value": "MIT"},
                {"section": "projects", "item_name": "MyProject", "field": "summary", "new_value": "New project description"},
                {"section": "theme", "item_name": "", "field": "", "new_value": "classic"}
            ]
        }
        ```

    Section-specific notes:
        - summary: Only `new_value` is used; `item_name` and `field` are ignored.
        - contact: Use `field` to specify which contact field to update (e.g., email, phone).
        - theme: Only `new_value` is used; valid themes are 'sb2nov', 'classic', 'moderncv', 'engineeringresumes'.
        - skills: Use `item_name` to identify the skill to rename; `new_value` is the new skill name.
        - experience: Use `item_name` for the job title, `field` for the attribute to change.
        - education: Use `item_name` for the degree name, `field` for the attribute to change.
        - projects: Use `item_name` for the project name, `field` for the attribute to change.
    """
    doc = _load_resume(id)
    modify_map = {
        "experience": doc.modify_experience,
        "education": doc.modify_education,
        "projects": doc.modify_project,
    }
    results = []

    for edit in payload.edits:
        section = edit.section.lower()

        if section == "summary":
            result = _check_result(doc.update_summary(str(edit.new_value)))

        elif section == "contact":
            if edit.field not in ALLOWED_CONTACT_FIELDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown contact field '{edit.field}'. Valid fields: {', '.join(sorted(ALLOWED_CONTACT_FIELDS))}"
                )
            doc.update_contact(**{edit.field: edit.new_value})
            result = f"Successfully updated contact field '{edit.field}'"

        elif section == "theme":
            try:
                result = _check_result(doc.update_theme(str(edit.new_value)))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        elif section == "skills":
            result = _check_result(doc.modify_skill(edit.item_name, edit.new_value))

        elif section in modify_map:
            result = _check_result(modify_map[section](edit.item_name, edit.field, edit.new_value))

        else:
            raise HTTPException(status_code=400,
                                detail=f"Unknown section '{section}'. Valid: experience, education, projects, skills, summary, contact, theme",
            )
        results.append(result)

    return {"results": results}


@resumeRouter.post("/resume/{id}/render")
def render_resume_default(id: str, background_tasks: BackgroundTasks):
    """Backward-compatible route that renders a resume as PDF (default format)."""
    return render_resume(id, "pdf", background_tasks)


@resumeRouter.post("/resume/{id}/render/{format}")
def render_resume(id: str, format: str, background_tasks: BackgroundTasks):
    """Re-render an existing resume to the specified format.

    Loads the resume YAML by ID, renders it via RenderCV in the requested
    format, and returns the file directly.

    Args:
        id: The resume identifier (name + UUID suffix from generation).
        format: Output format - one of 'pdf', 'html', or 'markdown'.
        background_tasks: FastAPI background tasks for post-response cleanup.

    Returns:
        FileResponse: The rendered file in the requested format.

    Raises:
        HTTPException: 400 if the format is not supported.
        HTTPException: 404 if the resume does not exist.
        HTTPException: 500 if rendering fails.
    """
    fmt = _validate_format(format)
    doc = _load_resume(id)
    rendered_path = _render_and_get_path(doc, fmt)

    background_tasks.add_task(shutil.rmtree, rendered_path.parent, True)

    media_types = {"pdf": "application/pdf", "html": "text/html", "markdown": "text/markdown"}

    return FileResponse(
        str(rendered_path),
        media_type=media_types[fmt],
        filename=f"resume_{id}.{EXTENSIONS[fmt]}",
        headers={"X-Resume-ID": id},
    )


@resumeRouter.post("/resume/{id}/export/{format}")
def export_resume(id: str, format: str):
    """Render a resume and save it to the default output directory.

    Renders the resume in the requested format and saves the file to
    User_config_files/rendered_outputs/.

    Args:
        id: The resume identifier.
        format: Output format - one of 'pdf', 'html', or 'markdown'.

    Returns:
        dict: {"status": "Saved successfully", "path": "<saved file path>"}.

    Raises:
        HTTPException: 400 if the format is not supported.
        HTTPException: 404 if the resume does not exist.
        HTTPException: 500 if rendering fails.
    """
    fmt = _validate_format(format)
    doc = _load_resume(id)
    rendered_path = _render_and_get_path(doc, fmt)

    RENDERED_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RENDERED_OUTPUTS_DIR / f"resume_{id}.{EXTENSIONS[fmt]}"
    shutil.copy2(rendered_path, dest)
    shutil.rmtree(rendered_path.parent, True)

    return {"status": "Saved successfully", "path": str(dest)}


@resumeRouter.post("/resume/{id}/export/{format}/custom")
def export_resume_custom(id: str, format: str, payload: SaveRequest):
    """Render a resume and save it to a custom location.

    Renders the resume in the requested format and saves the file to
    the directory specified in the request body.

    Args:
        id: The resume identifier.
        format: Output format - one of 'pdf', 'html', or 'markdown'.
        payload: SaveRequest with the target directory path.

    Returns:
        dict: {"status": "Saved successfully", "path": "<saved file path>"}.

    Raises:
        HTTPException: 400 if the format is not supported or directory does not exist.
        HTTPException: 404 if the resume does not exist.
        HTTPException: 500 if rendering fails.
    """
    fmt = _validate_format(format)
    target_dir = Path(payload.path).expanduser().resolve()
    if not target_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory '{payload.path}' does not exist")

    doc = _load_resume(id)
    rendered_path = _render_and_get_path(doc, fmt)

    dest = target_dir / f"resume_{id}.{EXTENSIONS[fmt]}"
    shutil.copy2(rendered_path, dest)
    shutil.rmtree(rendered_path.parent, True)

    return {"status": "Saved successfully", "path": str(dest)}


@resumeRouter.post("/resume/{id}/add/project/{project_name}")
def add_project(id: str, project_name: str, payload: Optional[ProjectRequest] = None):
    """Add a project entry to the resume from an analysed project in the database.

    Fetches the project analysis record by name, extracts the
    resume_item fields, and adds them as a new project on the resume.
    An optional ProjectRequest body can be provided to override any of the
    database values.

    Args:
        id: The resume identifier.
        project_name: The name of the analysed project in the database.
        payload: Optional ProjectRequest body to override database values.

    Returns:
        dict: {"status": "Successfully added project '<name>'"} on success.

    Raises:
        HTTPException: 400 if the project has no resume_item data.
        HTTPException: 404 if the resume or project record does not exist.
        HTTPException: 500 if an unexpected error occurs during save.
    """
    doc = _load_resume(id)

    candidates = [project_name]
    if not project_name.endswith(".json"):
        candidates.append(f"{project_name}.json")

    project_data = None
    for candidate in candidates:
        project_data = runtimeAppContext.store.fetch_by_name(candidate)
        if project_data is not None:
            break

    if project_data is None:
        raise HTTPException(status_code=404, detail=f"Project record '{project_name}' not found in database")

    resume_item = project_data.get("resume_item", {}) if isinstance(project_data, dict) else {}
    if not resume_item:
        raise HTTPException(status_code=400, detail=f"Project record '{project_name}' has no resume_item data")

    proj = Project(
        name=payload.name if payload and payload.name else resume_item.get("project_name", ""),
        start_date=payload.start_date if payload and payload.start_date else resume_item.get("start_date", "2025-01"),
        end_date=payload.end_date if payload and payload.end_date else resume_item.get("end_date", "2026-02"),
        location=payload.location if payload and payload.location else resume_item.get("location", "City, Country"),
        summary=payload.summary if payload and payload.summary else resume_item.get("summary"),
        highlights=payload.highlights if payload and payload.highlights else resume_item.get("highlights"),
    )
    try:
        result = _check_result(doc.add_project(proj))
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to add project: {e}")
    return {"status": result}


@resumeRouter.delete("/resume/{id}/project/{project_name}")
def remove_project(id: str, project_name: str):
    """Remove a project entry from an existing resume by project name.

    Args:
        id: The resume identifier.
        project_name: The exact project name to remove.

    Returns:
        dict: {"status": str} confirming the project was removed.

    Raises:
        HTTPException: 404 if the resume or project does not exist.
    """
    doc = _load_resume(id)
    result = doc.remove_project(project_name)
    if "not found" in result.lower() or "no projects" in result.lower():
        raise HTTPException(status_code=404, detail=result)
    return {"status": result}


@resumeRouter.post("/resume/{id}/add/education")
def add_education(id: str, payload: EducationRequest):
    """Add a new education entry to an existing resume.

    Args:
        id: The resume identifier.
        payload: Education details including institution, area, degree, dates, location, gpa, and highlights.

    Returns:
        dict: {"status": str} confirming the education was added.

    Raises:
        HTTPException: 404 if the resume does not exist.
        HTTPException: 409 if the institution already exists in the resume.
        HTTPException: 400 if the institution name is empty.
    """
    doc = _load_resume(id)
    edu = Education(
        institution=payload.institution,
        area=payload.area,
        degree=payload.degree,
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        gpa=payload.gpa,
        highlights=payload.highlights,
    )
    result = doc.add_education(edu)
    if "Duplicate" in result:
        raise HTTPException(status_code=409, detail=result)
    if result != "Successfully added education":
        raise HTTPException(status_code=400, detail=result)
    return {"status": result}


@resumeRouter.delete("/resume/{id}/education/{institution_name}")
def remove_education(id: str, institution_name: str):
    """Remove an education entry from an existing resume by institution name.

    Args:
        id: The resume identifier.
        institution_name: The exact institution name to remove.

    Returns:
        dict: {"status": str} confirming the education was removed.

    Raises:
        HTTPException: 404 if the resume or institution does not exist.
    """
    doc = _load_resume(id)
    result = doc.remove_education(institution_name)
    if "not found" in result.lower() or "no education to delete" in result.lower():
        raise HTTPException(status_code=404, detail=result)
    return {"status": result}


@resumeRouter.post("/resume/{id}/add/experience")
def add_experience(id: str, payload: ExperienceRequest):
    """Add a new work experience entry to an existing resume.

    Args:
        id: The resume identifier.
        payload: Experience details including company, position, dates, location, and highlights.

    Returns:
        dict: {"status": str} confirming the experience was added.

    Raises:
        HTTPException: 404 if the resume does not exist.
        HTTPException: 400 if the company name is empty or the operation fails.
    """
    doc = _load_resume(id)
    exp = Experience(
        company=payload.company,
        position=payload.position,
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        highlights=payload.highlights,
    )
    result = doc.add_experience(exp)
    if result != "Successfully added experience":
        raise HTTPException(status_code=400, detail=result)
    return {"status": result}


@resumeRouter.delete("/resume/{id}/experience/{company_name}")
def remove_experience(id: str, company_name: str):
    """Remove a work experience entry from an existing resume by company name.

    Args:
        id: The resume identifier.
        company_name: The exact company name to remove.

    Returns:
        dict: {"status": str} confirming the experience was removed.

    Raises:
        HTTPException: 404 if the resume or company does not exist.
    """
    doc = _load_resume(id)
    result = doc.remove_experience(company_name)
    if "not found" in result.lower() or "no experience to delete" in result.lower():
        raise HTTPException(status_code=404, detail=result)
    return {"status": result}


@resumeRouter.delete("/resume/{id}")
def delete_resume(id: str):
    """Delete a resume YAML file entirely from the system.

    Args:
        id: The resume identifier.

    Returns:
        dict: {"status": "Successfully deleted resume '<id>'"} on success.

    Raises:
        HTTPException: 404 if the resume does not exist.
        HTTPException: 500 if the file cannot be deleted (e.g., permission error).
    """
    doc = _load_resume(id)
    try:
        doc.yaml_file.unlink()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete resume: {e}")
    return {"status": f"Successfully deleted resume '{id}'"}
