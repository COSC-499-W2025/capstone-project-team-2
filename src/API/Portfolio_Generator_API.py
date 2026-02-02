

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


class ProjectRequest(BaseModel):
    edits: list[editItem]



class ProjectRequest(BaseModel):
    name:Optional[str] = None
    start_date:Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[list[str]] = None


