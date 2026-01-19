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

@dataclass
class Connections:
    """
    Represents a social network connection

    Attributes:
        network : Name of the platform (e.g., 'LinkedIn', 'GitHub', 'Twitter')
        Username : or profile identifier on the platform
    """
    network: Optional[str] = None
    username: Optional[str] = None
    to_dict = _to_dict

@dataclass
class Project:
    """
    Represents a project entry

    Attributes:
        name: Name of the project
        start_date: Start date in 'YYYY-MM' format
        end_date: End date in 'YYYY-MM' format, or 'present'
        location: City, State or City, Country
        summary: Brief description of the project
        highlights: List of accomplishments or responsibilities
    """
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict

# ========== DOCUMENT TYPE =========
DocumentType = Literal['resume', 'portfolio']

# ========= UNIFIED CLASS =========
class RenderCVDocument:
    """
    Unified builder class for creating and managing RenderCV YAML files.
    Supports both resume and portfolio document types with a single interface.
    """
    THEMES = {
        'classic': 'Classic CV theme',
        'engineeringclassic': 'Engineering-focused CV theme',
        'engineeringresumes': 'Engineering resume theme (recommended for resumes)',
        'moderncv': 'Modern CV theme',
        'sb2nov': 'Clean resume theme (recommended for resumes)',
    }
    def __init__(self, doc_type: DocumentType = 'resume', auto_save: bool = True, output_dir: str = 'rendercv_output')->None:
        """
        Initialize the CV/Resume/Portfolio builder with configuration options.

        Args:
            doc_type: Type of document to create ('resume' or 'portfolio'). Defaults to 'resume'.
            theme: Theme to use for the document. Defaults to 'sb2nov'.
            auto_save: If True, automatically save after each modification. Defaults to True.
            output_dir: Directory for rendered output files. Defaults to 'rendercv_output'.
        Returns:
            None: Constructor does not return a value.

        """
        self.doc_type = doc_type
        self.cv_files_dir = Path(__file__).parent.parent.parent / "User_config_files" / "Generate_render_CV_files"
        self.project_insight_folder = Path(__file__).parent.parent.parent / "User_config_files" / "project_insights"

        #Cached section data
        self.summary: Optional[List[str]] = None
        self.current_experience: Optional[List[dict]] = None
        self.current_projects: Optional[List[dict]] = None
        self.current_education: Optional[List[dict]] = None
        self.current_connections: Optional[List[dict]] = None
        self.current_skills: Optional[List[dict]] = None
        self.resume_sections: Optional[List[str]] = None
        self.name: Optional[str] = None
        self.data: Optional[dict] = None
        self.chosen_theme: str = "sb2nov"
        self.yaml_file: Optional[Path] = None
        self.auto_save: bool = auto_save
        self.output_dir: Path = Path(output_dir)

        #YAML parser instance
        self.yaml = ruamel.yaml.YAML()
        self.yaml.preserve_quotes = True

    @property
    def _file_suffix(self)->str:
        """
            Determines the file suffix based on the document type.
            used for generating consistent filenames

            Returns:
                str: Either "Resume_CV" for resume documents or "Portfolio_CV" for portfolio documents
            """
        return "Resume_CV" if self.doc_type == 'resume' else "Portfolio_CV"


    def _get_template(self)-> dict:
            """
            Generate a starter template dictionary based on the document type.
            on the document type.
            Creates the base YAML structure with placeholder content

            Args:
                name: The person's name to used in the template, underscore will be replaced with spaces

            Returns:
                  dict: Complete YAML template dictionary

            """
            base_template = {
                'cv': {
                    'name': self.name.replace('_', ' '),
                    'location': 'City, State',
                    'email': 'your.email@example.com',
                    'phone': '+1 234 567 8901',
                    'website': 'https://yourwebsite.com',
                    'social_networks': [
                        {'network': 'LinkedIn', 'username': ''},
                        {'network': 'GitHub', 'username': ''}
                    ],
                    'sections': {}
                },
                'design': {'theme': self.chosen_theme},
                'locale': {'language': 'english'}
            }
            if self.doc_type == 'resume':
                base_template['cv']['sections'] = {
                    'summary': [
                        'A brief summary about yourself and your professional background.'
                    ],
                    'education': [{
                        'institution': 'University Name',
                        'area': 'Field of Study',
                        'degree': 'BS',
                        'start_date': '2020-09',
                        'end_date': '2024-05',
                        'location': 'City, State',
                        'highlights': ['GPA: X.XX/4.00']
                    }],
                    'experience': [{
                        'company': 'Company Name',
                        'position': 'Position Title',
                        'start_date': '2023-06',
                        'end_date': '2023-07',
                        'location': 'City, State',
                        'highlights': ['Accomplishment 1', 'Accomplishment 2']
                    }],
                    'projects': [{
                        'name': 'Project Name',
                        'start_date': '2023-01',
                        'end_date': '2024-05',
                        'summary': 'Brief description of the project',
                        'highlights': ['Key feature 1', 'Key feature 2']
                    }],
                    'skills': [
                        {'label': 'Languages', 'details': 'Python, JavaScript, etc.'},
                        {'label': 'Frameworks', 'details': 'React, Django, etc.'},
                        {'label': 'Tools', 'details': 'Git, Docker, etc.'}
                    ]
                }
            else:
                base_template['cv']['sections'] = {
                    'projects': [{
                        'name': 'Project Name',
                        'start_date': '2023-01',
                        'end_date': '2024-05',
                        'summary': 'Brief description of the project',
                        'highlights': ['Key feature 1', 'Key feature 2']
                    }]
                }
            return base_template

    #====== FILE Operations =======
    def generate(self,overwrite:bool=False, name: str = "Jane Doe"):
        """
        Generate a starter YAML file with template content.
        Creates the necessary directories and writes the initial YAML structure.

        Args:
            overwrite: If True, deletes existing file and creates a new one; if False, skips generation when file exists
            name: The person's name used for the filename and within the template content

        Returns:
            str: "Success" if file was created, "Skipping generation" if file already exists and overwrite is False
        """
        self.name.replace(" ", "_")
        self.cv_files_dir.mkdir(parents=True, exist_ok=True)
        self.yaml_file = self.cv_files_dir / f"{self.name}_{self._file_suffix}.yaml"

        if self.yaml_file.exists():
            if overwrite:
                self.yaml_file.unlink()
            else:
                return "Skipping generation"

        template = self._get_template()
        with open(self.yaml_file, 'w') as f:
            self.yaml.dump(template, f)

        return "Success"



    def load(self,name: Optional[str] = None)-> dict:
        """
        Loads an existing YAML file into memory for editing
        Parses the file and caches section data for easy access
        
        Args:
            name: Optional name to load a specific file; if None, uses the previously set name from generate()

        Returns:
            dict: The complete parsed YAML data structure with 'cv', 'design', and 'locale' keys

        Raises:
            FileNotFoundError: If the YAML file does not exist at the expected path


        """

        if name:
            self.name= name.replace(" ", "_")
            self.yaml_file = self.cv_files_dir / f"{self.name}_{self._file_suffix}.yaml"

        if not self.yaml_file or not self.yaml_file.exists():
            raise FileNotFoundError(f"YAML file {self.yaml_file} not found")

        with open(self.yaml_file, 'r') as f:
            self.data = self.yaml.load(f)

        if self.data.get('cv') is None:
            raise ValueError("Invalid YAML structure: missing required 'cv' key")

        sections=self.data['cv']['sections']
        section_keys=list(sections.keys())
        self.resume_sections=section_keys[1:] if section_keys[0]=='name' else []
        self.current_education=sections.get('projects', [])
        self.current_projects=self.data['cv'].get('social_networks', [])
        self.data['cv']['name'] = str(self.name).replace("_", " ")

        if self.doc_type == 'resume':
            self.current_education=sections.get('education', [])
            self.current_skills=sections.get('skills', [])
            self.current_experience=sections.get('experience',[])
            self.summary = sections.get('summary', [])

        return self.data










