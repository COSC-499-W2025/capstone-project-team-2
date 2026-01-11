import yaml
from pathlib import Path


class PortfolioData:
    """
    Data container for portfolio PDF generation.
    
    This class transforms portfolio showcase data and analysis results into
    a format compatible with the SimpleResumeGenerator PDF generator.
    
    Attributes:
        project_title (str): The project title for the portfolio.
        one_sentence_summary (str): One-line summary of the project.
        detailed_summary (str): Detailed overview of the project.
        key_skills_used (list): List of skills used in the project.
        tech_stack (str): Comma-separated list of technologies/frameworks.
        key_responsibilities (list): Key technical highlights/responsibilities.
        impact (str): Description of the project's impact/design quality.
        oop_principles_detected (dict): OOP metrics (kept for compatibility).
    """
    
    def __init__(self, portfolio_showcase: dict, analysis: dict):
        self.project_title = portfolio_showcase.get('title', 'Portfolio')
        self.one_sentence_summary = portfolio_showcase.get('overview', '')
        self.detailed_summary = portfolio_showcase.get('overview', '')
        self.key_skills_used = portfolio_showcase.get('skills', [])
        frameworks = analysis.get('resume_item', {}).get('frameworks', [])
        self.tech_stack = ', '.join(frameworks) if frameworks else 'Not specified'
        self.key_responsibilities = portfolio_showcase.get('technical_highlights', [])
        self.impact = portfolio_showcase.get('design_quality', {}).get('oop_comment', '')
        self.oop_principles_detected = {}

def display_portfolio_showcase(ps: dict) -> None:
    """
    Display formatted portfolio showcase.
    
    Args:
        ps (dict): Portfolio showcase data to display.
    """
    print("\n===============================")
    print(" PORTFOLIO SHOWCASE")
    print("===============================\n")

    print(f"Project: {ps.get('title')}")
    if ps.get("role"):
        print(f"Role   : {ps.get('role')}\n")

    if ps.get("overview"):
        print("Overview:")
        print(ps["overview"], "\n")

    if ps.get("technical_highlights"):
        print("Technical Highlights:")
        for h in ps["technical_highlights"]:
            print(f"• {h}")
        print()

    design_quality = ps.get("design_quality", {})
    if design_quality:
        print("Design Quality:")
        if design_quality.get("oop_rating"):
            print(f"• OOP Rating: {design_quality['oop_rating']}")
        if design_quality.get("oop_comment"):
            print(f"• Comment: {design_quality['oop_comment']}")
        if design_quality.get("inheritance_classes"):
            print(f"• Classes with Inheritance: {design_quality['inheritance_classes']}")
        if design_quality.get("max_loop_depth") is not None:
            print(f"• Max Loop Depth: {design_quality['max_loop_depth']}")
        print()

    evidence = ps.get("evidence", {})
    if evidence:
        print("Evidence:")
        if evidence.get("files_analyzed"):
            print(f"• Files Analyzed: {evidence['files_analyzed']}")
        if evidence.get("total_functions"):
            print(f"• Total Functions: {evidence['total_functions']}")
        if evidence.get("collection_literals"):
            print(f"• Collection Literals: {evidence['collection_literals']}")
        print()

    if ps.get("skills"):
        print("Skills:")
        for skill in ps["skills"]:
            print(f"• {skill}")
        print()

    if ps.get("contributors"):
        print("Contributors:")
        for contrib in ps["contributors"]:
            print(f"• {contrib}")
        print()


def load_portfolio_showcase(project_name: str) -> dict:
    """
    Load human-authored portfolio showcase content for a project.
    
    Args:
        project_name (str):
            The project identifier used to locate the corresponding portfolio
            YAML file.

    Returns:
        dict:
            Parsed portfolio configuration data from YAML, or an empty
            dictionary if no portfolio customization file is found.
    """
    base = Path(__file__).parent.parent.parent / "User_config_files" / "portfolio_showcases"
    path = base / f"{project_name}.yaml"

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def build_portfolio_showcase(analysis: dict, portfolio_yaml: dict) -> dict:
    """
    Build curated portfolio output, separate from raw analysis and resume content.

    This function transforms technical analysis metrics into a human-readable
    portfolio narrative.

    Args:
        analysis (dict): Full project analysis output.
        portfolio_yaml (dict): Optional human-authored YAML overrides.

    Returns:
        dict: Structured portfolio showcase content.
    """
    resume_item = analysis.get("resume_item", {})
    oop = analysis.get("oop_analysis") or {}

    score = oop.get("score", {})
    classes = oop.get("classes", {})
    complexity = oop.get("complexity", {})
    data_structs = oop.get("data_structures", {})

    return {
        "title": portfolio_yaml.get("project", {}).get(
            "title", resume_item.get("project_name")
        ),

        "role": portfolio_yaml.get("project", {}).get("role"),

        "overview": portfolio_yaml.get("portfolio", {}).get(
            "overview",
            resume_item.get("summary"),
        ),

        "technical_highlights": portfolio_yaml.get("portfolio", {}).get(
            "highlights",
            [
                f"{classes.get('count', 0)} classes across multiple languages",
                f"Average {classes.get('avg_methods_per_class', 0)} methods per class",
                f"OOP score: {score.get('oop_score', 'N/A')} ({score.get('rating', '')})",
            ],
        ),

        "design_quality": {
            "oop_rating": score.get("rating"),
            "oop_comment": score.get("comment"),
            "inheritance_classes": classes.get("with_inheritance"),
            "max_loop_depth": complexity.get("max_loop_depth"),
        },

        "evidence": {
            "files_analyzed": oop.get("files_analyzed"),
            "total_functions": complexity.get("total_functions"),
            "collection_literals": sum(
                data_structs.get(k, 0)
                for k in ["list_literals", "dict_literals", "set_literals", "tuple_literals"]
            ),
        },

        "skills": resume_item.get("skills", []),
        "contributors": list((analysis.get("contributors") or {}).keys()),
    }