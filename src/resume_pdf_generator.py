
from dataclasses import dataclass
import pendulum as pd
from pathlib import Path
from typing import List,Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from Generate_AI_Resume import ResumeItem,OOPPrinciple,GenerateProjectResume



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
        self.story=[]



    def generate(self,data: ResumeItem,name:str="My Portfolio"):
        doc=SimpleDocTemplate(str(self.output_path),
                              pagesize=letter,
                              leftMargin=0.75 * inch,
                              rightMargin=0.75 * inch,
                              topMargin=0.75 * inch,
                              bottomMargin=0.75 * inch,
                              )

        self.story.append(Paragraph(f"<b>{name}<"
                                    f"/b>", self.styles['Title']))
        self.story.append(Paragraph(
            f"Generated on: {pd.now().date()}",
            self.styles['Normal']
        ))
        self.story.append(Spacer(1, 0.3 * inch))

        self.story.append(Paragraph(f"<b>{data.project_title}</b>", self.styles['Heading2']))
        self.story.append(Spacer(1, 0.3 * inch))

        self.story.append(Paragraph(data.detailed_summary, self.styles['Normal']))
        self.story.append(Spacer(1, 0.2 * inch))

        if data.key_responsibilities:
            self.story.append(Paragraph("<b>Key Responsibilities:</b>", self.styles['Heading3']))
            for responsibility in data.key_responsibilities:
                self.story.append(Paragraph(f"• {responsibility}", self.styles['Normal']))
            self.story.append(Spacer(1, 0.1 * inch))

        if data.key_skills_used:
            skills_text = f"<b>Skills:</b> {', '.join(data.key_skills_used)}"
            self.story.append(Paragraph(skills_text, self.styles['Normal']))

        if data.tech_stack:
            self.story.append(Paragraph(f"<b>Tech Stack:</b> {data.tech_stack}", self.styles['Normal']))

        if data.impact:
            self.story.append(Paragraph(f"<b>Impact:</b> {data.impact}", self.styles['Normal']))

        self.story.append(Spacer(1, 0.3 * inch))


        doc.build(self.story)
        return self.output_path





