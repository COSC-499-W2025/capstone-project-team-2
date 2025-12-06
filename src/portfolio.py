import json
from pathlib import Path

# Render saved analyses as portfolio-style output, honoring consent settings.
from src import app_context
from src.app_context import AppContext
from src.Generate_AI_Resume import GenerateProjectResume, GenerateLocalResume
from src.resume_pdf_generator import SimpleResumeGenerator
import os
from src.oop_aggregator import pretty_print_oop_report


def display_portfolio_and_generate_pdf(path: Path, ctx: AppContext) -> None:
    """
    Read a saved project JSON file and print a formatted portfolio summary.

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
        print("\n=== PROJECT SUMMARY (External tools disabled) ===")

        analysis = data if isinstance(data, dict) else {}
        if "analysis" in analysis and isinstance(analysis["analysis"], dict):
            analysis = analysis["analysis"]

        pt = (
            analysis.get("resume_item", {}).get("project_type")
            or analysis.get("project_type", {}).get("project_type", "—")
        )
        mode = (
            analysis.get("resume_item", {}).get("detection_mode")
            or analysis.get("project_type", {}).get("mode", "—")
        )
        stack = analysis.get("resume_item", {}) or {}
        langs = stack.get("languages") or analysis.get("stack", {}).get("languages", [])
        frws = stack.get("frameworks") or analysis.get("stack", {}).get("frameworks", [])
        skills = stack.get("skills") or analysis.get("skills", [])
        duration = analysis.get("duration_estimate", "—")
        summary = (analysis.get("resume_item", {}) or {}).get("summary", "—")

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
        docker = GenerateProjectResume(directory_file_path).generate(saveToJson=False)
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

    print("=== OOP Principles Detected ===\n")
    oop_data = docker.oop_principles_detected

    if not oop_data or not isinstance(oop_data, dict):
        print("No OOP data detected.\n")
        return
    else:
        print(oop_data.keys())

    for name, principle in docker.oop_principles_detected.items():
        print(f"=== {name.upper()} ===")
        print("present:", principle.present)
        print("description:", principle.description)
        if not principle.code_snippets:
            print("No code samples.\n")
        else:
            for snippet in principle.code_snippets:
                file = snippet.get("file", "(unknown file)")
                code = snippet.get("code", "")
                print(f"File: {file}")
                print(f"Code:\n{code[:200]}...\n")

    print("============================================\n")
    generate_pdf_input=input("Would you like to generate a PDF? (y/n): ")
    if generate_pdf_input.upper()=="Y":
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            folder_path=str(input("Enter the folder path where you want to save the PDF: "))
            if os.path.exists(folder_path):
                break
            else:
                attempts += 1
                if attempts < max_attempts:
                    print(f"Folder does not exist. Please enter a valid folder path. ({attempts}/{max_attempts} attempts)")
                else:
                    print("Maximum attempts reached. Returning to menu.")
                    return
        name_of_file=str(input("Enter the name of the PDF file or press enter to use default name (Portfolio): ")) or "Portfolio"
        SimpleResumeGenerator(folder_path,data=docker,fileName=name_of_file).display_and_run()








