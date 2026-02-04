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
    POST   /portfolio/generate                       - Create a new portfolio YAML document
    GET    /portfolio/{id}                           - Retrieve full portfolio data as JSON
    POST   /portfolio/{id}/edit                      - Modify a field on an existing section item
    POST   /portfolio/{id}/add/project/{project_id}  - Add a project entry
    POST   /portfolio/{id}/render                    - Re-render an existing portfolio to PDF
    DELETE /portfolio/{id}                           - Delete the portfolio YAML file entirely
"""

from typing import Optional,List
import uuid
import shutil
from fastapi import APIRouter, HTTPException,BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument,Project
)
from src.core.app_context import runtimeAppContext

portfolioRouter = APIRouter(tags=["Portfolio"])


"""Request / Response Models"""

class GeneratePortfolioRequest(BaseModel):
    """Request payload for creating a new portfolio document."""
    name: str
    theme: Optional[str]= 'sb2nov'
    overwrite:bool = False


class editItem(BaseModel):
    """Single edit operation specifying section, item, field, and new value."""
    section: str
    item_name: str
    field: str
    new_value: str


class EditProjectRequest(BaseModel):
    """Request payload containing a list of edit operations to apply."""
    edits: list[editItem]



class ProjectRequest(BaseModel):
    """Optional overrides for project fields when adding a project."""
    name:Optional[str] = None
    start_date:Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[list[str]] = None



"""----Helper Methods---"""
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
        raise HTTPException(status_code=404,detail=f"Portfolio '{name} not found'")

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
@portfolioRouter.post("/portfolio/generate")
def generate_portfolio(payload: GeneratePortfolioRequest):
    """Create a new portfolio YAML document.

    Args:
        payload: Request containing the name, optional theme, and overwrite flag.

    Returns:
        dict: The portfolio ID and a status message.

    Raises:
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
        doc.update_theme(payload.theme)

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

    Args:
        portfolio_id: The portfolio identifier.
        payload: A list of edit items specifying the section, field, and new value.

    Returns:
        dict: {"results": [str, ...]} with the outcome of each edit.

    Raises:
        HTTPException: 400 if an unknown section is specified.
        HTTPException: 404 if the portfolio does not exist.
    """
    doc=_load_portfolio(portfolio_id)
    modify_map={
        "projects": doc.modify_project,
    }
    results=[]
    result=""
    for edit in payload.edits:
        section=edit.section.lower()

        if section=="summary":
            result= doc.update_summary(str(edit.new_value))

        elif section=="contact":
            doc.update_contact(**{edit.field : edit.new_value})

        elif section == "theme":
            result=doc.update_theme(str(edit.new_value))

        elif section == "skills":
            result=doc.modify_skill(edit.item_name, edit.new_value)

        else:
            raise HTTPException(status_code=400,
                                detail=f"Unknown section '{section}'. Valid: projects, skills, summary, contact, theme",
                                )
        results.append(result)
    return {"results": results}


@portfolioRouter.post("/portfolio/{portfolio_id}/add/project/{project_id}")
def add_project(portfolio_id:str,project_id:int,payload: Optional[ProjectRequest]=None):
    """Add a project from the database to a portfolio.

    Args:
        portfolio_id: The portfolio identifier.
        project_id: The database ID of the project to add.
        payload: Optional overrides for project fields.

    Returns:
        dict: {"status": str} with the result of the operation.

    Raises:
        HTTPException: 404 if the portfolio or project does not exist.
        HTTPException: 500 if adding the project fails.
    """
    doc=_load_portfolio(portfolio_id)
    project_data=runtimeAppContext.store.fetch_by_id(project_id)
    if project_data is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found in database")
    resume_item=project_data.get("resume_item",{}) if isinstance(project_data,dict) else {}
    if not resume_item:
        raise HTTPException(status_code=404, detail=f"Project record {project_id} has no resume_item data")

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
def render_portfolio(portfolio_id: str, background_tasks: BackgroundTasks):
    """Render an existing portfolio to PDF.

    Use this after making edits to regenerate the PDF without creating
    a new portfolio.

    Args:
        portfolio_id: The portfolio identifier.
        background_tasks: FastAPI background tasks for cleanup after response.

    Returns:
        FileResponse: The rendered portfolio PDF.

    Raises:
        HTTPException: 404 if the portfolio does not exist.
        HTTPException: 500 if rendering fails.
    """
    doc = _load_portfolio(portfolio_id)
    status, pdf_path = doc.render()
    if pdf_path is None:
        raise HTTPException(status_code=500, detail=status)

    output_dir = pdf_path.parent
    background_tasks.add_task(shutil.rmtree, output_dir, True)
    return FileResponse(
        str(pdf_path),
        media_type='application/pdf',
        filename=f"portfolio_{portfolio_id}.pdf",
        headers={"X-Portfolio-ID": portfolio_id},
    )


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