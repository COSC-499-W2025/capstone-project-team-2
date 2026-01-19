import subprocess
import shutil
from functools import wraps
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Literal
import ruamel.yaml
import orjson
from src.reporting.Generate_AI_Resume import GenerateProjectResume


##=================HELPER FUNCTIONS===================

def _to_dict(obj)->dict:
    """
    Convert a dataclass instance to dictionary,
    excluding fields with None Values
        Args:
            obj: The dataclass instance to convert
        Returns:
            dict: A dictionary containing only non-None fields from the dataclass
    """
    return {k:v for k,v in obj.__dict__.items() if v is not None}

def requires_data(method):
    """
     Decorator that ensures CV data is loaded before method execution.
    Validates that self.data exists and contains the required 'cv' key.
        Args:
            method: The method to wrap with data validation check
        Returns:
             function: Wrapped method that raises ValueError if data is not loaded

    """

    @wraps(method)
    def wrapper(self,*args,**kwargs):
        if self.data is None:
            raise ValueError("No data loaded")
        if self.data.get('cv') is None:
            raise ValueError("Invalid data structure: missing required 'cv' key")
        return method(self,*args,**kwargs)
    return wrapper

def requires_resume(method):
    """
    Decorator that ensures the document type is 'resume' before
    method execution. Used to restrict methods to resume documents only

    Args:
        method: The method to wrap with document type validation

    Returns:
        function: Wrapped method that raises ValueError if doc_type is not 'resume'

    """
    @wraps(method)
    def wrapper(self,*args,**kwargs):
        if self.doc_type != 'resume':
            raise ValueError("Method requires document type 'resume'")
        return method(self,*args,**kwargs)
    return wrapper


#==================DATACLASSES====================

@dataclass
class Expereince:
    """Represents a Work experience entry

    Attributes:
        company: Name of the company or organization
        position: Job title or role held
        start_date: Start date in 'YYYY-MM' format
        end_date: End date in 'YYYY-MM' format, or 'present'
        location: City, State or City, Country
        highlights: List of accomplishments or responsibilities

    """
    company:str
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict

@dataclass
class Skills:
    """
    Represents a skill category entry
    Attributes:
        label: Category name for the skill group (e.g., 'Languages', 'Frameworks')
        details: Comma-separated string of skills in this category (e.g., 'Python, JavaScript, Go')
    """
    label:str
    details:str
    to_dict = _to_dict

@dataclass
class Education:
    """
    Represents an education entry

    Attributes:
    institution: Name of the university or school
        area: Field of study or major ('e.g., Computer science')
        start_date: Start date in 'YYYY-MM' format
        end_date: End date in 'YYYY-MM' format
        location: City, State or City, Country
        degree: Degree type (e.g., "BS", "MS", "PhD")
        gpa: Grade point average
        highlights: List of achievements or relevant coursework

    """
    institution: str
    area: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    gpa: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict


