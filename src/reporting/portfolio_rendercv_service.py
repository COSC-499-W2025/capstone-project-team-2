"""
Portfolio RenderCV Service

This module adapts PortfolioShowcase domain objects into
RenderCV-compatible Project entries and manages CRUD operations
and PDF rendering via the existing create_Render_CV infrastructure.

Portfolio narrative logic lives in portfolio_service and RenderCV schema logic lives here.
"""

from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict, Iterable

from src.reporting.portfolio_service import PortfolioShowcase
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import RenderCVDocument, Project

class PortfolioRenderCVService:
    """
    RenderCV adapter for portfolio projects.
    Manages portfolio entries as RenderCV Project objects under: cv.sections.projects.
    """
    
    def __init__(self, name: str, auto_save: bool = True):
        """
        Initialize the portfolio RenderCV service.

        Args:
            name (str): Name used for the RenderCV YAML file.
            auto_save (bool): Automatically save YAML after each mutation.
        """
        self.cv = RenderCVDocument(doc_type='portfolio', auto_save=auto_save)
        self.cv.generate(name=name)
        self.cv.load(name=name)
        self._remove_placeholder_content()

    def _remove_placeholder_content(self) -> None:
        """Remove starter template placeholders via CRUD operations."""
        try:
            cv = (self.cv.data or {}).get("cv", {})
            for key, placeholder in {
                "email": "your.email@example.com",
                "phone": "+1 234 567 9801",
                "website": "https://yourwebsite.com",
                "location": "City, State",
            }.items():
                if cv.get(key) in ("", None, placeholder):
                    cv.pop(key, None)

            self.cv.remove_project("Project Name")

            if self.cv.current_connections:
                for conn in list(self.cv.current_connections):
                    network = conn.get("network")
                    username = (conn.get("username") or "").strip()
                    if network and not username:
                        self.cv.remove_connection(network)

            self.cv.save()
        except Exception:
            # Best-effort cleanup; continue with existing data if it fails.
            pass

    @staticmethod
    def build_rendercv_project(ps: PortfolioShowcase) -> Project:
        """
        Convert a PortfolioShowcase into a RenderCV Project.

        Output strictly follows RenderCV docs:
            cv.sections.projects[]

        Args:
            ps (PortfolioShowcase): Curated portfolio narrative.

        Returns:
            Project: RenderCV-compatible project entry.
        """
        highlights: List[str] = list(ps.technical_highlights or [])

        # Enrich highlights with design quality
        design_comment = ps.design_quality.get("oop_comment")
        if design_comment:
            highlights.append(f"OOP Design: {design_comment}")

        # Add contributor info as a bullet
        if ps.contributors:
            highlights.append(
                f"Contributors: {', '.join(ps.contributors)}"
            )

        return Project(
            name=ps.title,
            summary=ps.overview,
            highlights=highlights,
            # Optional fields
            start_date=None,
            end_date=None,
            location=None,
        )

    def add_portfolio(self, ps: PortfolioShowcase) -> str:
        """
        Add a portfolio entry as a RenderCV project.

        Args:
            ps (PortfolioShowcase): Portfolio narrative.

        Returns:
            str: Status message from create_Render_CV.add_project
        """
        project = self.build_rendercv_project(ps)
        return self.cv.add_project(project)

    def list_portfolios(self) -> List[dict]:
        """
        List all portfolio projects.

        Returns:
            List[dict]: RenderCV project dictionaries.
        """
        return self.cv.current_projects or []

    def get_portfolio(self, project_name: str) -> Optional[dict]:
        """
        Retrieve a single portfolio project by name.

        Args:
            project_name (str): Project name.

        Returns:
            dict | None: Project entry if found.
        """
        if not self.cv.current_projects:
            return None
        return next(
            (p for p in self.cv.current_projects if p.get("name") == project_name),
            None
        )

    def update_portfolio(self, project_name: str, field: str, value: Any) -> str:
        """
        Update a specific field on a portfolio project.

        Valid fields:
            - name
            - start_date
            - end_date
            - location
            - summary
            - highlights

        Args:
            project_name (str): Project identifier.
            field (str): Field to update.
            value: New value.

        Returns:
            str: Status message.
        """
        return self.cv.modify_project(
            project_name=project_name,
            field=field,
            new_value=value
        )

    def delete_portfolio(self, project_name: str) -> str:
        """
        Delete a portfolio project.

        Args:
            project_name (str): Project name.

        Returns:
            str: Status message.
        """
        return self.cv.remove_project(project_name)

    def render_portfolio_pdf(self) -> Tuple[str, Optional[Path]]:
        """
        Render portfolio projects to PDF using RenderCV.

        Returns:
            Tuple[str, Path | None]: Render status and PDF path.
        """
        status, outputs = self.render_portfolio_outputs(["pdf"])
        pdf_paths = outputs.get("pdf", [])
        return status, pdf_paths[0] if pdf_paths else None

    def render_portfolio_outputs(self, formats: Iterable[str]) -> Tuple[str, Dict[str, List[Path]]]:
        """
        Render portfolio projects to multiple formats using RenderCV.

        Args:
            formats: Iterable of output formats (pdf, html, markdown)

        Returns:
            Tuple[str, Dict[str, List[Path]]]: Render status and output mapping.
        """
        return self.cv.render_outputs(formats=formats)
