

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

portfolioRouter = APIRouter()


"""Request / Response Models"""

class GeneratePorfirioRequest(BaseModel):
    name: str
    theme: Optional[str]= 'sb2nov'
    overwrite:bool = False


class editItem(BaseModel):
    section: str
    item_name: str
    field: str
    new_value: str


class EditProjectRequest(BaseModel):
    edits: list[editItem]



class ProjectRequest(BaseModel):
    name:Optional[str] = None
    start_date:Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[list[str]] = None



"""----Helper Methods---"""
def _load_portfolio(name:str) -> RenderCVDocument:
    doc=RenderCVDocument(doc_type='portfolio')
    try:
        doc.load(name=name)

    except FileNotFoundError:
        raise HTTPException(status_code=404,detail=f"Portfolio '{name} not found'")

    return doc

def _check_result(result:str):
    if "Successfully" not in result:
        raise HTTPException(status_code=400,detail=result)
    return result

"""---API Calls/Requests---"""
@portfolioRouter.post("/portfolio/generate")
def generate_portfolio(payload: GeneratePorfirioRequest, background_tasks: BackgroundTasks):
    doc=RenderCVDocument(doc_type='portfolio')
    portfolio_id=str(uuid.uuid4())[:8]
    full_name=f"{payload.name}_{portfolio_id}"
    gen_result=doc.generate(name=full_name,overwrite=payload.overwrite)
    if gen_result=="Skipping generation":
        raise HTTPException(status_code=404,detail=f" portfolio {full_name}.pdf. Set Overwrite=true to replace it")

    doc.load(name=full_name)
    if payload.theme and payload.theme !='sb2nov':
        doc.update_theme(payload.theme)


    status,pdf_path= doc.render()
    if pdf_path is None:
        raise HTTPException(status_code=500,detail=status)

    output_dir=pdf_path.parent
    background_tasks.add_task(shutil.rmtree, output_dir,True)
    return FileResponse(str(pdf_path), media_type='application/pdf', filename=f"portfolio_{full_name}.pdf",
                        headers={"X-Portfolio-ID": full_name})


@portfolioRouter.get("/portfolio/{portfolio_id}")
def get_portfolio(portfolio_id: str):
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
