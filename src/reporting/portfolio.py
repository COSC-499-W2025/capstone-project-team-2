import json
from pathlib import Path

# Render saved analyses as portfolio-style output, honoring consent settings.
from src.core.app_context import AppContext
from src.reporting.Generate_AI_Resume import GenerateProjectResume
from src.aggregation.oop_aggregator import pretty_print_oop_report
from src.reporting.resume_pdf_generator import SimpleResumeGenerator
from src.reporting.portfolio_rendercv_service import PortfolioRenderCVService
from src.reporting.portfolio_service import (
    load_portfolio_showcase,
    build_portfolio_showcase,
    display_portfolio_showcase,
    PortfolioData,
)
import os

def display_portfolio_and_generate_pdf(path: Path, ctx: AppContext) -> None:
    """
    Read a saved project JSON file and print a formatted portfolio summary.
    Optionally generate a PDF using RenderCV or legacy PDF generator.

    Args:
        path (Path): Saved analysis file.
        ctx (AppContext): Shared context for consent/config paths.

    Returns:
        None
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {path.name}: {e}")
        return

    has_external = ctx.external_consent

    if not has_external:
        analysis = data if isinstance(data, dict) else {}
        if "analysis" in analysis and isinstance(analysis["analysis"], dict):
            analysis = analysis["analysis"]

        if "portfolio_showcase" in analysis:
            project_name = analysis.get("resume_item", {}).get("project_name", "Portfolio")

            # Rebuild PortfolioShowcase object 
            portfolio_yaml = load_portfolio_showcase(project_name)
            ps = build_portfolio_showcase(analysis, portfolio_yaml)

            display_portfolio_showcase(ps)
            
            # PDF Prompt
            print("=" * 50)
            generate_pdf_input = input("Would you like to generate a PDF? (y/n): ").strip().upper()
            
            if generate_pdf_input == "Y":
                name_of_file = (
                    input("Enter the name of the PDF file or press enter to use default name (Portfolio): ").strip()or "Portfolio")
                
                # Collect folder path only for fallback (RenderCV uses its own output directory)
                folder_path = None
                try:
                    print("[INFO] Generating portfolio PDF using RenderCV...")
                    print("[INFO] RenderCV uses its own output directory.")

                    service = PortfolioRenderCVService(name=name_of_file)
                    service.add_portfolio(ps)
                    status, pdf_path = service.render_portfolio_pdf()

                    print(f"[INFO] RenderCV status: {status}")
                    if pdf_path:
                        print(f"[INFO] Portfolio PDF generated at: {pdf_path}")

                except Exception as e:
                    print(f"[WARN] RenderCV export failed, falling back to legacy PDF: {e}")
                    
                    # Collect folder path for fallback PDF generator
                    if folder_path is None:
                        attempts = 0
                        max_attempts = 3
                        while attempts < max_attempts:
                            folder_path = input("Enter the folder path where you want to save the PDF: ").strip()
                            if os.path.exists(folder_path):
                                break
                            attempts += 1
                        else:
                            print("Maximum attempts reached. Cannot generate fallback PDF.")
                            return
                    
                    portfolio_data = PortfolioData(ps, analysis)
                    SimpleResumeGenerator(folder_path, data=portfolio_data, fileName=name_of_file).display_and_run(portfolio_only=True)

            return

        # Fallback to old format 
        print("\n=== PROJECT SUMMARY (External tools disabled) ===")

        pt = (analysis.get("resume_item", {}).get("project_type") or analysis.get("project_type", {}).get("project_type", "—"))
        mode = (analysis.get("resume_item", {}).get("detection_mode") or analysis.get("project_type", {}).get("mode", "—"))

        stack = analysis.get("resume_item", {}) or {}
        langs = stack.get("languages") or []
        frws = stack.get("frameworks") or []
        skills = stack.get("skills") or []
        duration = analysis.get("duration_estimate", "—")
        summary = stack.get("summary", "—")

        print("\n===============================")
        print(f" PROJECT: {path.name}")
        print("===============================")

        if summary and summary != "—":
            print(f"Summary: {summary}")
        print(f"Duration     : {duration}")
        print(f"Languages    : {', '.join(langs) or '—'}")
        print(f"Frameworks   : {', '.join(frws) or '—'}")
        print(f"Skills       : {', '.join(skills) or '—'}")
        print()

        oop_analysis = analysis.get("oop_analysis")
        if oop_analysis and isinstance(oop_analysis, dict):
            pretty_print_oop_report(oop_analysis)
        return
    
    try:
        directory_file_path = data.get("project_root")
        docker = GenerateProjectResume(directory_file_path).generate(
            saveToJson=False
        )
    except Exception as e:
        print(f"[ERROR] Could not generate portfolio: {e}")
        return

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
    
    generate_pdf_input = input("Would you like to generate a PDF? (y/n): ").strip().upper()
    if generate_pdf_input == "Y":
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            folder_path = input("Enter the folder path where you want to save the PDF: ").strip()
            if os.path.exists(folder_path):
                break
            attempts += 1
        else:
            print("Maximum attempts reached. Returning to menu.")
            return

        name_of_file = (
            input("Enter the name of the PDF file or press enter to use default name (Portfolio): ").strip() or "Portfolio")

        SimpleResumeGenerator(folder_path, data=docker, fileName=name_of_file).display_and_run(portfolio_only=True)
