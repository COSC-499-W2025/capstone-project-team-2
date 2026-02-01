"""
FASTAPI endpoints for resume generation and editing via RenderCV

"""
from typing import Optional,List,Any
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument,
    Project,
    Experience,
    Education,
    Skills,
    Connections,
)


resumeRouter = APIRouter()

"""Request / Response Models"""


class GenerateResumeRequest(BaseModel):
    name:str
    theme: Optional[str] = 'sb2nov'
    overwrite: bool = False

class EditResumeRequest(BaseModel):
    section: str
    item_name: str
    field: str
    new_value: str

class ContactUpdateRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    name: Optional[str] = None

class ExperienceRequest(BaseModel):
    company: str
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[List[str]] = None


class EducationRequest(BaseModel):
    institution: str
    area: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    gpa: Optional[str] = None
    highlights: Optional[List[str]] = None


class ProjectRequest(BaseModel):
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None

class SkillsRequest(BaseModel):
    label: str
    details: str

"""-------Helper Methods-------"""
def _load_resume(name:str) ->RenderCVDocument:
    doc=RenderCVDocument(doc_type="resume")
    try:
        doc.load(name=name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Resume '{name}' not found")
    return doc

"""POST /Resume/generate"""
@resumeRouter.post("/resume/generate")
def generate_resume(payload: GenerateResumeRequest):
    doc=RenderCVDocument(doc_type="resume")
    resume_id=str(uuid.uuid4())[:8]
    full_name=f"{payload.name}_{resume_id}"


    gen_result=doc.generate(name=full_name,overwrite=payload.overwrite)

    if gen_result== "Skipping generation":
        raise HTTPException(status_code=409,
                            detail=f"Resume '{payload.name}' already exists. Set overwrite=true to replace it.",
                            )
    doc.load(name=full_name)

    if payload.theme and payload.theme != 'sb2nov':
        doc.update_theme(payload.theme)

    status,pdf_path=doc.render()
    if pdf_path is None:
        raise HTTPException(status_code=500,detail=status)

    return FileResponse(str(pdf_path),media_type='application/pdf',filename=f"resume_{full_name}.pdf",
                        headers={"X-Resume-ID": full_name})

"""GET /resume/{id}"""
@resumeRouter.get("/resume/{id}")
def get_resume(id: str):
    doc=_load_resume(id)
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
