import json
from pathlib import Path
from typing import Any

# Render saved analyses as portfolio-style output, honoring consent settings.
from src.core.app_context import AppContext
from src.reporting.Generate_AI_Resume import GenerateProjectResume, ResumeItem
from src.reporting.resume_pdf_generator import SimpleResumeGenerator
from src.reporting.portfolio_rendercv_service import PortfolioRenderCVService
from src.reporting.portfolio_service import (
    load_portfolio_showcase,
    build_portfolio_showcase,
    display_portfolio_showcase,
)
import os
import shutil

def display_portfolio_and_generate_pdf(
    path: Path,
    ctx: AppContext,
    *,
    generate_pdf: bool = False,
    output_name: str = "Portfolio",
    custom_output_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Read a saved project JSON file and display a formatted portfolio summary.
    Optionally generate a PDF using RenderCV or legacy PDF generator.

    Args:
        path (Path): Saved analysis file.
        ctx (AppContext): Shared context for consent/config paths.
        generate_pdf (bool): If true, generates PDF output.
        output_name (str): Output filename stem for generated portfolio.
        custom_output_dir (Path | None): Optional destination directory to copy PDF into.

    Returns:
        dict[str, Any]: Summary of rendering and optional export results.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"status": "error", "detail": f"Could not read {path.name}: {e}"}

    has_external = ctx.external_consent

    if not has_external:
        analysis = data if isinstance(data, dict) else {}
        if "analysis" in analysis and isinstance(analysis["analysis"], dict):
            analysis = analysis["analysis"]

        project_name = analysis.get("resume_item", {}).get("project_name", "Portfolio")

        # Rebuild PortfolioShowcase object 
        portfolio_yaml = load_portfolio_showcase(project_name)
        ps = build_portfolio_showcase(analysis, portfolio_yaml)

        display_portfolio_showcase(ps)

        if not generate_pdf:
            return {"status": "ok", "mode": "local", "pdf_generated": False}

        if custom_output_dir is not None and not custom_output_dir.exists():
            return {"status": "error", "detail": f"Path not found: {custom_output_dir}"}

        try:
            print("[INFO] Generating portfolio PDF using RenderCV...")

            service = PortfolioRenderCVService(name=output_name)
            service.add_portfolio(ps)
            status, pdf_path = service.render_portfolio_pdf()

            print(f"[INFO] RenderCV status: {status}")
            if pdf_path:
                print(f"[INFO] Portfolio PDF generated at: {pdf_path}")
                if custom_output_dir is not None:
                    custom_path = custom_output_dir / pdf_path.name
                    shutil.copy2(pdf_path, custom_path)
                    print(f"[INFO] PDF saved to: {custom_path}")
                    return {
                        "status": "ok",
                        "mode": "local",
                        "pdf_generated": True,
                        "pdf_path": str(custom_path),
                    }
                return {
                    "status": "ok",
                    "mode": "local",
                    "pdf_generated": True,
                    "pdf_path": str(pdf_path),
                }
            return {"status": "error", "detail": "RenderCV did not return a PDF path."}

        except Exception as e:
            print(f"[WARN] RenderCV export failed, falling back to legacy PDF: {e}")
            if custom_output_dir is None:
                return {
                    "status": "error",
                    "detail": (
                        "RenderCV export failed and no custom_output_dir provided "
                        "for legacy PDF fallback."
                    ),
                }

            resume_item = analysis.get("resume_item") or {}
            tech_stack_parts = []
            if resume_item.get("languages"):
                tech_stack_parts.extend(resume_item.get("languages") or [])
            if resume_item.get("frameworks"):
                tech_stack_parts.extend(resume_item.get("frameworks") or [])

            legacy_data = ResumeItem(
                project_title=resume_item.get("project_name", ps.title),
                one_sentence_summary=resume_item.get("summary", ps.overview),
                detailed_summary=ps.overview or resume_item.get("summary", ""),
                key_responsibilities=list(ps.technical_highlights or []),
                key_skills_used=list(resume_item.get("skills") or []),
                tech_stack=", ".join(tech_stack_parts),
                impact="",
                oop_principles_detected={},
            )
            SimpleResumeGenerator(
                str(custom_output_dir),
                data=legacy_data,
                fileName=output_name,
            ).display_and_run(portfolio_only=True)
            return {
                "status": "ok",
                "mode": "local",
                "pdf_generated": True,
                "pdf_path": str(Path(custom_output_dir) / f"{output_name}.pdf"),
                "fallback": "legacy_pdf_generator",
            }

    try:
        directory_file_path = data.get("project_root")
        docker = GenerateProjectResume(directory_file_path).generate(
            saveToJson=False
        )
    except Exception as e:
        return {"status": "error", "detail": f"Could not generate portfolio: {e}"}

    print("\n===============================")
    print(f"PROJECT: {docker.project_title}")
    print("===============================\n")
    print(f"One-Sentence Summary: {docker.one_sentence_summary}\n")

    print("Key Skills Used:")
    for skill in docker.key_skills_used:
        print(f"  • {skill}")
    print()

    print("Tech Stack:")
    tech_stack = docker.tech_stack
    if isinstance(tech_stack, str):
        tech_stack = [tech_stack]

    if tech_stack:
        print("  • " + ", ".join(tech_stack))
    else:
        print("  (None detected)")
    print()

    if not generate_pdf:
        return {"status": "ok", "mode": "external", "pdf_generated": False}
    if custom_output_dir is None or not os.path.exists(custom_output_dir):
        return {
            "status": "error",
            "detail": "custom_output_dir is required and must exist for PDF generation.",
        }

    SimpleResumeGenerator(
        str(custom_output_dir),
        data=docker,
        fileName=output_name,
    ).display_and_run(portfolio_only=True)
    return {
        "status": "ok",
        "mode": "external",
        "pdf_generated": True,
        "pdf_path": str(Path(custom_output_dir) / f"{output_name}.pdf"),
    }
