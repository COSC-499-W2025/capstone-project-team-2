from functools import wraps
from pathlib import Path
from src.reporting.Generate_RenderCV_Resume import Project, Connections
from src.reporting.Generate_AI_Resume import GenerateProjectResume
import ruamel.yaml
import subprocess
import orjson



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



class Create_Portfolio_RenderCV:
    """Builder class for creating and managing portfolio YAML files using RenderCV.

    Provides methods to generate, load, modify, and render portfolio files
    focused on showcasing projects and social network connections.

    Attributes:
        cv_files_dir: Path to directory where CV YAML files are stored.
        project_insight_folder: Path to directory containing project analysis files.
        current_projects: Cached list of project dictionaries from loaded data.
        current_connections: Cached list of social network connection dictionaries.
        name: Sanitized name used for filename generation.
        yaml: YAML parser instance with quote preservation enabled.
        data: Loaded YAML data structure.
        chosen_theme: Selected RenderCV theme for PDF generation.
        themes: Dictionary mapping theme names to descriptions.
        yaml_file: Path to the current YAML file being edited.
        auto_save: Flag indicating whether to save automatically after modifications.
        output_dir: Directory path for rendered output files.
    """

    def __init__(self, auto_save: bool = True, output_dir: str = 'rendercv_output'):
        """Initialize the Portfolio builder.

        Args:
            auto_save: If True, automatically save after each modification. Defaults to True.
            output_dir: Directory for rendered output files. Defaults to 'rendercv_output'.

        Returns:
            None: Constructor does not return a value.
        """
        self.cv_files_dir = Path(__file__).parent.parent.parent / "User_config_files" / "Generate_render_CV_files"
        self.project_insight_folder=Path(__file__).parent.parent.parent / "User_config_files" / "project_insights"
        self.current_projects=None #Cached list of project dictionaries
        self.current_connections=None #Cached list of Connections dictionaries
        self.name=None
        self.yaml=ruamel.yaml.YAML()
        self.yaml.preserve_quotes=True
        self.data=None
        self.chosen_theme='sb2nov'
        self.themes={
            'classic':'Classic CV theme',
            'engineeringclassic':'Engineering-focused CV theme',
            'engineeringresumes':'Engineering resume theme (recommended for resumes)',
            'moderncv':'Modern CV theme',
            'sb2nov':'Clean resume theme (recommended for resumes)',
        }
        self.yaml_file=None
        self.auto_save=auto_save
        self.output_dir=Path(output_dir)




    def generate_portfolio(self, overwrite: bool = False, name: str = "Jane Doe"):
        """Generate a starter portfolio YAML file with default template structure.

        Creates a minimal portfolio template with essential sections including
        contact information, social networks, and a projects section.

        Args:
            overwrite: If True, delete and regenerate existing file. If False, skip generation
                when file already exists. Defaults to False.
            name: The name to use for the portfolio file and as the default name in the template.
                Spaces are replaced with underscores for the filename. Defaults to 'Jane Doe'.

        Returns:
            str: 'Success' if file was created successfully, 'Skipping generation' if file
                exists and overwrite is False.
        """
        self.name = name.replace(" ", "_")

        self.cv_files_dir.mkdir(parents=True,exist_ok=True)
        self.yaml_file=self.cv_files_dir / f"{self.name}_Portfolio_CV.yaml"
        if self.yaml_file.exists():
            if overwrite:
                self.yaml_file.unlink()
            else:
                return "Skipping generation"

        portfolio_template = {
            'cv': {
                'name': self.name.replace('_', ' '),
                'location': 'City, State',
                'email': 'your.email@example.com',
                'phone':"+1 234 567 9801",
                'website': "https://yourwebsite.com",
                'social_networks':[
                    {'network': 'LinkedIn', 'username': ''},
                    {'network': 'GitHub', 'username': ''}
                ],
                'sections': {
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
        #Write the template to file
        with open(self.yaml_file,'w') as f:
            self.yaml.dump(portfolio_template,f)

        return "Success"

    def load_Protfolio_starter_file(self, name: str = None):
        """Load the portfolio YAML file into memory for editing.

        Parses the YAML file and initializes instance attributes for projects
        and connections. Must be called before any modification methods.

        Args:
            name: Optional name to load an existing file from the CV files directory
                without calling generate_portfolio() first. Spaces are replaced with
                underscores for filename lookup.

        Returns:
            dict: The loaded YAML data structure containing cv, design, and locale sections.

        Raises:
            FileNotFoundError: If the YAML file does not exist at the expected path.
        """
        if name:
            self.name=name.replace(" ","_")
            self.yaml_file=self.cv_files_dir / f"{self.name}_Portfolio_CV.yaml"
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist"
                                    f"Run generate_portfolio() first")

        with open(self.yaml_file,'r') as f:
            self.data=self.yaml.load(f)

        self.current_projects = self.data['cv']['sections'].get('projects')
        self.current_connections=self.data['cv'].get('social_networks')

        return self.data





    def save(self, filename: str = None):
        """Save the portfolio data to a YAML file.

        Persists the current in-memory data structure to disk. Can save to
        a custom path or the default yaml_file path.

        Args:
            filename: Optional custom file path to save to. If not provided,
                saves to the default yaml_file path set during generation or loading.

        Returns:
            Path: The path to the saved file.

        Raises:
            ValueError: If no data has been loaded into memory.
        """
        if self.data is None:
            raise ValueError("No data Loaded")
        output_file = Path(filename) if filename else self.yaml_file

        with open(output_file, 'w') as f:
            self.yaml.dump(self.data, f)

        return output_file

    def _auto_save_if_enabled(self):
        """Automatically save the portfolio to disk if auto-save mode is enabled.

        This internal method is called after each modification operation to
        persist changes immediately when auto_save is True.

        Args:
            None: This method takes no parameters.

        Returns:
            None: This method does not return a value; it saves as a side effect.
        """
        if self.auto_save and self.data is not None:
            self.save()

    @requires_data
    def add_new_portfolio_connection(self, connection_info: Connections):
        """Add a new social network connection to the portfolio.

        Appends a social network connection to the portfolio. Creates the
        social_networks section if it does not exist. Prevents duplicates
        by checking the network name.

        Args:
            connection_info: A Connections dataclass instance containing the
                network name (e.g., 'LinkedIn', 'GitHub') and username.

        Returns:
            str: A success message with the network name if added, or an error
                message if a connection with the same network already exists.
        """
        if self.current_connections is None:
            self.data['cv']['social_networks'] = []
            self.current_connections = self.data['cv']['social_networks']

        existing_networks = {c['network'] for c in self.current_connections}
        if connection_info.network in existing_networks:
            return f"Connection '{connection_info.network}' already exists"

        self.current_connections.append(connection_info.to_dict())
        self._auto_save_if_enabled()
        return f"Successfully added: {connection_info.network}"

    @requires_data
    def modify_portfolio_connection(self, network_name: str, new_username: str):
        """Modify the username for an existing social network connection.

        Updates the username field of a social network connection identified
        by its network name (e.g., LinkedIn, GitHub).

        Args:
            network_name: The name of the social network to modify
                (e.g., 'LinkedIn', 'GitHub', 'Twitter').
            new_username: The new username to set for the network profile.

        Returns:
            str: A success message with the network name if updated, or an error
                message if no connections exist or the network was not found.
        """
        if self.current_connections is None or not self.current_connections:
            return "No connections to modify"

        connection = next((c for c in self.current_connections if c.get('network') == network_name), None)
        if connection is None:
            return f"Connection '{network_name}' not found"

        connection['username'] = new_username
        self._auto_save_if_enabled()
        return f"Successfully updated: {network_name}"

    @requires_data
    def remove_portfolio_connection(self, connection_name: str):
        """Remove a social network connection from the portfolio by network name.

        Deletes a social network connection identified by its network name.
        The network name must match exactly (case-sensitive).

        Args:
            connection_name: The name of the social network to delete
                (e.g., 'LinkedIn', 'GitHub', 'Twitter').

        Returns:
            str: A success message with the deleted network name, or an error
                message if no connections exist or the network was not found.
        """
        if self.current_connections is None or not self.current_connections:
            return "No connections to delete"

        connection = next((c for c in self.current_connections if c.get('network') == connection_name), None)
        if connection is None:
            return f"Connection '{connection_name}' not found"

        self.current_connections.remove(connection)
        self._auto_save_if_enabled()
        return f"Successfully deleted: {connection_name}"



    @requires_data
    def add_portfolio_project(self, project_info: Project):
        """Add a new project entry to the portfolio.

        Appends a project to the projects section. Creates the section if it
        does not exist. Prevents duplicate projects by checking the name.

        Args:
            project_info: A Project dataclass instance containing the project
                details (name, dates, summary, highlights, etc.).

        Returns:
            str: A success message with the project name if added, or an error
                message if a project with the same name already exists.
        """
        if self.current_projects is None:
            self.data['cv']['sections']['projects'] = []
            self.current_projects = self.data['cv']['sections']['projects']
        existing_projects = [p['name'] for p in self.current_projects]
        if project_info.name in existing_projects:
            return f"Project '{project_info.name}' already exists"
        self.current_projects.append(project_info.to_dict())
        self._auto_save_if_enabled()
        return f"Successfully added: {project_info.name}"

    @requires_data
    def modify_portfolio_project(self, project_name: str, field: str, new_value):
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
            str: A success message with the project name if modified, or an error
                message if the field is invalid or the project is not found.
        """
        valid_fields = ['name', 'start_date', 'end_date', 'location', 'summary', 'highlights']
        if field not in valid_fields:
            return f"Invalid field: {field}. Valid fields are: {', '.join(valid_fields)}"
        project = next((p for p in self.current_projects if p.get("name") == project_name), None)
        if project is None:
            return f"Project not found: {project_name}"
        project[field] = new_value
        self._auto_save_if_enabled()
        return f"Successfully modified: {project_name}"

    @requires_data
    def add_portfolio_project_from_AI(self, project_folder: str):
        """Generate project information using AI analysis and add it to the portfolio.

        Reads project insights from a JSON file, uses AI (Google Gemini) to analyze
        the project codebase and generate portfolio-appropriate content, then adds
        it as a new project entry.

        Args:
            project_folder: Path to a JSON file containing project insights,
                including the 'project_root' key pointing to the project directory
                to be analyzed.

        Returns:
            str: A success message with the project name if added, or an error
                message if the project already exists (delegated to add_portfolio_project).
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
        print(f"AI analysis complete for: {ai_resume.project_title}")
        return self.add_portfolio_project(project)

    @requires_data
    def remove_portfolio_project(self, project_name: str):
        """Remove a project entry from the portfolio by its name.

        Deletes a project from the projects section. The project is identified
        by its name field, which must match exactly (case-sensitive).

        Args:
            project_name: The exact name of the project to delete.

        Returns:
            str: A success message with the deleted project name, or an error
                message if no projects exist or the project was not found.
        """
        if 'projects' not in self.data['cv']['sections'] or not self.current_projects:
            return "No projects to delete"

        project = next((p for p in self.current_projects if p.get('name') == project_name), None)
        if project is None:
            return f"Project not found: {project_name}"
        self.current_projects.remove(project)
        self._auto_save_if_enabled()
        return f"Successfully deleted: {project_name}"


    @requires_data
    def update_portfolio_contact(self,email: str = None,phone: str = None,location: str = None,website: str = None,name: str = None):
        """Update contact information in the portfolio.

        Updates one or more contact fields in the CV section. Only fields
        with non-None values are updated.

        Args:
            email: Email address to set.
            phone: Phone number to set.
            location: Location string (e.g., 'City, State').
            website: Website URL.
            name: Full name to display.

        Returns:
            str: A success message listing updated fields.
        """
        contact_section = self.data['cv']
        updated_fields = []

        fields = {
            'email': email,
            'phone': phone,
            'website': website,
            'location': location,
            'name': name
        }

        for field_name, value in fields.items():
            if value is not None:
                contact_section[field_name] = value
                updated_fields.append(field_name)

        self._auto_save_if_enabled()

        if updated_fields:
            return f"Successfully updated: {', '.join(updated_fields)}"
        return "No fields updated"



    def render_portfolio(self):
        """Render the portfolio to PDF format using RenderCV.

        Executes the RenderCV command-line tool to generate a PDF from the
        current YAML file. The PDF is saved to the rendercv_output directory
        next to the YAML file.

        Args:
            None: This method takes no parameters.

        Returns:
            Path: The path to the generated PDF file if successful.
            tuple: A tuple of (error_message, None) if rendering failed.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
        """
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist")
        subprocess.run(
            ["rendercv", str(self.yaml_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        yaml_file_absolute = self.yaml_file.resolve()
        default_output = yaml_file_absolute.parent / "rendercv_output"
        source_filename = f"{self.name}_Portfolio_CV.pdf"
        source_pdf = default_output / source_filename
        if source_pdf.exists():
            return source_pdf
        else:
            return f"render failed - PDF not found at {source_pdf}", None
