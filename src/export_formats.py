from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from src.Generate_AI_Resume import ResumeItem
from src.app_context import AppContext

EXPORT_FORMATS = ("pdf", "html", "md")

def _sanitize_name(value: str) -> str:
    """Normalize a string for safe filesystem paths.

    Args:
        value: Raw name to normalize.

    Returns:
        Sanitized name with only safe characters.
    """
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip())
    cleaned = cleaned.strip("._-")
    return cleaned or "project"

def _normalize_formats(raw: str) -> List[str]:
    """Normalize a user-supplied format string into ordered formats.

    Args:
        raw: Raw input string (comma/space separated).

    Returns:
        Ordered list of valid formats or an empty list if invalid.
    """
    if not raw:
        return []

    tokens = [t for t in re.split(r"[,\s]+", raw.lower().strip()) if t]
    if not tokens:
        return []

    mapping = {
        "pdf": "pdf",
        "html": "html",
        "htm": "html",
        "md": "md",
        "markdown": "md",
    }

    resolved = []
    for token in tokens:
        normalized = mapping.get(token)
        if not normalized:
            return []
        resolved.append(normalized)

    ordered = []
    for fmt in EXPORT_FORMATS:
        if fmt in resolved and fmt not in ordered:
            ordered.append(fmt)
    return ordered

def prompt_export_formats(label: str) -> List[str]:
    """Prompt the user to select one or more export formats.

    Args:
        label: Label describing the export target (resume/portfolio).

    Returns:
        List of selected formats, or an empty list if the user skips.
    """
    prompt = (
        f"Select {label} export formats (pdf, html, md). "
        "Use commas to pick multiple, or press Enter for PDF. "
        "Type 'n' to skip: "
    )
    while True:
        raw = input(prompt).strip().lower()
        if not raw:
            return ["pdf"]
        if raw in {"n", "no"}:
            return []

        formats = _normalize_formats(raw)
        if formats:
            return formats

        print("Invalid selection. Examples: pdf, html, md, pdf,md.")

def _export_root(ctx: AppContext) -> Path:
    """Return the root directory for exports.

    Args:
        ctx: Application context with configured paths.

    Returns:
        Path to the export root directory.
    """
    return ctx.legacy_save_dir / "exports"

def _export_dir(ctx: AppContext, project_title: str, artifact: str) -> Path:
    """Build the export directory for a project and artifact type.

    Args:
        ctx: Application context with configured paths.
        project_title: Project title used to namespace exports.
        artifact: Artifact name (e.g., resume, portfolio).

    Returns:
        Path to the export directory.
    """
    project_dir = _export_root(ctx) / _sanitize_name(project_title)
    return project_dir / _sanitize_name(artifact)

def _render_markdown(item: ResumeItem, title: str) -> str:
    """Render a full resume/portfolio as Markdown.

    Args:
        item: Resume data to render.
        title: Document title.

    Returns:
        Markdown document as a string.
    """
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Project:** {item.project_title or 'Untitled project'}")
    lines.append("")

    lines.append("## One-Sentence Summary")
    lines.append(item.one_sentence_summary or "N/A")
    lines.append("")

    lines.append("## Detailed Summary")
    lines.append(item.detailed_summary or "N/A")
    lines.append("")

    lines.append("## Key Responsibilities")
    if item.key_responsibilities:
        lines.extend([f"- {resp}" for resp in item.key_responsibilities])
    else:
        lines.append("- None listed")
    lines.append("")

    lines.append("## Skills")
    if item.key_skills_used:
        lines.append(", ".join(item.key_skills_used))
    else:
        lines.append("None listed")
    lines.append("")

    lines.append("## Tech Stack")
    lines.append(item.tech_stack or "N/A")
    lines.append("")

    lines.append("## Impact")
    lines.append(item.impact or "N/A")
    lines.append("")

    lines.append("## OOP Principles")
    oop = item.oop_principles_detected or {}
    if oop:
        for name in sorted(oop.keys()):
            principle = oop[name]
            status = "Present" if principle.present else "Not detected"
            desc = principle.description or ""
            suffix = f" - {desc}" if desc else ""
            lines.append(f"- {name.title()}: {status}{suffix}")
    else:
        lines.append("- None detected")

    lines.append("")
    return "\n".join(lines)

def _render_html(item: ResumeItem, title: str) -> str:
    """Render a full resume/portfolio as HTML.

    Args:
        item: Resume data to render.
        title: Document title.

    Returns:
        HTML document as a string.
    """
    def esc(value: str) -> str:
        return html.escape(value or "")

    def list_items(items: Iterable[str]) -> str:
        items = list(items or [])
        if not items:
            return "<p>None listed</p>"
        return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

    oop = item.oop_principles_detected or {}
    oop_items = []
    for name in sorted(oop.keys()):
        principle = oop[name]
        status = "Present" if principle.present else "Not detected"
        desc = principle.description or ""
        detail = f" - {esc(desc)}" if desc else ""
        oop_items.append(f"<li><strong>{esc(name.title())}:</strong> {status}{detail}</li>")
    oop_html = "<ul>" + "".join(oop_items) + "</ul>" if oop_items else "<p>None detected</p>"

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{esc(title)}</title>
    <style>
      body {{
        font-family: "Georgia", "Times New Roman", serif;
        margin: 2rem auto;
        max-width: 800px;
        color: #1f1f1f;
        line-height: 1.6;
      }}
      h1, h2 {{
        color: #2c2c2c;
      }}
      h2 {{
        border-bottom: 1px solid #ddd;
        padding-bottom: 0.25rem;
      }}
      .meta {{
        color: #555;
      }}
    </style>
  </head>
  <body>
    <h1>{esc(title)}</h1>
    <p class="meta"><strong>Project:</strong> {esc(item.project_title or 'Untitled project')}</p>

    <h2>One-Sentence Summary</h2>
    <p>{esc(item.one_sentence_summary or 'N/A')}</p>

    <h2>Detailed Summary</h2>
    <p>{esc(item.detailed_summary or 'N/A')}</p>

    <h2>Key Responsibilities</h2>
    {list_items(item.key_responsibilities)}

    <h2>Skills</h2>
    <p>{esc(", ".join(item.key_skills_used)) if item.key_skills_used else "None listed"}</p>

    <h2>Tech Stack</h2>
    <p>{esc(item.tech_stack or 'N/A')}</p>

    <h2>Impact</h2>
    <p>{esc(item.impact or 'N/A')}</p>

    <h2>OOP Principles</h2>
    {oop_html}
  </body>
</html>
"""

def _resume_line_text(item: ResumeItem) -> str:
    """Build the single-line resume string used for resume-line exports.

    Args:
        item: Resume data to render.

    Returns:
        Single-line resume text.
    """
    project = item.project_title or "Project"
    summary = item.one_sentence_summary or ""
    tech_stack = item.tech_stack or ""
    impact = item.impact or ""
    return f"{project} - {summary}.{tech_stack} {impact}".strip()

def _render_resume_line_markdown(item: ResumeItem, title: str) -> str:
    """Render a resume line as Markdown.

    Args:
        item: Resume data to render.
        title: Document title.

    Returns:
        Markdown document as a string.
    """
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(_resume_line_text(item))
    lines.append("")
    return "\n".join(lines)

def _render_resume_line_html(item: ResumeItem, title: str) -> str:
    """Render a resume line as HTML.

    Args:
        item: Resume data to render.
        title: Document title.

    Returns:
        HTML document as a string.
    """
    def esc(value: str) -> str:
        return html.escape(value or "")

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{esc(title)}</title>
  </head>
  <body>
    <h1>{esc(title)}</h1>
    <p>{esc(_resume_line_text(item))}</p>
  </body>
</html>
"""

def export_resume_line(
    item: ResumeItem,
    ctx: AppContext,
    artifact: str,
    formats: Iterable[str],
    document_title: str,
) -> Tuple[Path, List[Path]]:
    """Export a resume line in the selected formats.

    Args:
        item: Resume data to export.
        ctx: Application context with configured paths.
        artifact: Base filename for the export.
        formats: Iterable of selected formats.
        document_title: Title to embed in rendered files.

    Returns:
        Tuple of export directory and list of saved file paths.
    """
    export_dir = _export_dir(ctx, item.project_title, artifact)
    export_dir.mkdir(parents=True, exist_ok=True)

    saved: List[Path] = []
    normalized = [fmt for fmt in EXPORT_FORMATS if fmt in formats]

    if "pdf" in normalized:
        from src.resume_pdf_generator import SimpleResumeGenerator

        generator = SimpleResumeGenerator(str(export_dir), data=item, fileName=artifact)
        generator.create_resume_line()
        file_name = f"{generator.project_title}_resume_line.pdf"
        saved.append(export_dir / file_name)

    if "html" in normalized:
        html_doc = _render_resume_line_html(item, document_title)
        html_path = export_dir / f"{artifact}.html"
        html_path.write_text(html_doc, encoding="utf-8")
        saved.append(html_path)

    if "md" in normalized:
        md_doc = _render_resume_line_markdown(item, document_title)
        md_path = export_dir / f"{artifact}.md"
        md_path.write_text(md_doc, encoding="utf-8")
        saved.append(md_path)

    return export_dir, saved

def export_resume_item(
    item: ResumeItem,
    ctx: AppContext,
    artifact: str,
    formats: Iterable[str],
    document_title: str,
    include_resume_line_pdf: bool = False,
) -> Tuple[Path, List[Path]]:
    """Export a full resume/portfolio in the selected formats.

    Args:
        item: Resume data to export.
        ctx: Application context with configured paths.
        artifact: Base filename for the export.
        formats: Iterable of selected formats.
        document_title: Title to embed in rendered files.
        include_resume_line_pdf: Whether to also create the resume-line PDF.

    Returns:
        Tuple of export directory and list of saved file paths.
    """
    export_dir = _export_dir(ctx, item.project_title, artifact)
    export_dir.mkdir(parents=True, exist_ok=True)

    saved: List[Path] = []
    normalized = [fmt for fmt in EXPORT_FORMATS if fmt in formats]

    if "pdf" in normalized:
        from src.resume_pdf_generator import SimpleResumeGenerator
        generator = SimpleResumeGenerator(str(export_dir), data=item, fileName=artifact)
        generator.generate(name=document_title)
        saved.append(export_dir / f"{artifact}.pdf")
        if include_resume_line_pdf:
            generator.create_resume_line()
            saved.append(export_dir / f"{generator.project_title}_resume_line.pdf")

    if "html" in normalized:
        html_doc = _render_html(item, document_title)
        html_path = export_dir / f"{artifact}.html"
        html_path.write_text(html_doc, encoding="utf-8")
        saved.append(html_path)

    if "md" in normalized:
        md_doc = _render_markdown(item, document_title)
        md_path = export_dir / f"{artifact}.md"
        md_path.write_text(md_doc, encoding="utf-8")
        saved.append(md_path)

    return export_dir, saved
