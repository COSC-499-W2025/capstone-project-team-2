from functools import wraps
from pathlib import Path
from Generate_RenderCV_Resume import Project, Connections
from Generate_AI_Resume import GenerateProjectResume
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
    def __init__(self,auto_save:bool=True,output_dir:str='rendercv_output'):
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




    def generate_portfolio(self,overwrite:bool=False,name:str="Jane Doe"):
        self.name=name.replace(" ","_")

        self.cv_files_dir.mkdir(parents=True,exist_ok=True)
        self.yaml_file=self.cv_files_dir / f"{self.name}_CV.yaml"
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
    def load_Protfolio_starter_file(self,name:str=None):
        if name:
            self.name=name.replace(" ","_")
            self.yaml_file=self.cv_files_dir / f"{self.name}_CV.yaml"
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist"
                                    f"Run generate_portfolio() first")

        with open(self.yaml_file,'r') as f:
            self.data=self.yaml.load(f)

        self.current_projects = self.data['cv']['sections'].get('projects')
        self.current_connections=self.data['cv'].get('social_networks')

        return self.data





    def save(self,filename:str=None):
        if self.data is None:
            raise ValueError("No data Loaded")
        output_file = Path(filename) if filename else self.yaml_file

        with open(output_file, 'w') as f:
            self.yaml.dump(self.data, f)

        # print(f"✓ Saved to {output_file}")
        return output_file

    def _auto_save_if_enabled(self):
        if self.auto_save and self.data is not None:
            self.save()


    @requires_data
    def add_new_portfolio_connection(self, connection_info: Connections):
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
        if self.current_connections is None or not self.current_connections:
            return "No connections to delete"

        connection = next((c for c in self.current_connections if c.get('network') == connection_name), None)
        if connection is None:
            return f"Connection '{connection_name}' not found"

        self.current_connections.remove(connection)
        self._auto_save_if_enabled()
        return f"Successfully deleted: {connection_name}"



    @requires_data
    def add_portfolio_project(self, projectInfo: Project):
        if self.current_projects is None:
            self.data['cv']['sections']['projects'] = []
            self.current_projects = self.data['cv']['sections']['projects']
        existing_projects = [p['name'] for p in self.current_projects]
        if projectInfo.name in existing_projects:
            return f"Project '{projectInfo.name}' already exists"
        self.current_projects.append(projectInfo.to_dict())
        self._auto_save_if_enabled()
        return f"Successfully added: {projectInfo.name}"
    
    @requires_data
    def modify_portfolio_project(self,project_name:str,field:str, new_value):
        valid_fields=['name','start_date','end_date','location','summary','highlights']
        if field not in valid_fields:
            return f"Invalid field: {field}. Valid fields are: {', '.join(valid_fields)}"
        project=next((for p in self.current_projects if p.get("name")==project_name),None)
        if project is None:
            return f"Project not found: {project_name}"
        project[field]=new_value
        self._auto_save_if_enabled()
        return f"Successfully modified: {project_name}"

    @requires_data
    def add_portfolio_project_from_AI(self, project_folder: str):

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
    def Remove_portfolio_project(self, project_name: str):
        if 'projects' not in self.data['cv']['sections'] or not self.current_projects:
            return "No projects to delete"

        project = next((p for p in self.current_projects if p.get('name') == project_name), None)
        if project is None:
            return f"Project not found: {project_name}"
        self.current_projects.remove(project)
        self._auto_save_if_enabled()
        return f"Successfully deleted: {project_name}"


    def render_portfolio(self):
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist")
        result_for_rendering=subprocess.run(["rendercv",str(self.yaml_file)],
                                            capture_output=True,
                                            text=True,
                                            encoding="utf-8",
                                            errors="replace")
        yaml_file_absolute=self.yaml_file.resolve()
        default_output=yaml_file_absolute.parent / "rendercv_output"
        source_filename=f"{self.name}_CV.pdf"
        source_pdf=default_output / source_filename
        if source_pdf.exists():
            return source_pdf
        else:
            return f"render failed - PDF not found at {source_pdf}", None




