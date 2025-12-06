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
        """
        Initialize the SimpleResumeGenerator with the required configuration.

        This constructor sets up the necessary attributes for generating PDF documents,
        including the output folder path, resume data, and filename. It initializes
        the ReportLab styles and prepares an empty story list for building the PDF content.

        :param folderPath: The directory path where the generated PDF files will be saved.
        :type folderPath: str
        :param data: The resume data object containing project information and details.
        :type data: ResumeItem
        :param fileName: The base filename for the generated portfolio PDF (without extension).
        :type fileName: str
        """
        self.project_title = None
        self.styles=getSampleStyleSheet()
        self.folder_path=Path(folderPath)
        self.story=[]
        self.data:ResumeItem=data
        self.project_title = self.data.project_title
        self.fileName=fileName


    def generate(self,name:str="My Portfolio"):
        """
        Generate a PDF portfolio document with structured resume content.

        This method creates a complete PDF document containing the portfolio information
        including the document title, generation date, project title, detailed summary,
        key responsibilities, skills, tech stack, and impact sections. The PDF is created
        using the ReportLab library and saved to the configured folder path.

        If a PDF file with the same name already exists, it will be removed before
        generating the new file to prevent conflicts.

        :param name: Title to be displayed on the first page of the document.
        :type name: str
        :return: None
        :rtype: None
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
        """
        Create a condensed one-line resume PDF document.

        This method generates a separate PDF file containing a single-line summary
        of the project, suitable for use as a quick reference or resume bullet point.
        The line includes the project title, one-sentence summary, tech stack, and
        impact statement formatted in a concise format.

        The output file is named using the project title with '_resume_line.pdf' suffix.

        :return: None
        :rtype: None
        """
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
        """
        Generate the resume line PDF and display a confirmation message.

        This method wraps the create_resume_line() method and prints a confirmation
        message to stdout indicating the location where the resume line PDF was saved.

        :return: None
        :rtype: None
        """
        self.create_resume_line()
        print(f"Resume Generated at: {self.folder_path}")

    def display_portfolio(self):
        """
        Generate the portfolio PDF and display a confirmation message.

        This method wraps the generate() method and prints a confirmation message
        to stdout indicating the location where the portfolio PDF was saved.

        :return: None
        :rtype: None
        """
        self.generate()
        print(f"Portfolio Generated at: {self.folder_path}")


    def display_and_run(self):
        """
        Generate both the portfolio and resume line PDFs with confirmation messages.

        This is the primary convenience method for generating all resume artifacts at once.
        It calls display_portfolio() to create the full portfolio PDF and display_resume_line()
        to create the condensed one-line resume PDF. Upon successful completion, it prints
        confirmation messages indicating where the files were saved.

        :return: None
        :rtype: None
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
       


