import json
import os


class SaveFileAnalysisAsJSON:
    """
    Persist analysis payloads to JSON on disk, without mutating them.

    Responsibilities:
    - Pretty-print the supplied dict (2-space indent, UTF-8)
    - Ensure the target directory exists
    - Write a single `<project_name>.json` file
    """

    def convertAnalysisToJSON(self, project_dict: dict) -> str:
        """Convert a dictionary to pretty JSON."""
        return json.dumps(project_dict, indent=2)
    
    def saveAnalysis(self, project_name: str, project_dict: dict, folder_path: str):
        """Save ``project_dict`` into ``folder_path`` as ``<project_name>.json``."""
        json_project = self.convertAnalysisToJSON(project_dict)
        write_file = os.path.join(folder_path, project_name + r".json")
        os.makedirs(folder_path, exist_ok=True)
        with open(write_file, "w", encoding="utf-8") as file:
            file.write(json_project)
