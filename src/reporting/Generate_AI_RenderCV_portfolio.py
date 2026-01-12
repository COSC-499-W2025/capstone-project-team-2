from functools import wraps
from pathlib import Path
from Generate_RenderCV_Resume import Project
import ruamel.yaml
import subprocess



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
    def load_starter_file(self,name:str=None):
        if name:
            self.name=name.replace(" ","_")
            self.yaml_file=self.cv_files_dir / f"{self.name}_CV.yaml"
        if not self.yaml_file.exists():
            raise FileNotFoundError(f"File {self.yaml_file} does not exist"
                                    f"Run generate_portfolio() first")

        with open(self.yaml_file,'r') as f:
            self.data=self.yaml.load(f)

        self.current_projects = self.data['cv']['sections'].get('projects')

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




