

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


@portfolioRouter.get("/portfolio/{id}")
def get_portfolio(id: str):
    doc=_load_portfolio(id)
    return {
        "name": id,
        "contact": doc.get_contact_info(),
        "theme": doc.get_theme(),
        "summary": doc.get_summary(),
        "projects": doc.get_projects(),
        "skills": doc.get_skills(),
        "connections": doc.get_connections(),
    }

@portfolioRouter.post("/portfolio/{id}/edit")
def edit_portfolio(id:str,payload: EditProjectRequest):
    doc=_load_portfolio(id)
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

