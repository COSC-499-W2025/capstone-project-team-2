import json
from pathlib import Path

# Render saved analyses as portfolio-style output, honoring consent settings.
from src.core.app_context import AppContext
from src.reporting.Generate_AI_Resume import GenerateProjectResume, ResumeItem
from src.aggregation.oop_aggregator import pretty_print_oop_report
from src.reporting.resume_pdf_generator import SimpleResumeGenerator
from src.reporting.portfolio_rendercv_service import PortfolioRenderCVService
from src.reporting.portfolio_service import (
    load_portfolio_showcase,
    build_portfolio_showcase,
    display_portfolio_showcase,
)
import os
import shutil

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

        project_name = analysis.get("resume_item", {}).get("project_name", "Portfolio")

        # Rebuild PortfolioShowcase object 
        portfolio_yaml = load_portfolio_showcase(project_name)
        ps = build_portfolio_showcase(analysis, portfolio_yaml)

        display_portfolio_showcase(ps)
        
        # PDF Prompt
        print("=" * 50)
        while True:
            generate_pdf_input = input("Would you like to generate a PDF? (y/N): ").strip().upper()
            
            if generate_pdf_input in {"Y", "N", ""}:
                break
            print("[WARN] Please enter only 'y' or 'n'.")
        
        if generate_pdf_input != "Y":
            return # Early exit if no PDF generation requested
        
        name_of_file = (
            input("Enter the name of the PDF file or press enter to use default name (Portfolio): ").strip()or "Portfolio")
            
        # Collect folder path only for fallback (RenderCV uses its own output directory)
        folder_path = None
        try:
            print("[INFO] Generating portfolio PDF using RenderCV...")

            service = PortfolioRenderCVService(name=name_of_file)
            service.add_portfolio(ps)
            status, pdf_path = service.render_portfolio_pdf()

            print(f"[INFO] RenderCV status: {status}")
            if pdf_path:
                print(f"[INFO] Portfolio PDF generated at: {pdf_path}")
                save_custom = input("Save PDF to a custom location? (y/N): ").strip().upper()
                if save_custom == "Y":
                    attempts = 0
                    max_attempts = 3                        
                    while attempts < max_attempts:
                        custom_folder = input("Enter the folder path to save the PDF: ").strip()
                        if os.path.exists(custom_folder):
                            custom_path = Path(custom_folder) / pdf_path.name
                            shutil.copy2(pdf_path, custom_path)
                            print(f"[INFO] PDF saved to: {custom_path}")
                            break
                        else:
                            print(f"[ERROR] Path not found: {custom_folder}")                                
                            attempts += 1
                    else:
                            print("[WARN] Maximum attempts reached. PDF remains at default location.")

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
            SimpleResumeGenerator(folder_path, data=legacy_data, fileName=name_of_file).display_and_run(portfolio_only=True)

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
    
    while True:
        generate_pdf_input = input("Would you like to generate a PDF? (y/N): ").strip().upper()
            
        if generate_pdf_input in {"Y", "N", ""}:
            break
        print("[WARN] Please enter only 'y' or 'n'.")
        
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
        
