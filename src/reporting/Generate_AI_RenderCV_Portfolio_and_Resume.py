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
        self.sections: Optional[List[str]] = None
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
        self.sections=section_keys[1:] if section_keys[0]=='name' else []
        self.current_projects=sections.get('projects', [])
        self.current_connections=self.data['cv'].get('social_networks', [])
        self.data['cv']['name'] = str(self.name).replace("_", " ")

        if self.doc_type == 'resume':
            self.current_education=sections.get('education', [])
            self.current_skills=sections.get('skills', [])
            self.current_experience=sections.get('experience',[])
            self.summary = sections.get('summary', [])

        return self.data


    def save(self,filename:Optional[str] = None):
        """

        :param filename:
        :return:
        """
        if self.data is None:
            raise ValueError("No data loaded")

        output_file=Path(filename) if filename else self.yaml_file
        with open(self.yaml_file, 'w') as f:
            self.yaml.dump(self.data, f)

        return output_file

    def _auto_save_if_enabled(self)-> None:
        """
        Automatically saves the data if auto_save is enabled.
        called internally after each modification method.

        Returns:
            None: This method does not return anything.

        """
        if self.auto_save and self.data is not None:
            self.save()


    def render(self) -> tuple[str,Optional[Path]]:
        """
         Render the YAML file to PDF using the RenderCV command-line tool.
        Cleans up any existing output directory before rendering.

        Returns:
            tuple[str, Optional[Path]]: A tuple containing:
                - Status message ("successfully rendered" or error description)
                - Path to the generated PDF file, or None if rendering failed

        Raises:
            FileNotFoundError: If the YAML file does not exist
        """
        if not self.yaml_file or not self.yaml_file.exists():
            raise FileNotFoundError(f"YAML file {self.yaml_file} does not exist")

        yaml_file_absolute=self.yaml_file.resolve()
        default_output=yaml_file_absolute.parent / "rendercv_output"
        source_pdf = default_output / f"{self.name}_CV.pdf"

        if default_output.exists():
            shutil.rmtree(default_output)

        result= subprocess.run(['rendercv', 'render', str(self.yaml_file)],capture_output=True,text=True, encoding='utf-8',errors='replace')

        if source_pdf.exists():
            return "successfully rendered", source_pdf
        else:
            if result.returncode !=0:
                return f"render failed (code {result.returncode}): {result.stderr}", None
            return f"render failed - PDF not found at {source_pdf}", None

# ============== CONTACT & THEME ==============
    @requires_data
    def update_contact(self,email: Optional[str] = None,phone: Optional[str] = None,location: Optional[str] = None,website: Optional[str] = None,name: Optional[str] = None):
        """

        :param email:
        :param phone:
        :param location:
        :param website:
        :param name:
        :return:
        """
        cv=self.data['cv']
        fields = {'email': email, 'phone': phone, 'location': location, 'website': website, 'name': name}
        for field_name,value in fields.items():
            if value and str(value).strip():
                cv[field_name] = value
        self._auto_save_if_enabled()
        return self
    @requires_data
    def update_theme(self,selected_theme:str):
        """

        :param selected_theme:
        :return:
        """
        if selected_theme not in self.THEMES:
            available = ', '.join(self.THEMES.keys())
            raise ValueError(f"Invalid theme '{selected_theme}'. Available: {available}")

        self.data['design']['theme'] = selected_theme
        self._auto_save_if_enabled()
        return f"Successfully updated theme '{selected_theme}'"

    # ============== PROJECTS (shared) ==============
    @requires_data
    def add_project(self,project_info: Project):
        """

        :param project_info:
        :return:
        """
        if not project_info.name or not project_info.name.strip():
            return "Project name cannot be empty"

        if 'project' not in self.sections:
            self.sections['project'] = []
            self.current_projects=self.sections['projects']

        existing = [p['name'] for p in self.current_projects]
        if project_info.name  in existing:
            return f"Project '{project_info.name}' already exists"
        self.current_projects.append(project_info.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added project '{project_info.name}' "

    @requires_data
    def modify_project(self, project_name: str, field: str, new_value):
        """

        :param project_name:
        :param field:
        :param new_value:
        :return:
        """
        valid_fields = ["name", "start_date", "end_date", "location", "summary", "highlights"]
        if field not in valid_fields:
            return f"Invalid field '{field}'. Valid: {', '.join(valid_fields)}"

        project = next((p for p in self.current_projects if p.get("name") == project_name), None)
        if project is None:
            return f"Project '{project_name}' not found"

        project[field] = new_value
        self._auto_save_if_enabled()
        return f"Successfully modified {field}"

    @requires_data
    def remove_project(self,project_name: str):
        """

        :param project_name:
        :return:
        """
        if 'projects' not in self.sections or not self.current_projects:
            return "No projects to delete"

        project = next((p for p in self.current_projects if p.get('name') == project_name), None)
        if project is None:
            return f"Project '{project_name}' not found"

        self.current_projects.remove(project)
        self._auto_save_if_enabled()
        return f"Successfully deleted: {project_name}"

    @requires_data
    def add_project_from_ai(self, project_folder: str) -> str:
        """
        Generate project information using AI analysis and add it to the projects section.
        Reads project insight data and uses GenerateProjectResume to create content.

        Args:
            project_folder: Path to the project insight JSON file containing 'project_root' key

        Returns:
            str: Result from add_project() - success message with project name or error message
        """
        with open(project_folder, 'rb') as f:
            data = orjson.loads(f.read())

        project_loc = data.get('project_root')
        ai_resume = GenerateProjectResume(project_loc).generate()

        summary = ai_resume.one_sentence_summary
        if ai_resume.tech_stack:
            summary = f"{summary} Tech stack: {ai_resume.tech_stack}"

        project = Project(
            name=ai_resume.project_title,
            summary=summary,
            highlights=ai_resume.key_responsibilities,
        )
        print(f"✓ AI analysis complete for: {ai_resume.project_title}")
        return self.add_project(project)

    @requires_data
    def add_connection(self,connection_info: ConnectionInfo):
        """

        :param connection_info:
        :return:
        """
        if not connection_info.network or not connection_info.network.strip():
            return "Network name cannot be empty"

        if "social_networks" not in self.data['cv']:
            self.data['cv']['social_networks'] = []
            self.current_connections = self.data['cv']['social_networks']

        existing = [c['network'] for c in self.current_connections]
        if connection_info.network in existing:
            return f"Connection '{connection_info.network}' already exists"

        self.current_connections.append(connection_info.to_dict())
        self._auto_save_if_enabled()
        return f"Successfully added: {connection_info.network}"

    @requires_data
    def modify_connection(self, network_name: str, new_username: str) -> str:
        """
        Modify the username for an existing social network connection.

        Args:
            network_name: The exact name of the network to modify (e.g., "GitHub", "LinkedIn")
            new_username: The new username or profile identifier to set

        Returns:
            str: Success message confirming the update, or error message if network not found
        """
        connection = next((c for c in self.current_connections if c.get("network") == network_name), None)
        if connection is None:
            return f"Connection '{network_name}' not found"

        connection["username"] = new_username
        self._auto_save_if_enabled()
        return f"Successfully updated: {network_name}"

    @requires_data
    def remove_connection(self, network_name: str) -> str:
        """
        Remove a social network connection from the CV header.

        Args:
            network_name: The exact name of the network to remove (e.g., "GitHub", "LinkedIn")

        Returns:
            str: Success message confirming deletion, or error message if no connections exist or network not found
        """
        if not self.current_connections:
            return "No connections to delete"

        connection = next((c for c in self.current_connections if c.get("network") == network_name), None)
        if connection is None:
            return f"Connection '{network_name}' not found"

        self.current_connections.remove(connection)
        self._auto_save_if_enabled()
        return f"Successfully deleted: {network_name}"

    # ============== RESUME-ONLY METHODS ==============
    @requires_data
    @requires_resume
    def update_summary(self, new_content: str) -> str:
        """
        Update the professional summary section at the top of the resume.
        Available only for resume document type.

        Args:
            new_content: The complete summary text to replace existing content

        Returns:
            str: Confirmation message that the summary was updated
        """
        if 'summary' not in self.sections:
            self.sections['summary'] = []
        self.sections['summary'] = [new_content]
        self._auto_save_if_enabled()
        return "Summary updated successfully"

    @requires_data
    @requires_resume
    def add_experience(self, experience: Experience) -> str:
        """
        Add a new work experience entry to the experience section.
        Available only for resume document type. Creates the section if it doesn't exist.

        Args:
            experience: Experience dataclass instance with company name (required) and optional position, dates, location, highlights

        Returns:
            str: Success message confirming the experience was added, or error if company name is empty
        """
        if not experience.company or not experience.company.strip():
            return "Company name cannot be empty"

        if 'experience' not in self.sections:
            self.sections['experience'] = []
            self.current_experience = self.sections['experience']

        self.current_experience.append(experience.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added experience"

    @requires_data
    @requires_resume
    def modify_experience(self, company_name: str, field: str, new_value) -> str:
        """
        Modify a specific field of an existing work experience entry.
        Available only for resume document type.

        Args:
            company_name: The exact company name of the experience entry to modify
            field: The field to update (valid: "company", "position", "start_date", "end_date", "location", "summary", "highlights")
            new_value: The new value to set for the field (type depends on field)

        Returns:
            str: Success message confirming the field was modified, or error if field is invalid or experience not found
        """
        valid_fields = ["company", "position", "start_date", "end_date", "location", "summary", "highlights"]
        if field not in valid_fields:
            return f"Invalid field '{field}'. Valid: {', '.join(valid_fields)}"

        exp = next((e for e in self.current_experience if e.get("company") == company_name), None)
        if exp is None:
            return f"Experience '{company_name}' not found"

        exp[field] = new_value
        self._auto_save_if_enabled()
        return f"Successfully modified {field}"

    @requires_data
    @requires_resume
    def remove_experience(self, company_name: str) -> str:
        """
        Remove a work experience entry by company name.
        Available only for resume document type.

        Args:
            company_name: The exact company name of the experience entry to remove

        Returns:
            str: Success message confirming deletion, or error if no experiences exist or company not found
        """
        if not self.current_experience:
            return "No experience to delete"

        exp = next((e for e in self.current_experience if e.get("company") == company_name), None)
        if exp is None:
            return f"Experience '{company_name}' not found"

        self.current_experience.remove(exp)
        self._auto_save_if_enabled()
        return "Successfully removed experience"

    @requires_data
    @requires_resume
    def add_education(self, education: Education) -> str:
        """
        Add a new education entry to the education section.
        Available only for resume document type. Creates the section if it doesn't exist.
        Prevents duplicate institution names.

        Args:
            education: Education dataclass instance with institution and area (required), plus optional degree, dates, location, gpa, highlights

        Returns:
            str: Success message confirming the education was added, or error if institution is empty or duplicate
        """
        if not education.institution or not education.institution.strip():
            return "Institution name cannot be empty"

        if 'education' not in self.sections:
            self.sections['education'] = []
            self.current_education = self.sections['education']

        existing = [e['institution'] for e in self.current_education]
        if education.institution in existing:
            return "Duplicate education entry"

        self.current_education.append(education.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added education"

    @requires_data
    @requires_resume
    def modify_education(self, institution_name: str, field: str, new_value) -> str:
        """
        Modify a specific field of an existing education entry.
        Available only for resume document type.

        Args:
            institution_name: The exact institution name of the education entry to modify
            field: The field to update (valid: "institution", "area", "degree", "start_date", "end_date", "location", "highlights")
            new_value: The new value to set for the field (type depends on field)

        Returns:
            str: Success message confirming the field was modified, or error if field is invalid or institution not found
        """
        valid_fields = ["institution", "area", "degree", "start_date", "end_date", "location", "highlights"]
        if field not in valid_fields:
            return f"Invalid field '{field}'. Valid: {', '.join(valid_fields)}"

        edu = next((e for e in self.current_education if e.get("institution") == institution_name), None)
        if edu is None:
            return f"Education '{institution_name}' not found"

        edu[field] = new_value
        self._auto_save_if_enabled()
        return f"Successfully modified {field}"

    @requires_data
    @requires_resume
    def remove_education(self, institution_name: str) -> str:
        """
        Remove an education entry by institution name.
        Available only for resume document type.

        Args:
            institution_name: The exact institution name of the education entry to remove

        Returns:
            str: Success message confirming deletion, or error if no education entries exist or institution not found
        """
        if not self.current_education:
            return "No education to delete"

        edu = next((e for e in self.current_education if e.get("institution") == institution_name), None)
        if edu is None:
            return f"Education '{institution_name}' not found"

        self.current_education.remove(edu)
        self._auto_save_if_enabled()
        return "Successfully deleted education"

    @requires_data
    @requires_resume
    def add_skills(self, skill: Skills) -> str:
        """
        Add a new skill category to the skills section.
        Available only for resume document type. Creates the section if it doesn't exist.
        Prevents duplicate skill labels.

        Args:
            skill: Skills dataclass instance with label (category name) and details (comma-separated skills)

        Returns:
            str: Success message confirming the skill was added, or error if label is empty or duplicate
        """
        if not skill.label or not skill.label.strip():
            return "Skill label cannot be empty"

        if 'skills' not in self.sections:
            self.sections['skills'] = []
            self.current_skills = self.sections['skills']

        existing = [s['label'] for s in self.current_skills]
        if skill.label in existing:
            return "Duplicate skill label"

        self.current_skills.append(skill.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added skills"



