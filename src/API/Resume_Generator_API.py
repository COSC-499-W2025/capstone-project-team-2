"""
FASTAPI endpoints for resume generation and editing via RenderCV

"""
from typing import Optional,List,Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from langchain_community.agent_toolkits import OpenAPIToolkit
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
    overwrite: False

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
    position: Optional[str] =None
    location: Optional[str] =None
    website: Optional[str] =None
    name: Optional[str] =None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[list[str]] = None


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
