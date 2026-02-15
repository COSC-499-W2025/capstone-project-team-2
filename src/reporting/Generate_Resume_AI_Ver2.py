import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from src.core.app_context import runtimeAppContext


@dataclass
class ResumeProjectInfo:
    """
    Stores key information extracted from a database project record
    for generating a resume entry. Fields are populated from the
    analysis JSON stored in the project_data table.
    """
    # Basic project info
    project_name: str
    project_type: str  # 'individual' or 'team'

    # Skills and technologies
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)

    # Resume content
    summary: str = ""
    highlights: List[str] = field(default_factory=list)

    # Code quality metrics
    oop_score: float = 0.0
    oop_rating: str = ""  # 'low', 'medium', 'high'

    # Additional context
    duration_estimate: str = ""
    framework_sources: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def from_project_data(cls, data: dict) -> "ResumeProjectInfo":
        """
        Create a ResumeProjectInfo instance from raw project analysis data
        retrieved from the database.

        Args:
            data: The analysis dictionary returned by fetch_by_name(), expected
                to contain top-level keys 'resume_item', 'oop_analysis',
                'project_type', and 'duration_estimate'.

        Returns:
            ResumeProjectInfo: A populated dataclass with project name, type,
                skills, languages, frameworks, summary, highlights, OOP score
                and rating, duration estimate, and framework sources.
        """
        resume_item = data.get("resume_item", {})
        oop_analysis = data.get("oop_analysis", {})
        oop_score_info = oop_analysis.get("score", {})
        project_type_info = data.get("project_type", {})

        return cls(
            project_name=resume_item.get("project_name", ""),
            project_type=project_type_info.get("project_type", "unknown"),
            skills=resume_item.get("skills", []),
            languages=resume_item.get("languages", []),
            frameworks=resume_item.get("frameworks", []),
            summary=resume_item.get("summary", ""),
            highlights=resume_item.get("highlights", []),
            oop_score=oop_score_info.get("oop_score", 0.0),
            oop_rating=oop_score_info.get("rating", ""),
            duration_estimate=data.get("duration_estimate", ""),
            framework_sources=resume_item.get("framework_sources", {}),
        )


@dataclass
class AIResumeEntry:
    """
    AI-generated resume entry for a project. Represents the polished
    output from the Gemini LLM, ready to be mapped into a RenderCV
    Project for document generation.
    """
    project_title: str
    one_sentence_summary: str
    detailed_summary: str
    key_responsibilities: List[str] = field(default_factory=list)
    key_skills_used: List[str] = field(default_factory=list)
    tech_stack: str = ""
    impact: str = ""


class GenerateResumeAI_Ver2():
    # Prompt template for generating resume entries
    RESUME_PROMPT = """
You are an expert technical resume writer.

You are given analyzed data from a software project including:
- Project name and type
- Programming languages and frameworks used
- Skills demonstrated
- OOP analysis scores and metrics
- Project highlights

Based on this information, generate a professional resume entry.

Return a single JSON object:
{{
  "project_title": "...",
  "one_sentence_summary": "A concise, impactful one-liner for the resume",
  "detailed_summary": "2-3 sentences describing the project in detail",
  "key_responsibilities": [
    "Action-oriented bullet point...",
    "Another responsibility..."
  ],
  "key_skills_used": [
    "skill1",
    "skill2"
  ],
  "tech_stack": "Short summary of main technologies",
  "impact": "Brief statement about project impact or achievements"
}}

Guidelines:
- Use strong action verbs (Developed, Implemented, Designed, Built, etc.)
- Quantify achievements where possible
- Focus on technical accomplishments
- Keep bullet points concise but impactful
- Highlight OOP principles if the score is medium or high

PROJECT DATA:
{project_data}
"""

    def __init__(self, project_name: str):
        """
        Initialize the generator for a given database project.

        Loads environment variables, checks whether the project exists in
        the database, and prepares instance state. The LangChain LLM chain
        is lazily initialized on first use to avoid requiring a Google API
        key until generation is actually requested.

        Args:
            project_name: The Pname primary key of the project in the
                project_data database table.

        Returns:
            None: Sets instance attributes project_name, project_exists,
                project_data, raw_project_data, and _chain.
        """
        load_dotenv()
        self.context = runtimeAppContext
        self.project_name = project_name
        self.project_data = None
        self.raw_project_data = None
        self.project_exists = self.context.store.project_exists(project_name)
        self._chain = None

    def _get_chain(self):
        """
        Lazily initialize and return the LangChain processing chain.

        Reads the GOOGLE_API_KEY from the environment on first call,
        creates the ChatGoogleGenerativeAI LLM, JSON output parser, and
        prompt template, then composes them into a chain. Subsequent calls
        return the cached chain.

        Args:
            None: Uses GOOGLE_API_KEY from the environment and the class-level
                RESUME_PROMPT template.

        Returns:
            Chain: A LangChain chain composed of PromptTemplate, ChatGoogleGenerativeAI,
                and JsonOutputParser that accepts a 'project_data' input and
                returns a parsed JSON dictionary.
        """
        if self._chain is None:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise RuntimeError("Missing GOOGLE_API_KEY in .env file")

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=google_api_key
            )
            parser = JsonOutputParser()
            prompt = PromptTemplate.from_template(self.RESUME_PROMPT)
            self._chain = prompt | llm | parser
        return self._chain

    def get_info_about_project(self) -> ResumeProjectInfo | None:
        """
        Fetch the project analysis data from the database and convert it
        into a structured ResumeProjectInfo dataclass. Also stores the raw
        database response in self.raw_project_data for reference.

        Args:
            None: Uses self.project_name to query the database via
                self.context.store.fetch_by_name().

        Returns:
            ResumeProjectInfo | None: A populated ResumeProjectInfo if the
                project was found in the database, or None if no record exists.
        """
        self.raw_project_data = self.context.store.fetch_by_name(self.project_name)
        if self.raw_project_data:
            self.project_data = ResumeProjectInfo.from_project_data(self.raw_project_data)
        return self.project_data

    def _build_context_for_ai(self) -> str:
        """
        Build a human-readable context string from the structured project
        data to be injected into the LLM prompt. Automatically calls
        get_info_about_project() if project_data has not been loaded yet.

        Args:
            None: Uses self.project_data, which is populated by
                get_info_about_project().

        Returns:
            str: A formatted multi-line string containing the project name,
                type, languages, frameworks, skills, summary, OOP score,
                duration estimate, and highlights. Returns an empty string
                if no project data is available.
        """
        if not self.project_data:
            self.get_info_about_project()

        if not self.project_data:
            return ""

        info = self.project_data
        context_parts = [
            f"Project Name: {info.project_name}",
            f"Project Type: {info.project_type}",
            f"Languages: {', '.join(info.languages) if info.languages else 'Not detected'}",
            f"Frameworks: {', '.join(info.frameworks) if info.frameworks else 'Not detected'}",
            f"Skills: {', '.join(info.skills) if info.skills else 'Not detected'}",
            f"Summary: {info.summary}",
            f"OOP Score: {info.oop_score} ({info.oop_rating})",
            f"Duration Estimate: {info.duration_estimate}",
            f"Highlights:",
        ]
        for h in info.highlights:
            context_parts.append(f"  - {h}")

        return "\n".join(context_parts)

    def generate_AI_Resume_entry(self) -> AIResumeEntry | None:
        """
        Generate an AI-polished resume entry by fetching project data from
        the database, building a context string, and invoking the Gemini
        LLM via LangChain. This is the main entry point for producing a
        resume-ready project description.

        Args:
            None: Uses self.project_name and self.project_exists to validate,
                then delegates to _build_context_for_ai() and _get_chain().

        Returns:
            AIResumeEntry | None: A populated AIResumeEntry dataclass with
                project_title, one_sentence_summary, detailed_summary,
                key_responsibilities, key_skills_used, tech_stack, and impact.
                Returns None if the project does not exist in the database or
                if no analysis data is available.
        """
        if not self.project_exists:
            print(f"Project '{self.project_name}' not found in database.")
            return None

        context = self._build_context_for_ai()
        if not context:
            print("No project data available.")
            return None

        print(f"Generating AI resume entry for: {self.project_data.project_name}")

        # Invoke the LangChain chain
        result = self._get_chain().invoke({"project_data": context})

        # Convert result to dataclass
        key_responsibilities = list(result.get("key_responsibilities", []))
        tech_stack = result.get("tech_stack", "")

        # Add tech stack as a highlight if detected
        if tech_stack:
            key_responsibilities.append(f"Tech Stack: {tech_stack}")

        return AIResumeEntry(
            project_title=result.get("project_title", ""),
            one_sentence_summary=result.get("one_sentence_summary", ""),
            detailed_summary=result.get("detailed_summary", ""),
            key_responsibilities=key_responsibilities,
            key_skills_used=result.get("key_skills_used", []),
            tech_stack=tech_stack,
            impact=result.get("impact", ""),
        )




