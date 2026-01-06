"""
RenderCV Generator - A Python wrapper for creating and managing CV/resume YAML files.

This module provides dataclasses and a builder class for programmatically generating
CVs using the RenderCV tool. It handles YAML file creation, modification, and rendering.
"""

import subprocess
from functools import wraps
from pathlib import Path
import ruamel.yaml
from dataclasses import dataclass, asdict
from typing import Optional, List
import orjson

from src.reporting.Generate_AI_Resume import GenerateProjectResume


def _to_dict(obj) -> dict:
    """Convert dataclass to dictionary, excluding None values."""
    return {k: v for k, v in asdict(obj).items() if v is not None}


def requires_data(method):
    """Decorator that ensures CV data is loaded before method execution."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.data is None:
            raise ValueError("No data loaded")
        return method(self, *args, **kwargs)
    return wrapper


@dataclass
class Experience:
    """Represents an experience entry in a CV."""
    company: str
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict


@dataclass
class Skills:
    """Represents a skills section in a CV/Resume YAML file."""
    label: str
    details: str
    to_dict = _to_dict


@dataclass
class Education:
    """Represents an education entry in a CV."""
    institution: str
    areaOfStudy: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    gpa: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict


@dataclass
class Connections:
    """Represents a social network or professional connection link."""
    network: Optional[str] = None
    username: Optional[str] = None
    to_dict = _to_dict


@dataclass
class Project:
    """Represents a project entry in a CV."""
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict


class create_Render_CV:
    """Builder class for creating and managing RenderCV YAML files.

    Provides methods to generate, load, modify, and render CV files using
    the RenderCV command-line tool.
    """

    def __init__(self, auto_save: bool = True, output_dir: str = 'rendercv_output'):
        """Initialize the CV/Resume builder.

        Args:
            auto_save: If True, automatically save after each modification. Defaults to True.
            output_dir: Directory for rendered output files. Defaults to 'rendercv_output'.
        """
        # CV files directory
        self.cv_files_dir = Path(__file__).parent.parent.parent / "User_config_files" / "Generate_render_CV_files"
        self.project_insight_folder=Path(__file__).parent.parent.parent / "User_config_files" / "project_insights"
        self.summary = None
        self.current_experience = None
        self.resume_section = None  # List of section names (populated by load_starter_file)
        self.current_projects = None  # Cached list of project dictionaries
        self.current_education = None
        self.current_connections = None
        self.current_skills = None
        self.name = None  # Sanitized name for filename
        self.yaml = ruamel.yaml.YAML()  # YAML parser instance
        self.yaml.preserve_quotes = True  # Maintain original quote style when saving
        self.data = None  # Loaded YAML data structure
        self.chosen_theme = "sb2nov"  # Selected theme
        self.themes = {
            'classic': 'Classic CV theme',
            'engineeringclassic': 'Engineering-focused CV theme',
            'engineeringresumes': 'Engineering resume theme (recommended for resumes)',
            'moderncv': 'Modern CV theme',
            'sb2nov': 'Clean resume theme (recommended for resumes)', }
        self.yaml_file = None  # Path to the YAML file
        self.auto_save = auto_save  # Flag for automatic saving
        self.output_dir = Path(output_dir)  # Directory for rendered output

    def generate_starter_file(self, overwrite: bool = False, name: str = "Jane Doe"):
        """Generate a starter resume YAML file.

        Creates a minimal resume template with essential sections:
        education, experience, projects, and skills.

        Args:
            overwrite: If True, delete and regenerate existing file. If False, skip generation.

        Returns:
            None
        """
        self.name = name.replace(" ", "_")

        # Create CV files directory if it doesn't exist
        self.cv_files_dir.mkdir(parents=True, exist_ok=True)

        self.yaml_file = self.cv_files_dir / f"{self.name}_CV.yaml"
        if self.yaml_file.exists():
            if overwrite:
                # Remove existing file before regenerating
                # print(f"Deleting existing file: {self.yaml_file}")
                self.yaml_file.unlink()
            else:
                # Skip generation if file exists and overwrite is False
                # print(f'File already exists: {self.yaml_file} (skipping generation)')
                return "Skipping generation"

        # Create minimal resume template directly
        resume_template = {
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
                'sections': {
                    'summary': [
                        'A brief summary about yourself and your professional background. Highlight your key strengths, experience, and career objectives.'
                    ],
                    'education': [
                        {
                            'institution': 'University Name',
                            'area': 'Field of Study',
                            'degree': 'BS',
                            'start_date': '2020-09',
                            'end_date': '2024-05',
                            'location': 'City, State',
                            'highlights': ['GPA: X.XX/4.00']
                        }
                    ],
                    'experience': [
                        {
                            'company': 'Company Name',
                            'position': 'Position Title',
                            'start_date': '2023-06',
                            'end_date': '2023-07',
                            'location': 'City, State',
                            'highlights': [
                                'Accomplishment or responsibility 1',
                                'Accomplishment or responsibility 2'
                            ]
                        }
                    ],
                    'projects': [
                        {
                            'name': 'Project Name',
                            'start_date': '2023-01',
                            'end_date': '2024-05',
                            'summary': 'Brief description of the project',
                            'highlights': [
                                'Key feature or accomplishment 1',
                                'Key feature or accomplishment 2'
                            ]
                        }
                    ],
                    'skills': [
                        {'label': 'Languages', 'details': 'Python, JavaScript, etc.'},
                        {'label': 'Frameworks', 'details': 'React, Django, etc.'},
                        {'label': 'Tools', 'details': 'Git, Docker, etc.'}
                    ]
                }
            },
            'design': {
                'theme': self.chosen_theme
            },
            'locale': {
                'language': 'english'
            }
        }

        # Write the template to file
        with open(self.yaml_file, 'w') as f:
            self.yaml.dump(resume_template, f)

        print(f"Starter resume file has been generated with '{self.chosen_theme}' theme")
        return "Success"

    def load_starter_file(self, name: str = None):
        """Load the YAML file into memory for editing.

        Parses the YAML file and initializes instance attributes for
        sections and projects. Must be called before any modification methods.

        Args:
            name: Optional name to load an existing file from RenderedCV folder
                  without calling generate_starter_file() first.

        Returns:
            dict: The loaded YAML data structure.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
        """
        # If name is provided, set yaml_file path to CV files directory
        if name:
            self.name = name.replace(" ", "_")
            self.yaml_file = self.cv_files_dir / f"{self.name}_CV.yaml"

        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist "
                                    f"Run generate_starter_file() first.")

        # Parse YAML file into data structure
        with open(self.yaml_file, 'r') as f:
            self.data = self.yaml.load(f)

        # Extract section names (skip first section which is typically 'summary')
        self.resume_section = list(self.data['cv']['sections'].keys())[1:]
        # Cache projects list for quick access
        self.current_projects = self.data['cv']['sections']['projects']
        # Restore spaces in name for display
        self.data['cv']['name'] = str(self.name).replace("_", " ")
        self.current_education = self.data['cv']['sections']['education']
        self.current_connections = self.data['cv']['social_networks']
        self.current_skills = self.data['cv']['sections']['skills']
        self.current_experience = self.data['cv']['sections']['experience']
        self.summary = self.data['cv']['sections']['summary']

        return self.data

    def save(self, filename: str = None):
        """Save the CV data to a YAML file.

        Args:
            filename: Optional custom filename. Uses default if not provided.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If no data has been loaded.
        """
        if self.data is None:
            raise ValueError("No data loaded")

        output_file = Path(filename) if filename else self.yaml_file

        with open(output_file, 'w') as f:
            self.yaml.dump(self.data, f)

        # print(f"✓ Saved to {output_file}")
        return output_file

    def _auto_save_if_enabled(self):
        """Save the CV if auto_save is enabled."""
        if self.auto_save and self.data is not None:
            self.save()

    def render_CV(self, output_dir: str = None, filename: str = None):

        """Render the CV to PDF and other output formats.

        Args:
            output_dir: Directory to save rendered output files. Uses self.output_dir if not specified.
            filename: Custom filename for the PDF (without .pdf extension). Uses name_CV if not specified.

        Returns:
            The subprocess result object.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
            subprocess.CalledProcessError: If rendering fails.
        """
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist ")

        # Use instance output_dir if not specified
        target_dir = Path(output_dir).absolute() if output_dir else self.output_dir.absolute()

        # Render to rendercv_output folder (created next to the YAML file)
        result_for_rendering = subprocess.run(
            ['rendercv', 'render', str(self.yaml_file)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        # rendercv creates output folder next to the yaml file
        # Use absolute path to ensure we find the file regardless of working directory
        yaml_file_absolute = self.yaml_file.resolve()
        default_output = yaml_file_absolute.parent / 'rendercv_output'
        source_filename = f"{self.name}_CV.pdf"
        source_pdf = default_output / source_filename

        # Check if PDF exists (rendercv may return non-zero due to Windows console encoding issues
        # even when the PDF was successfully generated)
        if source_pdf.exists():
            return "successfully rendered", source_pdf
        else:
            return f"render failed - PDF not found at {source_pdf}", None

    @requires_data
    def Update_summary(self, new_content_summary: str):
        if 'summary' not in self.data['cv']['sections']:
            self.data['cv']['sections']['summary'] = []
        self.data['cv']['summary'] = new_content_summary
        self._auto_save_if_enabled()
        return "summary has been updated successfully"

    @requires_data
    def remove_section(self, section_to_remove_num: int):
        """Remove a section from the CV by its index."""
        section_name = self.resume_section[section_to_remove_num]
        if section_name in self.data['cv']['sections']:
            del self.data['cv']['sections'][section_name]
            self._auto_save_if_enabled()

    @requires_data
    def modify_projects_info(self, project_name: str, field: str, new_value):
        valid_fields = ["name", "start_date", "end_date", "location", "summary", 'highlights']
        if field not in valid_fields:
            return f"Invalid field {field}. Valid fields are: {', '.join(valid_fields)}"
        for idx, project in enumerate(self.current_projects):
            if project.get("name") == project_name:
                self.current_projects[idx][field] = new_value
                self._auto_save_if_enabled()
                return f"Successfully modified {field} to {new_value}"
        return f"Project {project_name} not found."

    @requires_data
    def add_skills(self, skillToAdd: Skills):
        current_skills = [s['label'] for s in self.current_skills]
        if 'skills' not in self.data['cv']['sections']:
            self.data['cv']['sections']['skills'] = []
        if skillToAdd.label in current_skills:
            return "Duplicate label/skills"
        self.current_skills.append(skillToAdd.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added skills"

    @requires_data
    def modify_skill(self, skillToModify: str, new_value: str):
        skill_to_update = next((skill for skill in self.current_skills if skill.get('label') == skillToModify), None)
        if skill_to_update:
            skill_to_update["details"] = new_value
            self._auto_save_if_enabled()
            return "Successfully modified skill"
        return "Skill not found."

    @requires_data
    def delete_skill(self, skillName: str):
        if 'skills' not in self.data['cv']['sections'] or not self.current_skills:
            return "No skills found to be deleted."
        skill_to_remove = next((skill for skill in self.current_skills if skill.get('label') == skillName), None)
        if skill_to_remove:
            self.current_skills.remove(skill_to_remove)
            self._auto_save_if_enabled()
            return "Successfully deleted chosen skill"
        return "skill not found"

    @requires_data
    def add_experience(self, experienceToAdd: Experience):
        """Add a work experience entry to the CV."""
        if "experience" not in self.data['cv']['sections']:
            self.data['cv']['sections']['experience'] = []
        self.current_experience.append(experienceToAdd.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added experience"

    @requires_data
    def remove_experience(self, experience_name: str):
        if 'experience' not in self.data['cv']['sections'] or not self.data['cv']['sections']['experience']:
            return "Experience not found."
        experience_to_remove = next(
            (ex for ex in self.current_experience if ex.get("company") == experience_name), None)
        if experience_to_remove:
            self.current_experience.remove(experience_to_remove)
            self._auto_save_if_enabled()
            return "Successfully removed experience from system"
        return f"Experience {experience_name} not found."

    @requires_data
    def modify_experience(self, company_name: str, field: str, new_value):
        """Modify a field of an existing experience entry.

        Args:
            company_name: The company name to identify the experience entry.
            field: The field to modify (company, position, start_date, end_date, location, highlights).
            new_value: The new value for the field.

        Returns:
            Success or error message.
        """
        valid_fields = ["company", "position", "start_date", "end_date", "location", "summary", "highlights"]
        if field not in valid_fields:
            return f"Invalid field '{field}'. Valid fields are: {', '.join(valid_fields)}"
        experience_to_update = next(
            (exp for exp in self.current_experience if exp.get("company") == company_name), None)
        if experience_to_update:
            experience_to_update[field] = new_value
            self._auto_save_if_enabled()
            return f"Successfully modified {field} to {new_value}"
        return f"Experience with company '{company_name}' not found."

    @requires_data
    def add_education(self, education_info: Education):
        """Add an education entry to the CV."""
        if 'education' not in self.data['cv']['sections']:
            self.data['cv']['sections']['education'] = []
        existing_institutions = [e['institution'] for e in self.data['cv']['sections']['education']]
        if education_info.institution in existing_institutions:
            return "Duplicate education entry"
        self.data['cv']['sections']['education'].append(education_info.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added education"

    @requires_data
    def delete_education(self, InstutionName):
        """Delete an education entry from the CV."""
        if 'education' not in self.data['cv']['sections'] or not self.data['cv']['sections']['education']:
            return "No education to be deleted"
        education_to_remove = next(
            (edu for edu in self.current_education if edu.get("institution") == InstutionName), None)
        if education_to_remove:
            self.current_education.remove(education_to_remove)
            self._auto_save_if_enabled()
            return "Successfully deleted education"
        return f"Education {InstutionName} not found."

    @requires_data
    def delete_project(self, project_name):
        """Delete a project from the resume or CV."""
        if 'projects' not in self.data['cv']['sections'] or not self.data['cv']['sections']['projects']:
            return "No projects to delete"
        for pos, project in enumerate(self.current_projects):
            if project.get('name') == project_name:
                del self.current_projects[pos]
                self._auto_save_if_enabled()
                return f"Successfully deleted: {project_name}"
        return f"Project not found: {project_name}"

    @requires_data
    def add_project(self, projectInfo: Project):
        """Add a project entry to the CV."""
        if 'projects' not in self.data['cv']['sections']:
            self.data['cv']['sections']['projects'] = []
        existing_projects = [p['name'] for p in self.data['cv']['sections']['projects']]
        if projectInfo.name in existing_projects:
            return f"Project '{projectInfo.name}' already exists"
        self.data['cv']['sections']['projects'].append(projectInfo.to_dict())
        self._auto_save_if_enabled()
        return f"Successfully added: {projectInfo.name}"

    @requires_data
    def add_project_from_ai(self, project_folder: str):
        """Generate project info using AI and add it to the CV."""
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
    def modify_connection(self, network_name: str, new_username: str):
        """Modify the username for an existing social network connection."""
        for idx, connection in enumerate(self.current_connections):
            if connection.get("network") == network_name:
                self.current_connections[idx]["username"] = new_username
                self._auto_save_if_enabled()
                return f"Successfully updated connection {network_name}"
        return f"Network {network_name} Cannot be found."

    @requires_data
    def delete_connection(self, connectionName: str):
        """Delete a social network connection from the CV."""
        if "social_networks" not in self.data['cv'] or not self.data['cv']['social_networks']:
            return "No connections to delete"
        for pos, connection in enumerate(self.current_connections):
            if connection.get("network") == connectionName:
                del self.current_connections[pos]
                self._auto_save_if_enabled()
                return f"Successfully deleted connection: {connectionName}"
        return f"Connection '{connectionName}' not found"

    @requires_data
    def add_connection(self, connectionInfo: Connections):
        """Add a social network connection to the CV."""
        if "social_networks" not in self.data['cv']:
            self.data['cv']['social_networks'] = []
        existing_social_networks = [c['network'] for c in self.current_connections]
        if connectionInfo.network in existing_social_networks:
            return "Connection already exists in Resume"
        self.data['cv']['social_networks'].append(connectionInfo.to_dict())
        self._auto_save_if_enabled()
        return f"Successfully added: {connectionInfo.network}"

    @requires_data
    def update_theme(self, selected_theme: str):
        self.data['design']['theme'] = selected_theme
        self._auto_save_if_enabled()
        return f"Successfully updated: {selected_theme}"

    @requires_data
    def update_contact(self, email=None, phone=None, location=None, website=None, name=None):
        """Update contact information in the CV."""
        cv = self.data['cv']
        if email:
            cv['email'] = email
        if phone:
            cv['phone'] = phone
        if location:
            cv['location'] = location
        if website:
            cv['website'] = website
        if name:
            cv['name'] = name
        self._auto_save_if_enabled()
        return self