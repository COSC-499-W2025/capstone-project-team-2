"""
FASTAPI endpoints for resume generation and editing via RenderCV

"""
from typing import Optional,List,Any
import uuid
import shutil
from fastapi import APIRouter, HTTPException, BackgroundTasks
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

class RemoveItemRequest(BaseModel):
    section: str
    item_name: str

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
def generate_resume(payload: GenerateResumeRequest, background_tasks: BackgroundTasks):
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

    output_dir = pdf_path.parent
    background_tasks.add_task(shutil.rmtree, output_dir, True)

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

"""POST /Resume/{id}/edit"""
@resumeRouter.post("/resume/{id}/edit")
def edit_resume(id:str,payload: EditResumeRequest):
    doc=_load_resume(id)
    section=payload.section.lower()
    modify_map = {
        "experience": lambda: doc.modify_experience(payload.item_name, payload.field, payload.new_value),
        "education": lambda: doc.modify_education(payload.item_name, payload.field, payload.new_value),
        "projects": lambda: doc.modify_project(payload.item_name, payload.field, payload.new_value),
        "skills": lambda: doc.modify_skill(payload.item_name, payload.new_value),
    }
    if section=="summary":
        result=doc.update_summary(str(payload.new_value))

    elif section=="contact":
        doc.update_contact(**{payload.field: payload.new_value})
        result = f"Successfully updated contact field '{payload.field}'"

    elif section == "theme":
        result = doc.update_theme(str(payload.new_value))

    elif section in modify_map:
        result = modify_map[section]()

    else:
        raise HTTPException(status_code=400,
                            detail=f"Unknown section '{section}'. Valid: experience, education, projects, skills, summary, contact, theme",
)
    return {"status": result}

def _check_result(result: str):
    """Raise 400 if the RenderCVDocument operation did not succeed."""
    if "Successfully" not in result:
        raise HTTPException(status_code=400, detail=result)
    return result

"""POST /resume/{id}/add"""
@resumeRouter.post("/resume/{id}/add/experience")
def add_experience(id: str, payload: ExperienceRequest):
    doc = _load_resume(id)
    exp = Experience(
        company=payload.company,
        position=payload.position,
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        highlights=payload.highlights,
    )
    try:
        result = _check_result(doc.add_experience(exp))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add experience: {e}")
    return {"status": result}

@resumeRouter.post("/resume/{id}/add/education")
def add_education(id: str, payload: EducationRequest):
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
    try:
        result = _check_result(doc.add_education(edu))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add education: {e}")
    return {"status": result}

@resumeRouter.post("/resume/{id}/add/project")
def add_project(id: str, payload: ProjectRequest):
    doc = _load_resume(id)
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


@resumeRouter.delete("/resume/{id}")
def delete_resume(id: str):
    doc = _load_resume(id)
    try:
        doc.yaml_file.unlink()
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete resume: {e}")
    return {"status": f"Successfully deleted resume '{id}'"}

@resumeRouter.post("/resume/{id}/add/skill")
def add_skill(id: str, payload: SkillsRequest):
    doc = _load_resume(id)
    skill = Skills(label=payload.label, details=payload.details)
    try:
        result = _check_result(doc.add_skills(skill))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add skill: {e}")
    return {"status": result}

"""POST /resume/{id}/remove"""
@resumeRouter.post("/resume/{id}/remove")
def remove_item(id: str, payload: RemoveItemRequest):
    doc = _load_resume(id)
    section = payload.section.lower()
    remove_map = {
        "experience": lambda: doc.remove_experience(payload.item_name),
        "education": lambda: doc.remove_education(payload.item_name),
        "projects": lambda: doc.remove_project(payload.item_name),
        "skills": lambda: doc.remove_skill(payload.item_name),
    }

    if section not in remove_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown section '{section}'. Valid: experience, education, projects, skills",
        )

    result = _check_result(remove_map[section]())
    return {"status": result}



