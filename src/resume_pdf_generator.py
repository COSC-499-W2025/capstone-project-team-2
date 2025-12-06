import time
from dataclasses import dataclass
import pendulum as pd
from pathlib import Path
from typing import List,Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from src.Generate_AI_Resume import ResumeItem,GenerateProjectResume
from tqdm import tqdm
import os




class SimpleResumeGenerator:

    """
    Class used for generating a simple resume PDF for a given input data set.

    Detailed description:
    This class allows the creation of a PDF document that represents a resume or
    portfolio. It leverages tools like ReportLab for document creation and ProgressBar
    for tracking the generation process.

    The primary functionality includes setting up the document structure, adding
    different resume sections like title, project details, skills, key responsibilities,
    and generating the final PDF file saved at a specified output path.

    :ivar project_title: The title of the project to be included in the resume.
    :type project_title: str
    :ivar styles: A collection of styles used for formatting the PDF content.
    :type styles: StyleSheet1
    :ivar output_path: Path to the output PDF file where the resume is saved.
    :type output_path: Path
    :ivar story: A list of elements representing the content structure of the PDF.
    :type story: list
    :ivar data: The input data for populating the resume content.
    :type data: ResumeItem
    """
    def __init__(self,folderPath:str,data,fileName:str):
        self.project_title = None
        self.styles=getSampleStyleSheet()
        self.folder_path=Path(folderPath)
        self.story=[]
        self.data:ResumeItem=data
        self.project_title = self.data.project_title
        self.fileName=fileName


    def generate(self,name:str="My Portfolio"):
        """
        Generates a PDF document with structured content detailing the provided portfolio
        information. The document includes sections for project title, summary,
        responsibilities, skills, tech stack, impact, and a timestamp for generation and is created
        using the report lab python library to create the PDF.

        :param fileName:
        :param name: Title to be displayed on the first page of the document.
        :type name: str
        :return: None
        """
        # Creates a SimpleDocTemplate object to generate a PDF document.
        # The document will have a specific page size (letter), left, right, top, and
        # bottom margins (0.75 * inch each). The document will be saved at the location
        # specified by self.output_path.

        if os.path.exists(self.folder_path/f"{self.fileName}.pdf"):
            os.remove(self.folder_path/f"{self.fileName}.pdf")

        if os.path.exists(self.folder_path/f"{self.project_title}_resume_line.pdf"):
            os.remove(self.folder_path/f"{self.project_title}_resume_line.pdf")


        doc=SimpleDocTemplate(str(self.folder_path/f"{self.fileName}.pdf"),
                              pagesize=letter,  # Specifies the page size as letter.
                              leftMargin=0.75 * inch,  # Specifies the left margin.
                              rightMargin=0.75 * inch,  # Specifies the right margin.
                              topMargin=0.75 * inch,  # Specifies the top margin.
                              bottomMargin=0.75 * inch,  # Specifies the bottom margin.
                              )


        # Display the title of the document
        self.story.append(Paragraph(f"<b>{name}<"
                                    f"/b>", self.styles['Title']))
        # Display the date the document was generated
        self.story.append(Paragraph(
            f"Generated on: {pd.now().date()}",
            self.styles['Normal']
        ))
        # Add a small space between paragraphs
        self.story.append(Spacer(1, 0.3 * inch))

        # Display the project title
        self.story.append(Paragraph(f"<b>{self.data.project_title}</b>", self.styles['Heading2']))
        # Add a small space between paragraphs
        self.story.append(Spacer(1, 0.3 * inch))

        # Display the detailed summary of the project
        self.story.append(Paragraph(self.data.detailed_summary, self.styles['Normal']))
        # Add a small space between paragraphs
        self.story.append(Spacer(1, 0.2 * inch))

        # Display the key responsibilities if they exist
        if self.data.key_responsibilities:
            self.story.append(Paragraph("<b>Key Responsibilities:</b>", self.styles['Heading3']))
            for responsibility in self.data.key_responsibilities:
                self.story.append(Paragraph(f"• {responsibility}", self.styles['Normal']))
            # Add a small space between paragraphs
            self.story.append(Spacer(1, 0.1 * inch))

        # Display the skills used in the project if they exist
        if self.data.key_skills_used:
            skills_text = f"<b>Skills:</b> {', '.join(self.data.key_skills_used)}"
            self.story.append(Paragraph(skills_text, self.styles['Normal']))
            self.story.append(Spacer(1, 0.1 * inch))

        # Display the tech stack used in the project if it exists
        if self.data.tech_stack:
            self.story.append(Paragraph(f"<b>Tech Stack:</b> {self.data.tech_stack}", self.styles['Normal']))
            self.story.append(Spacer(1, 0.1 * inch))

        # Display the impact of the project if it exists
        if self.data.impact:
            self.story.append(Paragraph(f"<b>Impact:</b> {self.data.impact}", self.styles['Normal']))
            self.story.append(Spacer(1, 0.1 * inch))

        # Add a small space between paragraphs
        self.story.append(Spacer(1, 0.3 * inch))



        doc.build(self.story) #Here we are building the PDF to be saved to the system


    def create_resume_line(self):
        doc=SimpleDocTemplate(str(self.folder_path/f"{self.project_title}_resume_line.pdf"),
                              pagesize=letter,  # Specifies the page size as letter.
                              leftMargin=0.75 * inch,  # Specifies the left margin.
                              rightMargin=0.75 * inch,  # Specifies the right margin.
                              topMargin=0.75 * inch,  # Specifies the top margin.
                              bottomMargin=0.75 * inch,  # Specifies the bottom margin.
        )
        line = f"<b>{self.data.project_title}</b> — {self.data.one_sentence_summary}.{self.data.tech_stack} {self.data.impact}"
        paragraph = Paragraph(line, self.styles['Normal'])
        doc.build([paragraph,Spacer(1, 0.25 * inch)])


    def display_resume_line(self):
        self.create_resume_line()
        print(f"Resume Generated at: {self.folder_path}")

    def display_portfolio(self):
        self.generate()
        print(f"Portfolio Generated at: {self.folder_path}")


    def display_and_run(self):
        """
        Executes a visualization progress bar while invoking the generation of a PDF Portfolio.

        This method displays a progress bar while performing a task and then calls the `generate`
        method to complete the PDF Portfolio creation. Upon successful completion, it prints a
        confirmation message including the save location of the generated file.

        :return: None
        """
        #for i in tqdm(range(20), desc=f"Creating PDF Portfolio for {self.project_title}", unit="step"):
        #    time.sleep(1)
        self.display_portfolio()
        print("Portfolio has been created")


        #for i in tqdm(range(20), desc=f"Creating Resume PDF Line for {self.project_title}", unit="step"):
        #    time.sleep(1)
        self.display_resume_line()
        print(f"Resume Line has been created")
        print(f"Resume Line and Portfolio has been saved to {self.folder_path}")
       


