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
    """Convert a dataclass instance to a dictionary, excluding fields with None values.

    This utility function is used to serialize dataclass objects for YAML output,
    ensuring that optional fields with no value are omitted from the final output.

    Args:
        obj: A dataclass instance to be converted to a dictionary.

    Returns:
        dict: A dictionary containing only the non-None fields from the dataclass.
    """
    return {k: v for k, v in asdict(obj).items() if v is not None}


def requires_data(method):
    """Decorator that ensures CV data is loaded before method execution.

    This decorator validates that the create_Render_CV instance has loaded
    YAML data before allowing the decorated method to execute. It prevents
    operations on uninitialized CV data.

    Args:
        method: The method to be wrapped with the data validation check.

    Returns:
        callable: A wrapper function that validates data exists before calling the method.

    Raises:
        ValueError: If self.data is None when the decorated method is called.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.data is None:
            raise ValueError("No data loaded")
        return method(self, *args, **kwargs)
    return wrapper


@dataclass
class Experience:
    """Represents a work experience entry in a CV.

    Stores information about a job or work position including the company,
    role, duration, and key accomplishments.

    Attributes:
        company: The name of the company or organization.
        position: The job title or role held at the company.
        start_date: The start date of employment in 'YYYY-MM' format.
        end_date: The end date of employment in 'YYYY-MM' format, or 'present'.
        location: The geographic location of the job (e.g., 'City, State').
        highlights: A list of key accomplishments or responsibilities.
        to_dict: Method to convert the dataclass to a dictionary.
    """
    company: str
    position: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    highlights: Optional[List[str]] = None
    to_dict = _to_dict


@dataclass
class Skills:
    """Represents a skill category entry in a CV.

    Stores a labeled group of skills, typically displayed as a category
    with associated technologies or competencies.

    Attributes:
        label: The category name for the skill group (e.g., 'Languages', 'Frameworks').
        details: A comma-separated string of skills in this category
            (e.g., 'Python, JavaScript, Go').
        to_dict: Method to convert the dataclass to a dictionary.
    """
    label: str
    details: str
    to_dict = _to_dict


@dataclass
class Education:
    """Represents an education entry in a CV.

    Stores information about academic qualifications including the institution,
    degree, field of study, and any notable achievements.

    Attributes:
        institution: The name of the educational institution (e.g., 'University of Example').
        areaOfStudy: The field or major of study (e.g., 'Computer Science').
        start_date: The start date of attendance in 'YYYY-MM' format.
        end_date: The end date or expected graduation in 'YYYY-MM' format.
        location: The geographic location of the institution (e.g., 'City, State').
        degree: The type of degree (e.g., 'BS', 'MS', 'PhD').
        gpa: The grade point average, if applicable (e.g., '3.8/4.0').
        highlights: A list of academic achievements, honors, or relevant coursework.
        to_dict: Method to convert the dataclass to a dictionary.
    """
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
    """Represents a social network or professional connection link in a CV.

    Stores information about online profiles and professional networks
    that can be displayed on the CV for networking purposes.

    Attributes:
        network: The name of the social network or platform
            (e.g., 'LinkedIn', 'GitHub', 'Twitter').
        username: The username or handle on the specified network.
        to_dict: Method to convert the dataclass to a dictionary.
    """
    network: Optional[str] = None
    username: Optional[str] = None
    to_dict = _to_dict


@dataclass
class Project:
    """Represents a project entry in a CV.

    Stores information about personal, academic, or professional projects
    including their scope, timeline, and key features or accomplishments.

    Attributes:
        name: The title or name of the project.
        start_date: The start date of the project in 'YYYY-MM' format.
        end_date: The end date of the project in 'YYYY-MM' format, or 'present'.
        location: The context or organization where the project was done.
        summary: A brief one-line description of what the project does.
        highlights: A list of key features, technologies used, or accomplishments.
        to_dict: Method to convert the dataclass to a dictionary.
    """
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
            name: The name to use for the CV file and as the default name in the template.
                Defaults to 'Jane Doe'.

        Returns:
            str: 'Success' if file was created, 'Skipping generation' if file exists
                and overwrite is False.
        """
        self.name = name.replace(" ", "_")

        # Create CV files directory if it doesn't exist
        self.cv_files_dir.mkdir(parents=True, exist_ok=True)

        self.yaml_file = self.cv_files_dir / f"{self.name}_Resume_CV.yaml"
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
            self.yaml_file = self.cv_files_dir / f"{self.name}_Resume_CV.yaml"

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
        """Automatically save the CV to disk if auto-save mode is enabled.

        This internal method is called after each modification operation to
        persist changes immediately when auto_save is True. It prevents data
        loss by ensuring modifications are written to the YAML file.

        Args:
            None

        Returns:
            None: This method does not return a value; it saves as a side effect.
        """
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
        source_filename = f"{self.name}_Resume_CV.pdf"
        source_pdf = default_output / source_filename

        # Check if PDF exists (rendercv may return non-zero due to Windows console encoding issues
        # even when the PDF was successfully generated)
        if source_pdf.exists():
            return "successfully rendered", source_pdf
        else:
            return f"render failed - PDF not found at {source_pdf}", None

    @requires_data
    def Update_summary(self, new_content_summary: str):
        """Update the summary section of the CV with new content.

        Replaces the existing summary text with the provided content. Creates
        the summary section if it does not already exist.

        Args:
            new_content_summary: The new summary text to display at the top of the CV.

        Returns:
            str: A success message confirming the summary was updated.
        """
        if 'summary' not in self.data['cv']['sections']:
            self.data['cv']['sections']['summary'] = []
        self.data['cv']['summary'] = new_content_summary
        self._auto_save_if_enabled()
        return "summary has been updated successfully"

    @requires_data
    def remove_section(self, section_to_remove_num: int):
        """Remove a section from the CV by its index position.

        Deletes an entire section (e.g., education, experience, projects) from
        the CV based on its index in the resume_section list.

        Args:
            section_to_remove_num: The zero-based index of the section to remove
                from the resume_section list.

        Returns:
            None: The section is removed as a side effect; no value is returned.
        """
        section_name = self.resume_section[section_to_remove_num]
        if section_name in self.data['cv']['sections']:
            del self.data['cv']['sections'][section_name]
            self._auto_save_if_enabled()

    @requires_data
    def modify_projects_info(self, project_name: str, field: str, new_value):
        """Modify a specific field of an existing project entry.

        Updates a single field of a project identified by its name. Valid fields
        include name, dates, location, summary, and highlights.

        Args:
            project_name: The name of the project to modify, used as identifier.
            field: The field to update. Must be one of: name, start_date, end_date,
                location, summary, or highlights.
            new_value: The new value to set for the specified field. Type depends
                on the field (str for most, List[str] for highlights).

        Returns:
            str: A success message with the field and new value, or an error message
                if the field is invalid or the project is not found.
        """
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
        """Add a new skill category to the CV.

        Appends a skill entry (label and details) to the skills section.
        Creates the section if it does not exist. Prevents duplicates by label.

        Args:
            skillToAdd: A Skills dataclass instance containing the label
                (e.g., 'Languages') and details (e.g., 'Python, JavaScript').

        Returns:
            str: A success message, or 'Duplicate label/skills' if a skill
                with the same label already exists.
        """
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
        """Modify the details of an existing skill category.

        Updates the details field of a skill identified by its label.
        The label itself cannot be changed with this method.

        Args:
            skillToModify: The label of the skill category to modify
                (e.g., 'Languages', 'Frameworks').
            new_value: The new details string to replace the existing one
                (e.g., 'Python, JavaScript, Go').

        Returns:
            str: A success message, or 'Skill not found.' if no skill
                with the given label exists.
        """
        skill_to_update = next((skill for skill in self.current_skills if skill.get('label') == skillToModify), None)
        if skill_to_update:
            skill_to_update["details"] = new_value
            self._auto_save_if_enabled()
            return "Successfully modified skill"
        return "Skill not found."

    @requires_data
    def delete_skill(self, skillName: str):
        """Delete a skill category from the CV by its label.

        Removes an entire skill entry (label and details) from the skills section.
        The skill is identified by its label.

        Args:
            skillName: The label of the skill category to delete
                (e.g., 'Languages', 'Frameworks').

        Returns:
            str: A success message, or an error message if no skills exist
                or the specified skill was not found.
        """
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
        """Add a new work experience entry to the CV.

        Appends a work experience entry to the experience section. Creates
        the section if it does not exist.

        Args:
            experienceToAdd: An Experience dataclass instance containing the
                work experience details (company, position, dates, location, highlights).

        Returns:
            str: A success message confirming the experience was added.
        """
        if "experience" not in self.data['cv']['sections']:
            self.data['cv']['sections']['experience'] = []
        self.current_experience.append(experienceToAdd.to_dict())
        self._auto_save_if_enabled()
        return "Successfully added experience"

    @requires_data
    def remove_experience(self, experience_name: str):
        """Remove a work experience entry from the CV by company name.

        Deletes an experience entry identified by its company name. The company
        name must match exactly.

        Args:
            experience_name: The company name of the experience entry to remove.

        Returns:
            str: A success message, or an error message if no experiences exist
                or the specified experience was not found.
        """
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
        """Modify a specific field of an existing work experience entry.

        Updates a single field of an experience entry identified by company name.
        Valid fields include company, position, dates, location, summary, and highlights.

        Args:
            company_name: The company name to identify the experience entry.
            field: The field to modify. Must be one of: company, position,
                start_date, end_date, location, summary, or highlights.
            new_value: The new value for the field. Type depends on the field
                (str for most, List[str] for highlights).

        Returns:
            str: A success message with the field and new value, or an error
                message if the field is invalid or the experience is not found.
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
        """Add a new education entry to the CV.

        Appends an education entry to the education section. Creates the section
        if it does not exist. Prevents duplicates by checking the institution name.

        Args:
            education_info: An Education dataclass instance containing the
                education details (institution, area, degree, dates, GPA, highlights).

        Returns:
            str: A success message, or 'Duplicate education entry' if an entry
                with the same institution already exists.
        """
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
        """Delete an education entry from the CV by institution name.

        Removes an education entry identified by its institution name. The
        institution name must match exactly.

        Args:
            InstutionName: The institution name of the education entry to delete.

        Returns:
            str: A success message, or an error message if no education entries
                exist or the specified institution was not found.
        """
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
        """Delete a project entry from the CV by its name.

        Removes a project from the projects section. The project is identified
        by its name field, which must match exactly.

        Args:
            project_name: The exact name of the project to delete.

        Returns:
            str: A success message with the deleted project name, or an error
                message if no projects exist or the project was not found.
        """
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
        """Add a new project entry to the CV.

        Appends a project to the projects section. Creates the section if it
        does not exist. Prevents duplicate projects by checking the name.

        Args:
            projectInfo: A Project dataclass instance containing the project
                details (name, dates, summary, highlights, etc.).

        Returns:
            str: A success message with the project name, or an error message
                if a project with the same name already exists.
        """
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
        """Generate project information using AI analysis and add it to the CV.

        Reads project insights from a JSON file, uses AI to analyze the project
        and generate resume-appropriate content, then adds it as a new project entry.

        Args:
            project_folder: Path to a JSON file containing project insights,
                including the 'project_root' key pointing to the project location.

        Returns:
            str: A success message with the project name, or an error message
                if the project already exists (delegated to add_project).
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
    def modify_connection(self, network_name: str, new_username: str):
        """Modify the username for an existing social network connection.

        Updates the username field of a social network connection identified
        by its network name (e.g., LinkedIn, GitHub).

        Args:
            network_name: The name of the social network to modify
                (e.g., 'LinkedIn', 'GitHub').
            new_username: The new username to set for the network profile.

        Returns:
            str: A success message with the network name, or an error message
                if the specified network was not found.
        """
        for idx, connection in enumerate(self.current_connections):
            if connection.get("network") == network_name:
                self.current_connections[idx]["username"] = new_username
                self._auto_save_if_enabled()
                return f"Successfully updated connection {network_name}"
        return f"Network {network_name} Cannot be found."

    @requires_data
    def delete_connection(self, connectionName: str):
        """Delete a social network connection from the CV by network name.

        Removes a social network connection identified by its network name.
        The network name must match exactly.

        Args:
            connectionName: The name of the social network to delete
                (e.g., 'LinkedIn', 'GitHub').

        Returns:
            str: A success message with the deleted network name, or an error
                message if no connections exist or the network was not found.
        """
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
        """Add a new social network connection to the CV.

        Appends a social network connection to the CV. Creates the social_networks
        section if it does not exist. Prevents duplicates by checking network name.

        Args:
            connectionInfo: A Connections dataclass instance containing the
                network name (e.g., 'LinkedIn') and username.

        Returns:
            str: A success message with the network name, or an error message
                if a connection with the same network already exists.
        """
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
        """Update the visual theme used for rendering the CV.

        Changes the RenderCV theme that determines the visual styling of the
        generated PDF. Available themes include classic, moderncv, sb2nov, etc.

        Args:
            selected_theme: The name of the theme to use (e.g., 'sb2nov',
                'classic', 'moderncv', 'engineeringresumes').

        Returns:
            str: A success message with the selected theme name.
        """
        self.data['design']['theme'] = selected_theme
        self._auto_save_if_enabled()
        return f"Successfully updated: {selected_theme}"

    @requires_data
    def update_contact(self, email=None, phone=None, location=None, website=None, name=None):
        """Update contact information fields in the CV.

        Updates one or more contact information fields. Only provided (non-None)
        fields are updated; others remain unchanged. Supports method chaining.

        Args:
            email: The email address to display on the CV. Optional.
            phone: The phone number to display on the CV. Optional.
            location: The location/address to display (e.g., 'City, State'). Optional.
            website: The personal website URL to display. Optional.
            name: The full name to display at the top of the CV. Optional.

        Returns:
            create_Render_CV: Returns self to allow method chaining.
        """
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