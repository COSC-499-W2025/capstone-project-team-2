"""
Document Generator Menu Module

Provides a unified interface for creating and editing resumes and portfolios
using the RenderCV system. This module handles all document generation flows
including creating new documents, loading existing ones, and editing content.

Similar to portfolio.py, this module serves as the CLI interface layer that
delegates to the underlying RenderCVDocument service.
"""

import json
import os
from pathlib import Path
from typing import Optional

from src.core.app_context import AppContext
from src.reporting.Generate_AI_Resume import GenerateProjectResume, GenerateLocalResume
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument, Project, Experience, Education, Skills, Connections
)
from src.storage.saved_projects import list_saved_projects


def document_generator_menu(ctx: AppContext) -> None:
    """
    Unified menu for creating and editing resumes and portfolios using RenderCV.

    Allows users to:
    - Create new resume or portfolio documents
    - Load existing documents
    - Add projects from saved analyses (local or AI-powered)
    - Edit contact information and sections
    - Render to PDF

    Args:
        ctx (AppContext): Shared DB/store context.

    Returns:
        None
    """
    while True:
        print("\n=== Document Generator (Resume & Portfolio) ===")
        print("1) Create new Resume")
        print("2) Create new Portfolio")
        print("3) Load existing document")
        print("0) Back to main menu")

        choice = input("Select an option: ").strip()

        if choice == "0":
            return
        elif choice == "1":
            name = input("Enter your name: ").strip()
            if not name:
                print("[ERROR] Name cannot be empty.")
                continue
            doc = RenderCVDocument(doc_type='resume', auto_save=True)
            result = doc.generate(name=name)
            if result == "Skipping generation":
                print(f"[INFO] Resume for '{name}' already exists. Loading...")
            else:
                print(f"[SUCCESS] Resume created for '{name}'")
            doc.load(name=name)
            _document_edit_menu(ctx, doc)
        elif choice == "2":
            name = input("Enter your name: ").strip()
            if not name:
                print("[ERROR] Name cannot be empty.")
                continue
            doc = RenderCVDocument(doc_type='portfolio', auto_save=True)
            result = doc.generate(name=name)
            if result == "Skipping generation":
                print(f"[INFO] Portfolio for '{name}' already exists. Loading...")
            else:
                print(f"[SUCCESS] Portfolio created for '{name}'")
            doc.load(name=name)
            _document_edit_menu(ctx, doc)
        elif choice == "3":
            _load_existing_document_menu(ctx)
        else:
            print("Please choose a valid option (0-3).")


def _load_existing_document_menu(ctx: AppContext) -> None:
    """Load an existing resume or portfolio document."""
    print("\n=== Load Existing Document ===")
    print("1) Load Resume")
    print("2) Load Portfolio")
    print("0) Back")

    choice = input("Select document type: ").strip()

    if choice == "0":
        return

    doc_type = 'resume' if choice == "1" else 'portfolio' if choice == "2" else None
    if not doc_type:
        print("[ERROR] Invalid choice.")
        return

    # Get the directory where documents are stored
    doc = RenderCVDocument(doc_type=doc_type, auto_save=True)
    cv_files_dir = doc.cv_files_dir

    # Find existing documents of the selected type
    suffix = "Resume_CV.yaml" if doc_type == 'resume' else "Portfolio_CV.yaml"
    existing_files = list(cv_files_dir.glob(f"*_{suffix}"))

    if not existing_files:
        print(f"\n[INFO] No saved {doc_type}s found.")
        return

    # Extract names from filenames and display list
    print(f"\nExisting {doc_type}s:")
    names = []
    for i, file_path in enumerate(existing_files, start=1):
        # Extract name from filename (e.g., "John_Doe_Resume_CV.yaml" -> "John_Doe")
        name = file_path.stem.replace(f"_{suffix.replace('.yaml', '')}", "")
        names.append(name)
        display_name = name.replace("_", " ")
        print(f"  {i}) {display_name}")

    print("  0) Back")

    sel = input("\nSelect a document to load: ").strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(names):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    selected_name = names[idx]

    try:
        doc.load(name=selected_name)
        print(f"[SUCCESS] Loaded {doc_type} for '{selected_name.replace('_', ' ')}'")
        _document_edit_menu(ctx, doc)
    except FileNotFoundError:
        print(f"[ERROR] No {doc_type} found for '{selected_name}'.")
    except Exception as e:
        print(f"[ERROR] Could not load document: {e}")


def _document_edit_menu(ctx: AppContext, doc: RenderCVDocument) -> None:
    """
    Edit menu for a loaded RenderCV document.

    Args:
        ctx: Application context
        doc: The RenderCVDocument instance to edit
    """
    doc_type_label = "Resume" if doc.doc_type == 'resume' else "Portfolio"

    while True:
        print(f"\n=== Editing {doc_type_label}: {doc.name.replace('_', ' ')} ===")
        print("1) Add project from saved analysis")
        print("2) Add project from AI analysis")
        print("3) Edit contact information")
        if doc.doc_type == 'resume':
            print("4) Add experience")
            print("5) Add education")
            print("6) Add skills")
            print("7) Update summary")
        print("8) View current document")
        print("9) Render to PDF")
        print("0) Save and return")

        choice = input("Select an option: ").strip()

        if choice == "0":
            doc.save()
            print("[SUCCESS] Document saved.")
            return
        elif choice == "1":
            _add_project_from_analysis(ctx, doc)
        elif choice == "2":
            _add_project_from_ai(ctx, doc)
        elif choice == "3":
            _edit_contact_info(doc)
        elif choice == "4" and doc.doc_type == 'resume':
            _add_experience(doc)
        elif choice == "5" and doc.doc_type == 'resume':
            _add_education(doc)
        elif choice == "6" and doc.doc_type == 'resume':
            _add_skills(doc)
        elif choice == "7" and doc.doc_type == 'resume':
            _update_summary(doc)
        elif choice == "8":
            _view_document(doc)
        elif choice == "9":
            _render_document(doc)
        else:
            max_opt = "9" if doc.doc_type == 'resume' else "9"
            print(f"Please choose a valid option (0-{max_opt}).")


def _add_project_from_analysis(ctx: AppContext, doc: RenderCVDocument) -> None:
    """Add a project from saved local analysis."""
    folder = Path(ctx.default_save_dir).resolve()
    items = list_saved_projects(folder)

    if not items:
        print("[INFO] No saved projects found.")
        return

    print("\nSaved analyses:")
    for i, p in enumerate(items, start=1):
        print(f"  {i}) {p.name}")

    sel = input("\nSelect a project (or 0 to cancel): ").strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(items):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    chosen_path = items[idx]
    try:
        data = json.loads(chosen_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {chosen_path.name}: {e}")
        return

    # Generate resume item from local analysis
    project_name = chosen_path.stem
    try:
        resume_item = GenerateLocalResume(data, project_name).generate()

        summary = resume_item.one_sentence_summary
        if resume_item.tech_stack:
            summary = f"{summary} Tech stack: {resume_item.tech_stack}"

        project = Project(
            name=resume_item.project_title,
            summary=summary,
            highlights=resume_item.key_responsibilities or []
        )

        result = doc.add_project(project)
        print(f"[SUCCESS] {result}")
    except Exception as e:
        print(f"[ERROR] Could not add project: {e}")


def _add_project_from_ai(ctx: AppContext, doc: RenderCVDocument) -> None:
    """Add a project using AI analysis (requires external consent)."""
    if not ctx.external_consent:
        print("\n[INFO] External services are disabled in your consent settings.")
        print("Enable external services in Settings to use AI analysis.\n")
        return

    folder = Path(ctx.default_save_dir).resolve()
    items = list_saved_projects(folder)

    if not items:
        print("[INFO] No saved projects found.")
        return

    print("\nSaved analyses:")
    for i, p in enumerate(items, start=1):
        print(f"  {i}) {p.name}")

    sel = input("\nSelect a project for AI analysis (or 0 to cancel): ").strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(items):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    chosen_path = items[idx]
    try:
        data = json.loads(chosen_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Could not read {chosen_path.name}: {e}")
        return

    project_root = data.get("project_root")
    if not project_root:
        print("[ERROR] Saved analysis does not contain 'project_root'.")
        return

    print("[INFO] Generating AI analysis... (this may take a moment)")
    try:
        ai_resume = GenerateProjectResume(project_root).generate(saveToJson=False)

        summary = ai_resume.one_sentence_summary
        if ai_resume.tech_stack:
            summary = f"{summary} Tech stack: {ai_resume.tech_stack}"

        project = Project(
            name=ai_resume.project_title,
            summary=summary,
            highlights=ai_resume.key_responsibilities or []
        )

        result = doc.add_project(project)
        print(f"[SUCCESS] {result}")
    except Exception as e:
        print(f"[ERROR] Could not generate AI analysis: {e}")


def _edit_contact_info(doc: RenderCVDocument) -> None:
    """Edit contact information in the document."""
    print("\n=== Edit Contact Information ===")
    print("(Press Enter to keep current value)\n")

    cv_data = doc.data.get('cv', {})

    name = input(f"Name [{cv_data.get('name', '')}]: ").strip()
    email = input(f"Email [{cv_data.get('email', '')}]: ").strip()
    phone = input(f"Phone [{cv_data.get('phone', '')}]: ").strip()
    location = input(f"Location [{cv_data.get('location', '')}]: ").strip()
    website = input(f"Website [{cv_data.get('website', '')}]: ").strip()

    doc.update_contact(
        name=name if name else None,
        email=email if email else None,
        phone=phone if phone else None,
        location=location if location else None,
        website=website if website else None
    )
    print("[SUCCESS] Contact information updated.")


def _add_experience(doc: RenderCVDocument) -> None:
    """Add work experience to a resume."""
    print("\n=== Add Work Experience ===")

    company = input("Company name: ").strip()
    if not company:
        print("[ERROR] Company name is required.")
        return

    position = input("Position/Title: ").strip()
    start_date = input("Start date (YYYY-MM): ").strip()
    end_date = input("End date (YYYY-MM or 'present'): ").strip()
    location = input("Location: ").strip()

    print("Enter highlights (one per line, empty line to finish):")
    highlights = []
    while True:
        h = input("  - ").strip()
        if not h:
            break
        highlights.append(h)

    exp = Experience(
        company=company,
        position=position if position else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        location=location if location else None,
        highlights=highlights if highlights else None
    )

    result = doc.add_experience(exp)
    print(f"[SUCCESS] {result}")


def _add_education(doc: RenderCVDocument) -> None:
    """Add education entry to a resume."""
    print("\n=== Add Education ===")

    institution = input("Institution name: ").strip()
    if not institution:
        print("[ERROR] Institution name is required.")
        return

    area = input("Field of study/Major: ").strip()
    if not area:
        print("[ERROR] Field of study is required.")
        return

    degree = input("Degree (e.g., BS, MS, PhD): ").strip()
    start_date = input("Start date (YYYY-MM): ").strip()
    end_date = input("End date (YYYY-MM): ").strip()
    location = input("Location: ").strip()
    gpa = input("GPA (optional): ").strip()

    print("Enter highlights (one per line, empty line to finish):")
    highlights = []
    while True:
        h = input("  - ").strip()
        if not h:
            break
        highlights.append(h)

    edu = Education(
        institution=institution,
        area=area,
        degree=degree if degree else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        location=location if location else None,
        gpa=gpa if gpa else None,
        highlights=highlights if highlights else None
    )

    result = doc.add_education(edu)
    print(f"[SUCCESS] {result}")


def _add_skills(doc: RenderCVDocument) -> None:
    """Add a skill category to a resume."""
    print("\n=== Add Skills ===")

    label = input("Skill category (e.g., Languages, Frameworks, Tools): ").strip()
    if not label:
        print("[ERROR] Skill category is required.")
        return

    details = input("Skills (comma-separated, e.g., Python, JavaScript, Go): ").strip()
    if not details:
        print("[ERROR] Skills list is required.")
        return

    skill = Skills(label=label, details=details)
    result = doc.add_skills(skill)
    print(f"[SUCCESS] {result}")


def _update_summary(doc: RenderCVDocument) -> None:
    """Update the professional summary in a resume."""
    print("\n=== Update Professional Summary ===")

    current = doc.sections.get('summary', [''])[0] if doc.sections.get('summary') else ''
    print(f"Current summary: {current[:100]}..." if len(current) > 100 else f"Current summary: {current}")

    print("\nEnter new summary (or press Enter to keep current):")
    new_summary = input("> ").strip()

    if new_summary:
        result = doc.update_summary(new_summary)
        print(f"[SUCCESS] {result}")
    else:
        print("[INFO] Summary unchanged.")


def _view_document(doc: RenderCVDocument) -> None:
    """Display current document contents."""
    doc_type_label = "Resume" if doc.doc_type == 'resume' else "Portfolio"

    print(f"\n{'=' * 60}")
    print(f"  {doc_type_label.upper()}: {doc.name.replace('_', ' ')}")
    print(f"{'=' * 60}")

    cv = doc.data.get('cv', {})

    # Contact info
    print(f"\nContact:")
    print(f"  Email: {cv.get('email', 'N/A')}")
    print(f"  Phone: {cv.get('phone', 'N/A')}")
    print(f"  Location: {cv.get('location', 'N/A')}")
    print(f"  Website: {cv.get('website', 'N/A')}")

    # Social networks
    if cv.get('social_networks'):
        print(f"\nSocial Networks:")
        for sn in cv['social_networks']:
            if sn.get('username'):
                print(f"  {sn.get('network')}: {sn.get('username')}")

    # Sections
    sections = cv.get('sections', {})

    if doc.doc_type == 'resume' and sections.get('summary'):
        print(f"\nSummary:")
        for s in sections['summary']:
            print(f"  {s}")

    if sections.get('projects'):
        print(f"\nProjects ({len(sections['projects'])}):")
        for p in sections['projects']:
            print(f"  - {p.get('name')}: {p.get('summary', '')[:60]}...")

    if doc.doc_type == 'resume':
        if sections.get('experience'):
            print(f"\nExperience ({len(sections['experience'])}):")
            for e in sections['experience']:
                print(f"  - {e.get('position', 'N/A')} at {e.get('company')}")

        if sections.get('education'):
            print(f"\nEducation ({len(sections['education'])}):")
            for e in sections['education']:
                print(f"  - {e.get('degree', '')} {e.get('area', '')} at {e.get('institution')}")

        if sections.get('skills'):
            print(f"\nSkills:")
            for s in sections['skills']:
                print(f"  {s.get('label')}: {s.get('details')}")

    print(f"\n{'=' * 60}")
    input("Press Enter to continue...")


def _render_document(doc: RenderCVDocument) -> None:
    """Render the document to PDF."""
    import shutil

    print("\n[INFO] Rendering document to PDF...")

    try:
        status, pdf_path = doc.render()
        print(f"[INFO] Render status: {status}")

        if pdf_path:
            print(f"[SUCCESS] PDF generated at: {pdf_path}")

            save_custom = input("Save PDF to a custom location? (y/n): ").strip().lower()
            if save_custom == "y":
                attempts = 0
                max_attempts = 3
                while attempts < max_attempts:
                    custom_folder = input("Enter the folder path: ").strip()
                    if os.path.exists(custom_folder):
                        custom_path = Path(custom_folder) / pdf_path.name
                        shutil.copy2(pdf_path, custom_path)
                        print(f"[SUCCESS] PDF saved to: {custom_path}")
                        break
                    else:
                        attempts += 1
                        print(f"[ERROR] Path not found. ({attempts}/{max_attempts})")
                else:
                    print("[WARN] Max attempts reached. PDF remains at default location.")
        else:
            print(f"[ERROR] {status}")
    except Exception as e:
        print(f"[ERROR] Could not render PDF: {e}")
