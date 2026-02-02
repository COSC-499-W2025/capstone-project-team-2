"""
FastAPI endpoints for resume generation and editing via RenderCV.

Provides a RESTFUL API for creating, reading, updating, and deleting
resume documents backed by RenderCV YAML files. Resumes are identified
by a unique ID (name + UUID suffix) returned in the X-Resume-ID header
upon generation.

Endpoints:
    POST   /resume/generate          - Create a new resume and render to PDF
    GET    /resume/{id}              - Retrieve full resume data as JSON
    POST   /resume/{id}/edit         - Modify a field on an existing section item
    POST   /resume/{id}/add/project/{project_id}  - Add a project entry
    DELETE /resume/{id}              - Delete the resume YAML file entirely
"""

from typing import Optional, List, Any
import uuid
import shutil
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument,
    Project,
)
from src.core.app_context import runtimeAppContext


resumeRouter = APIRouter()

"""Request / Response Models"""

class GenerateResumeRequest(BaseModel):
    """Request payload for generating a new resume.

    Attributes:
        name: The person's name used as the base filename.
        theme: RenderCV theme to apply. Defaults to 'sb2nov'.
               Valid: classic, engineeringclassic, engineeringresumes, moderncv, sb2nov.
        overwrite: If True, replaces an existing resume with the same name.
    """
    name: str
    theme: Optional[str] = 'sb2nov'
    overwrite: bool = False

class EditItem(BaseModel):
    """A single edit operation on a resume section item.

    Attributes:
        section: The section to edit. Valid: experience, education, projects,
                 skills, summary, contact, theme.
        item_name: Identifier for the item within the section (e.g., company
                   name for experience, institution for education).
        field: The specific field to modify (e.g., 'position', 'area').
        new_value: The new value to set for the field.
    """
    section: str
    item_name: str
    field: str
    new_value: str

class EditResumeRequest(BaseModel):
    """Request payload for editing one or more resume section items.

    Attributes:
        edits: A list of edit operations to apply.
    """
    edits: List[EditItem]

class ContactUpdateRequest(BaseModel):
    """Request payload for updating contact information.

    Attributes:
        email: Email address to display.
        phone: Phone number with country code.
        location: City and state/country.
        website: Personal website URL.
        name: Full name to display at the top of the CV.
    """
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    name: Optional[str] = None

class ExperienceRequest(BaseModel):
    """Request payload for adding a work experience entry.

    Attributes:
        company: Name of the company (required).
        position: Job title or role held.
        start_date: Start date in 'YYYY-MM' format.
        end_date: End date in 'YYYY-MM' format, or 'present'.
        location: City, State or City, Country.
        highlights: List of accomplishments or responsibilities.
    """
    company: str
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[List[str]] = None

class ProjectRequest(BaseModel):
    """Optional overrides when adding a project entry.

    Any field provided here takes precedence over the value pulled
    from the database.  All fields are optional.

    Attributes:
        name: Name of the project.
        start_date: Start date in 'YYYY-MM' format.
        end_date: End date in 'YYYY-MM' format.
        location: City, State or City, Country.
        summary: Brief description of the project.
        highlights: List of key features or accomplishments.
    """
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None


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

def _check_result(result: str):
    """Validate the result string from a RenderCVDocument operation.

    Args:
        result: Status message returned by a RenderCVDocument method.

    Returns:
        str: The result string if it indicates success.

    Raises:
        HTTPException: 400 if the result does not contain 'Successfully'.
    """
    if "Successfully" not in result:
        raise HTTPException(status_code=400, detail=result)
    return result


@resumeRouter.post("/resume/generate")
def generate_resume(payload: GenerateResumeRequest, background_tasks: BackgroundTasks):
    """Create a new resume from a starter template and render it to PDF.

    Generates a unique resume ID by appending a UUID suffix to the provided name.
    The YAML file is created, optionally themed, and rendered to PDF via RenderCV.
    The rendercv_output directory is cleaned up after the PDF response is sent.

    Args:
        payload: GenerateResumeRequest with name, optional theme, and overwrite flag.
        background_tasks: FastAPI background tasks for post-response cleanup.

    Returns:
        FileResponse: The rendered PDF file with content-type application/pdf.
            Includes X-Resume-ID header with the full resume identifier.

    Raises:
        HTTPException: 409 if resume already exists and overwrite is False.
        HTTPException: 500 if PDF rendering fails.
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
        doc.update_theme(payload.theme)

    status, pdf_path = doc.render()
    if pdf_path is None:
        raise HTTPException(status_code=500, detail=status)

    output_dir = pdf_path.parent
    background_tasks.add_task(shutil.rmtree, output_dir, True)

    return FileResponse(str(pdf_path), media_type='application/pdf', filename=f"resume_{full_name}.pdf",
                        headers={"X-Resume-ID": full_name})


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

    Supports editing items within experience, education, projects, and skills
    sections by item name and field. Also supports updating the summary,
    contact fields, and theme directly. Multiple edits can be submitted
    in a single request.

    Args:
        id: The resume identifier.
        payload: EditResumeRequest with a list of edits to apply.

    Returns:
        dict: {"results": [...]} with the status of each edit.

    Raises:
        HTTPException: 400 if any section is unknown or an item/field is not found.
        HTTPException: 404 if the resume does not exist.
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
            result = doc.update_summary(str(edit.new_value))

        elif section == "contact":
            # ** unpacks the dict into a keyword argument so the dynamic
            # field name (e.g. "email") is passed as update_contact(email=new_value)
            doc.update_contact(**{edit.field: edit.new_value})
            result = f"Successfully updated contact field '{edit.field}'"

        elif section == "theme":
            result = doc.update_theme(str(edit.new_value))

        elif section == "skills":
            result = doc.modify_skill(edit.item_name, edit.new_value)

        elif section in modify_map:
            result = modify_map[section](edit.item_name, edit.field, edit.new_value)

        else:
            raise HTTPException(status_code=400,
                                detail=f"Unknown section '{section}'. Valid: experience, education, projects, skills, summary, contact, theme",
            )
        results.append(result)

    return {"results": results}




@resumeRouter.post("/resume/{id}/add/project/{project_id}")
def add_project(id: str, project_id: int, payload: Optional[ProjectRequest] = None):
    """Add a project entry to the resume from an analysed project in the database.

    Fetches the project analysis record by its database row ID, extracts the
    resume_item fields, and adds them as a new project on the resume.
    An optional ProjectRequest body can be provided to override any of the
    database values.

    Args:
        id: The resume identifier.
        project_id: The database row ID of the analysed project.
        payload: Optional ProjectRequest body to override database values.

    Returns:
        dict: {"status": "Successfully added project '<name>'"} on success.

    Raises:
        HTTPException: 400 if the project has no resume_item data.
        HTTPException: 404 if the resume or project record does not exist.
        HTTPException: 500 if an unexpected error occurs during save.
    """
    doc = _load_resume(id)

    project_data = runtimeAppContext.store.fetch_by_id(project_id)
    if project_data is None:
        raise HTTPException(status_code=404, detail=f"Project record '{project_id}' not found in database")

    analysis = project_data if isinstance(project_data, dict) else {}
    if "analysis" in analysis and isinstance(analysis["analysis"], dict):
        analysis = analysis["analysis"]

    resume_item = analysis.get("resume_item", {})
    if not resume_item:
        raise HTTPException(status_code=400, detail=f"Project record '{project_id}' has no resume_item data")

    proj = Project(
        name=payload.name if payload and payload.name else resume_item.get("project_name", ""),
        start_date=payload.start_date if payload and payload.start_date else "2025-01",
        end_date=payload.end_date if payload and payload.end_date else "2026-02",
        location=payload.location if payload and payload.location else "N/A",
        summary=payload.summary if payload and payload.summary else resume_item.get("summary"),
        highlights=payload.highlights if payload and payload.highlights else resume_item.get("highlights"),
    )
    try:
        result = _check_result(doc.add_project(proj))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add project: {e}")
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


