
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List,Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


@dataclass()
class ResumeProject:
    title:str
    description:str
    skills : list[str]
    highlights: Optional[list[str]]= None


class SimpleResumeGenerator:
    def __init__(self,filePath:str):
        self.styles=getSampleStyleSheet()
        self.output_path=Path(filePath)



    def generate(self):
        doc=SimpleDocTemplate(str(self.output_path),
                              pagesize=letter,
                              leftMargin=0.75 * inch,
                              rightMargin=0.75 * inch,
                              topMargin=0.75 * inch,
                              bottomMargin=0.75 * inch,
                              )
        story=[]


