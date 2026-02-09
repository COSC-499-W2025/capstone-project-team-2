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
    """Stores key information for generating a resume entry from a project."""
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
        """Create a ResumeProjectInfo instance from raw project data."""
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
    """AI-generated resume entry for a project."""
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
        load_dotenv()
        self.context = runtimeAppContext
        self.project_name = project_name
        self.project_data = None
        self.raw_project_data = None
        self.project_exists = self.context.store.project_exists(project_name)
        self._chain = None

    def _get_chain(self):
        """Lazily initialize the LangChain chain on first use."""
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
        """Fetch project data and return as ResumeProjectInfo dataclass."""
        self.raw_project_data = self.context.store.fetch_by_name(self.project_name)
        if self.raw_project_data:
            self.project_data = ResumeProjectInfo.from_project_data(self.raw_project_data)
        return self.project_data

    def _build_context_for_ai(self) -> str:
        """Build a context string from project data for the AI."""
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
        """Generate an AI-powered resume entry using Google GenAI."""
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
        return AIResumeEntry(
            project_title=result.get("project_title", ""),
            one_sentence_summary=result.get("one_sentence_summary", ""),
            detailed_summary=result.get("detailed_summary", ""),
            key_responsibilities=result.get("key_responsibilities", []),
            key_skills_used=result.get("key_skills_used", []),
            tech_stack=result.get("tech_stack", ""),
            impact=result.get("impact", ""),
        )


if __name__ == "__main__":
    generator = GenerateResumeAI_Ver2("dndDice.json")
    print(f"Project Name: {generator.project_name}")
    print(f"Project Exists: {generator.project_exists}")

    entry = generator.generate_AI_Resume_entry()
    if entry:
        print(f"\n--- AI Resume Entry ---")
        print(f"Title: {entry.project_title}")
        print(f"Summary: {entry.one_sentence_summary}")
        print(f"Details: {entry.detailed_summary}")
        print(f"Tech Stack: {entry.tech_stack}")
        print(f"Impact: {entry.impact}")
        print(f"\nResponsibilities:")
        for r in entry.key_responsibilities:
            print(f"  - {r}")
        print(f"\nSkills: {', '.join(entry.key_skills_used)}")

