"""
FastAPI endpoints for portfolio generation and editing via RenderCV.

Provides a RESTFUL API for creating, reading, updating, and deleting
portfolio documents backed by RenderCV YAML files. Portfolios are identified
by a unique ID (name + UUID suffix) returned in the X-Portfolio-ID header
upon generation.

Portfolios differ from resumes in that they do NOT include education or
experience sections. They focus on projects, skills, summary, contact,
and connections.

Endpoints:
    POST   /portfolio/generate                              - Create a new portfolio YAML document
    GET    /portfolio/{id}                                - Retrieve full portfolio data as JSON
    POST   /portfolio/{id}/edit                           - Modify a field on an existing section item
    POST   /portfolio/{id}/add/project/manual              - Add a project entry with manual data (no DB lookup)
    POST   /portfolio/{id}/add/project/{project_name}     - Add a project entry from the database
    DELETE /portfolio/{id}/project/{project_name}          - Remove a project entry
    POST   /portfolio/{id}/add/skill                      - Add a new skill category
    POST   /portfolio/{id}/skill/{label}/append           - Append items to an existing skill category
    DELETE /portfolio/{id}/skill/{label}                  - Remove a skill category
    POST   /portfolio/{id}/render/{format}                - Re-render and return as file response
    POST   /portfolio/{id}/export/{format}                - Render and export to default directory
    POST   /portfolio/{id}/export/{format}/custom         - Render and export to a custom directory
    DELETE /portfolio/{id}                                - Delete the portfolio YAML file entirely
"""

from typing import Optional,List
from pathlib import Path
import uuid
import shutil
from fastapi import APIRouter, HTTPException,BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument,Project
)
from src.reporting.portfolio_service import (
    load_portfolio_showcase,
    save_project_role_override,
)
from src.core.app_context import runtimeAppContext

RENDERED_OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "User_config_files" / "Generate_render_CV_files" / "rendered_outputs"

portfolioRouter = APIRouter(tags=["Portfolio"])


"""Request / Response Models"""

class GeneratePortfolioRequest(BaseModel):
    """Request payload for creating a new portfolio document."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "Jane_Doe",
        "theme": "sb2nov",
        "overwrite": False,
    }})
    name: str
    theme: Optional[str]= 'sb2nov'
    overwrite:bool = False


class editItem(BaseModel):
    """Single edit operation specifying section, item, field, and new value."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "section": "contact",
        "item_name": "",
        "field": "email",
        "new_value": "jane.doe@example.com",
    }})
    section: str
    item_name: str
    field: str
    new_value: str


class EditProjectRequest(BaseModel):
    """Request payload containing a list of edit operations to apply."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "edits": [
            {"section": "contact", "item_name": "", "field": "email", "new_value": "jane.doe@example.com"},
            {"section": "contact", "item_name": "", "field": "phone", "new_value": "555-987-6543"},
            {"section": "summary", "item_name": "", "field": "", "new_value": "Full-stack developer passionate about open source."},
            {"section": "projects", "item_name": "MyProject", "field": "summary", "new_value": "Developed a portfolio site with FastAPI."},
            {"section": "theme", "item_name": "", "field": "", "new_value": "classic"},
        ]
    }})
    edits: list[editItem]



class ProjectRequest(BaseModel):
    """Optional overrides for project fields when adding a project."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "My Capstone Project",
        "start_date": "2024-09",
        "end_date": "2025-04",
        "location": "Kelowna, BC",
        "summary": "Built a developer portfolio generation tool using FastAPI and RenderCV.",
        "highlights": ["Designed REST API with FastAPI", "Integrated RenderCV for PDF generation"],
    }})
    name:Optional[str] = None
    start_date:Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[list[str]] = None


class ProjectRoleOverrideRequest(BaseModel):
    """Request payload for setting a project's showcase role."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "role": "Backend Developer",
    }})
    role: str = Field(default="Backend Developer", max_length=200)

class ManualProjectRequest(BaseModel):
    """Payload for adding a project directly without a database entry."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "name": "My Side Project",
        "start_date": "2024-01",
        "end_date": "2025-03",
        "location": "Vancouver, BC",
        "summary": "A personal project built to explore Rust async runtimes.",
        "highlights": ["Implemented async runtime", "Achieved 10k RPS under load"],
    }})
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[list[str]] = None


class  skillRequest(BaseModel):
    """Payload for adding a new a skill"""
    model_config = ConfigDict(json_schema_extra={
        "example":{
            "label":"Languages",
            "details": "Python, Java, C++"
        }
    })
    label: str
    details: str

class AppendSkillRequest(BaseModel):
    """Payload for appending items to an existing skill category"""
    model_config = ConfigDict(json_schema_extra={"example": {
        "details": "Rust, TypeScript",
    }})
    details: str





class SaveRequest(BaseModel):
    """Payload for saving a rendered file to a custom location."""
    model_config = ConfigDict(json_schema_extra={"example": {
        "path": "/home/user/Documents/portfolios",
    }})
    path: str


SUPPORTED_FORMATS = {"pdf", "html", "markdown"}
EXTENSIONS = {"pdf": "pdf", "html": "html", "markdown": "md"}

"""----Helper Methods---"""

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

def _load_portfolio(name:str) -> RenderCVDocument:
    """Load an existing portfolio by name.

    Args:
        name: The portfolio identifier used as the filename.

    Returns:
        RenderCVDocument: The loaded portfolio document.

    Raises:
        HTTPException: 404 if the portfolio file does not exist.
    """
    doc=RenderCVDocument(doc_type='portfolio')
    try:
        doc.load(name=name)

    except FileNotFoundError:
        raise HTTPException(status_code=404,detail=f"Portfolio '{name}' not found'")

    return doc

def _check_result(result:str):
    """Validate that an operation result indicates success.

    Args:
        result: The result string returned by a RenderCVDocument operation.

    Returns:
        str: The result string if it contains "Successfully".

    Raises:
        HTTPException: 400 if the result does not indicate success.
    """
    if "Successfully" not in result:
        raise HTTPException(status_code=400,detail=result)
    return result

"""---API Calls/Requests---"""

@portfolioRouter.post("/portfolio-showcase/{project_name}/role")
def set_portfolio_showcase_role(project_name: str, payload: ProjectRoleOverrideRequest):
    """
    Save a human-authored role override for a project's portfolio showcase.

    Args:
        project_name: Project name used for override storage.
        payload: Contains role text to persist.

    Returns:
        dict: Saved project name and role.
    """
    role = payload.role.strip()
    if not role:
        raise HTTPException(status_code=400, detail="Role cannot be empty.")

    try:
        saved = save_project_role_override(project_name, role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save role override: {e}")

    return {
        "project_name": project_name,
        "role": saved.get("project", {}).get("role"),
        "status": "Role override saved successfully",
    }


@portfolioRouter.get("/portfolio-showcase/{project_name}/role")
def get_portfolio_showcase_role(project_name: str):
    """
    Return the saved role override for a project's portfolio showcase.

    Args:
        project_name: Project name used for override lookup.

    Returns:
        dict: Project role if found.
    """
    overrides = load_portfolio_showcase(project_name)
    role = (overrides.get("project") or {}).get("role")
    if not role:
        raise HTTPException(status_code=404, detail=f"No saved role for project '{project_name}'.")

    return {"project_name": project_name, "role": role}


@portfolioRouter.post("/portfolio/generate")
def generate_portfolio(payload: GeneratePortfolioRequest):
    """Create a new portfolio YAML document.

    Args:
        payload: Request containing the name, optional theme, and overwrite flag.

    Returns:
        dict: The portfolio ID and a status message.

    Raises:
        HTTPException: 400 if the theme is invalid.
        HTTPException: 409 if a portfolio with the same name exists and overwrite is False.
    """
    doc=RenderCVDocument(doc_type='portfolio')
    portfolio_id=str(uuid.uuid4())[:8]
    full_name=f"{payload.name}_{portfolio_id}"
    gen_result=doc.generate(name=full_name,overwrite=payload.overwrite)
    if gen_result=="Skipping generation":
        raise HTTPException(status_code=409,detail=f"Portfolio {full_name} already exists. Set overwrite=true to replace it")

    doc.load(name=full_name)
    if payload.theme and payload.theme !='sb2nov':
        try:
            doc.update_theme(payload.theme)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"portfolio_id": full_name, "status": "Portfolio created successfully"}


@portfolioRouter.get("/portfolio/{portfolio_id}")
def get_portfolio(portfolio_id: str):
    """Retrieve all sections of an existing portfolio.

    Args:
        portfolio_id: The portfolio identifier.

    Returns:
        dict: Portfolio data including contact, theme, summary, projects, skills, and connections.

    Raises:
        HTTPException: 404 if the portfolio does not exist.
    """
    doc=_load_portfolio(portfolio_id)
    return {
        "name": portfolio_id,
        "contact": doc.get_contact_info(),
        "theme": doc.get_theme(),
        "summary": doc.get_summary(),
        "projects": doc.get_projects(),
        "skills": doc.get_skills(),
        "connections": doc.get_connections(),
    }

@portfolioRouter.post("/portfolio/{portfolio_id}/edit")
def edit_portfolio(portfolio_id:str,payload: EditProjectRequest):
    """Apply one or more edits to a portfolio's sections.

    Supports batch editing multiple fields across different sections in a single
    API call. Each edit in the list is applied sequentially.

    Args:
        portfolio_id: The portfolio identifier.
        payload: A list of edit items specifying the section, field, and new value.

    Returns:
        dict: {"results": [str, ...]} with the outcome of each edit.

    Raises:
        HTTPException: 400 if an unknown section is specified or theme is invalid.
        HTTPException: 404 if the portfolio does not exist.

    Example - Single edit:
        ```json
        {
            "edits": [
                {"section": "summary", "item_name": "", "field": "", "new_value": "Software engineer with 5 years experience"}
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
        - projects: Use `item_name` for the project name, `field` for the attribute to change.
    """
    doc=_load_portfolio(portfolio_id)
    results=[]
    for edit in payload.edits:
        section=edit.section.lower()

        if section=="summary":
            result= doc.update_summary(str(edit.new_value))

        elif section=="contact":
            doc.update_contact(**{edit.field : edit.new_value})
            result = f"Successfully updated contact field '{edit.field}'"

        elif section == "theme":
            try:
                result=doc.update_theme(str(edit.new_value))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        elif section == "skills":
            result=doc.modify_skill(edit.item_name, edit.new_value)

        elif section == "projects":
            result=doc.modify_project(edit.item_name, edit.field, edit.new_value)

        else:
            raise HTTPException(status_code=400,
                                detail=f"Unknown section '{section}'. Valid: projects, skills, summary, contact, theme",
                                )
        results.append(result)
    return {"results": results}


@portfolioRouter.post("/portfolio/{portfolio_id}/add/project/manual")
def add_project_manual(portfolio_id: str, payload: ManualProjectRequest):
    """Add a project entry to the portfolio with fully manual data.

    Unlike POST /portfolio/{id}/add/project/{project_name}, this endpoint does not
    require the project to exist in the database. All project fields are supplied
    directly in the request body.

    Args:
        portfolio_id: The portfolio identifier.
        payload: ManualProjectRequest with all project fields provided directly.

    Returns:
        dict: {"status": str} confirming the project was added.

    Raises:
        HTTPException: 404 if the portfolio does not exist.
        HTTPException: 400 if adding the project fails.
        HTTPException: 500 if an unexpected error occurs.
    """
    doc = _load_portfolio(portfolio_id)
    proj = Project(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        summary=payload.summary,
        highlights=payload.highlights,
    )
    try:
        result = _check_result(doc.add_project(proj))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add project: {e}")
    return {"status": result}


@portfolioRouter.post("/portfolio/{portfolio_id}/add/project/{project_name}")
def add_project(portfolio_id: str, project_name: str, payload: Optional[ProjectRequest] = None):
    """Add a project from the database to a portfolio.

    Args:
        portfolio_id: The portfolio identifier.
        project_name: The project name (Pname) of the analysed project.
        payload: Optional overrides for project fields.

    Returns:
        dict: {"status": str} with the result of the operation.

    Raises:
        HTTPException: 404 if the portfolio or project does not exist.
        HTTPException: 500 if adding the project fails.
    """
    doc=_load_portfolio(portfolio_id)
    candidates = [project_name]
    if not project_name.endswith(".json"):
        candidates.append(f"{project_name}.json")

    project_data = None
    for candidate in candidates:
        project_data = runtimeAppContext.store.fetch_by_name(candidate)
        if project_data is not None:
            break

    if project_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_name}' not found in database",
        )
    resume_item=project_data.get("resume_item",{}) if isinstance(project_data,dict) else {}
    if not resume_item:
        raise HTTPException(
            status_code=404,
            detail=f"Project record '{project_name}' has no resume_item data",
        )

    proj= Project(
        name=payload.name if payload and payload.name else resume_item.get("project_name",""),
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

@portfolioRouter.post("/portfolio/{portfolio_id}/render")
def render_portfolio_default(portfolio_id: str, background_tasks: BackgroundTasks):
    """Backward-compatible route that renders a portfolio as PDF (default format)."""
    return render_portfolio(portfolio_id, "pdf", background_tasks)


@portfolioRouter.post("/portfolio/{portfolio_id}/render/{format}")
def render_portfolio(portfolio_id: str, format: str, background_tasks: BackgroundTasks):
    """Render an existing portfolio to the specified format.

    Use this after making edits to regenerate the output without creating
    a new portfolio.

    Args:
        portfolio_id: The portfolio identifier.
        format: Output format - one of 'pdf', 'html', or 'markdown'.
        background_tasks: FastAPI background tasks for cleanup after response.

    Returns:
        FileResponse: The rendered portfolio file in the requested format.

    Raises:
        HTTPException: 400 if the format is not supported.
        HTTPException: 404 if the portfolio does not exist.
        HTTPException: 500 if rendering fails.
    """
    fmt = _validate_format(format)
    doc = _load_portfolio(portfolio_id)
    rendered_path = _render_and_get_path(doc, fmt)

    background_tasks.add_task(shutil.rmtree, rendered_path.parent, True)

    media_types = {"pdf": "application/pdf", "html": "text/html", "markdown": "text/markdown"}

    return FileResponse(
        str(rendered_path),
        media_type=media_types[fmt],
        filename=f"portfolio_{portfolio_id}.{EXTENSIONS[fmt]}",
        headers={"X-Portfolio-ID": portfolio_id},
    )


@portfolioRouter.post("/portfolio/{portfolio_id}/export/{format}")
def export_portfolio(portfolio_id: str, format: str):
    """Render a portfolio and save it to the default output directory.

    Renders the portfolio in the requested format and saves the file to
    User_config_files/rendered_outputs/.

    Args:
        portfolio_id: The portfolio identifier.
        format: Output format - one of 'pdf', 'html', or 'markdown'.

    Returns:
        dict: {"status": "Saved successfully", "path": "<saved file path>"}.

    Raises:
        HTTPException: 400 if the format is not supported.
        HTTPException: 404 if the portfolio does not exist.
        HTTPException: 500 if rendering fails.
    """
    fmt = _validate_format(format)
    doc = _load_portfolio(portfolio_id)
    rendered_path = _render_and_get_path(doc, fmt)

    RENDERED_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = RENDERED_OUTPUTS_DIR / f"portfolio_{portfolio_id}.{EXTENSIONS[fmt]}"
    shutil.copy2(rendered_path, dest)
    shutil.rmtree(rendered_path.parent, True)

    return {"status": "Saved successfully", "path": str(dest)}


@portfolioRouter.post("/portfolio/{portfolio_id}/export/{format}/custom")
def export_portfolio_custom(portfolio_id: str, format: str, payload: SaveRequest):
    """Render a portfolio and save it to a custom location.

    Renders the portfolio in the requested format and saves the file to
    the directory specified in the request body.

    Args:
        portfolio_id: The portfolio identifier.
        format: Output format - one of 'pdf', 'html', or 'markdown'.
        payload: SaveRequest with the target directory path.

    Returns:
        dict: {"status": "Saved successfully", "path": "<saved file path>"}.

    Raises:
        HTTPException: 400 if the format is not supported or directory does not exist.
        HTTPException: 404 if the portfolio does not exist.
        HTTPException: 500 if rendering fails.
    """
    fmt = _validate_format(format)
    target_dir = Path(payload.path).expanduser().resolve()
    if not target_dir.is_dir():
        raise HTTPException(status_code=400, detail=f"Directory '{payload.path}' does not exist")

    doc = _load_portfolio(portfolio_id)
    rendered_path = _render_and_get_path(doc, fmt)

    dest = target_dir / f"portfolio_{portfolio_id}.{EXTENSIONS[fmt]}"
    shutil.copy2(rendered_path, dest)
    shutil.rmtree(rendered_path.parent, True)

    return {"status": "Saved successfully", "path": str(dest)}


@portfolioRouter.delete("/portfolio/{portfolio_id}/project/{project_name}")
def remove_project(portfolio_id: str, project_name: str):
    """Remove a project entry from an existing portfolio by project name.

    Args:
        portfolio_id: The portfolio identifier.
        project_name: The exact project name to remove.

    Returns:
        dict: {"status": str} confirming the project was removed.

    Raises:
        HTTPException: 404 if the portfolio or project does not exist.
    """
    doc = _load_portfolio(portfolio_id)
    result = doc.remove_project(project_name)
    if "not found" in result.lower() or "no projects" in result.lower():
        raise HTTPException(status_code=404, detail=result)
    return {"status": result}




@portfolioRouter.post("/portfolio/{portfolio_id}/add/skill")
def add_skill(portfolio_id: str, payload:skillRequest):
    """Add a new skill category entry to an existing portfolio.

        Args:
            portfolio_id: The portfolio identifier.
            payload: SkillRequest with a label (category name) and details (comma-separated skills).

        Returns:
            dict: {"status": str} confirming the skill was added.

        Raises:
            HTTPException: 404 if the portfolio does not exist.
            HTTPException: 409 if a skill with the same label already exists.
            HTTPException: 400 if the label is empty or the operation fails.
        """
    doc = _load_portfolio(portfolio_id)
    result = doc.add_skills(payload.label, payload.details)

    if "Duplicate" in result:
        raise HTTPException(status_code=409, detail=result)
    if result != "Successfully added skills":
        raise HTTPException(status_code=400, detail=result)
    return {"status": result}




@portfolioRouter.post("/portfolio/{portfolio_id}/skill/{label}/append")
def append_skill(portfolio_id:str,label:str,payload:AppendSkillRequest):
    """Append a skill to an existing skill category in a portfolio.

       Args:
           portfolio_id: The portfolio identifier.
           label: The exact skill category label to append to (e.g., 'Languages').
           payload: The skill data to append.

       Returns:
           dict: {"status": str} confirming the skill was appended.

       Raises:
           HTTPException: 404 if the portfolio or skill label does not exist.
       """

    doc = _load_portfolio(portfolio_id)
    existing_skills = next((skill for skill in doc.get_skills() if skill.get("label") == label), None)
    if existing_skills is None:
        raise HTTPException(status_code=404, detail=f"Skill '{label}' not found")

    current = existing_skills.get("details", "").strip().rstrip(",")
    new_details = f"{current}, {payload.details.strip()}" if current else payload.details.strip()
    result = _check_result(doc.modify_skill(label, new_details))
    return {"status": result, "details": new_details}





@portfolioRouter.delete("/portfolio/{portfolio_id}/skill/{label}")
def remove_skill(portfolio_id: str, label: str):
    """Remove an entire skill category from an existing portfolio by label.

       Args:
           portfolio_id: The portfolio identifier.
           label: The exact skill category label to remove (e.g., 'Languages').

       Returns:
           dict: {"status": str} confirming the skill category was removed.

       Raises:
           HTTPException: 404 if the portfolio or skill label does not exist.
       """
    doc = _load_portfolio(portfolio_id)
    result = doc.remove_skill(label)
    if "not found" in result.lower() or "no skills" in result.lower():
        raise HTTPException(status_code=404, detail=result)
    return {"status": result}


@portfolioRouter.delete("/portfolio/{portfolio_id}")
def delete_portfolio(portfolio_id: str):
    """Delete a portfolio YAML file entirely from the system.

    Args:
        portfolio_id: The portfolio identifier.

    Returns:
        dict: {"status": "Successfully deleted portfolio '<portfolio_id>'"} on success.

    Raises:
        HTTPException: 404 if the portfolio does not exist.
        HTTPException: 500 if the file cannot be deleted (e.g., permission error).
    """
    doc = _load_portfolio(portfolio_id)
    try:
        doc.yaml_file.unlink()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete portfolio: {e}")
    return {"status": f"Successfully deleted portfolio '{portfolio_id}'"}
