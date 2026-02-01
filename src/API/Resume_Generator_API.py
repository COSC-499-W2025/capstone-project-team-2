"""
FASTAPI endpoints for resume generation and editing via RenderCV

"""
from typing import Optional,List,Any
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


