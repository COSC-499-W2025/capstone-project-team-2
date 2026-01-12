from src.reporting.Generate_RenderCV_Resume import create_Render_CV
from src.reporting.Generate_RenderCV_Resume import Project
import ruamel.yaml
from pathlib import Path



class Create_Portfolio_RenderCV:
    def __init__(self,auto_save:bool=True,output_dir:str='rendercv_output'):
        self.cv_files_dir = Path(__file__).parent.parent.parent / "User_config_files" / "Generate_render_CV_files"
        self.project_insight_folder = Path(__file__).parent.parent.parent / "User_config_files" / "project_insights"
        self.yaml=ruamel.yaml.YAML()
        self.yaml.preserve_quotes=True
        self.name=None
        self.data=None
        self.current_projects=None
        self.chosen_theme='sb2nov'
        self.themes = {
            'classic': 'Classic CV theme',
            'engineeringclassic': 'Engineering-focused CV theme',
            'engineeringresumes': 'Engineering resume theme (recommended for resumes)',
            'moderncv': 'Modern CV theme',
            'sb2nov': 'Clean resume theme (recommended for resumes)'}
        self.auto_save=auto_save
        self.output_dir=Path(output_dir)
        self.yaml_file=None

    def generate_starter_portfolio(self,overwrite:bool=False,name:str="Jane Doe"):
        self.name = name.replace(" ", "_")
        self.cv_files_dir.mkdir(parents=True, exist_ok=True)
        self.yaml_file=self.cv_files_dir / f"{self.name}_CV.yaml"
        if overwrite:
            self.yaml_file.unlink()
        else:
            return "Skipping Generation"
