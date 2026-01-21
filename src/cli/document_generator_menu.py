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
import time
from pathlib import Path
from typing import Optional

from tqdm import tqdm

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
    """
    Load an existing resume or portfolio document from saved files.

    Displays a menu for selecting document type (resume/portfolio), then lists
    all existing documents of that type and allows the user to select one to load.

    Args:
        ctx: Application context containing database and storage configuration

    Returns:
        None: Returns early if user cancels or no documents are found
    """
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
    Display and handle the edit menu for a loaded RenderCV document.

    Presents different menu options based on document type (resume vs portfolio).
    Resume documents have additional sections for experience, education, skills,
    and summary that are not available for portfolios.

    Args:
        ctx: Application context containing database and storage configuration
        doc: The RenderCVDocument instance to edit

    Returns:
        None: Saves document and returns when user selects exit option
    """
    doc_type_label = "Resume" if doc.doc_type == 'resume' else "Portfolio"

    while True:
        print(f"\n{'=' * 50}")
        print(f"  Editing {doc_type_label}: {doc.name.replace('_', ' ')}")
        print(f"{'=' * 50}")

        print("\n-- Projects --")
        print("  1) Add from saved analysis")
        print("  2) Add from AI analysis")
        print("  3) Add manually")
        print("  4) Modify/Delete")

        print("\n-- Contact & Social --")
        print("  5) Edit contact information")
        print("  6) Add social network")
        print("  7) Modify/Delete social networks")

        if doc.doc_type == 'resume':
            print("\n-- Experience --")
            print("  8) Add experience")
            print("  9) Modify/Delete experience")

            print("\n-- Education --")
            print("  10) Add education")
            print("  11) Modify/Delete education")

            print("\n-- Skills --")
            print("  12) Add skills")
            print("  13) Modify/Delete skills")

            print("\n-- Summary --")
            print("  14) Update summary")

            print("\n-- Document --")
            print("  15) Change theme")
            print("  16) View full document")
            print("  17) Render to PDF")
        else:
            # Portfolio uses sequential numbering
            print("\n-- Document --")
            print("  8) Change theme")
            print("  9) View full document")
            print("  10) Render to PDF")

        print(f"\n{'─' * 50}")
        print("  0) Save and return")

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
            _add_project_manually(doc)
        elif choice == "4":
            _modify_delete_projects(doc)
        elif choice == "5":
            _edit_contact_info(doc)
        elif choice == "6":
            _add_connection(doc)
        elif choice == "7":
            _modify_delete_connections(doc)
        elif choice == "8":
            if doc.doc_type == 'resume':
                _add_experience(doc)
            else:
                _change_theme(doc)
        elif choice == "9":
            if doc.doc_type == 'resume':
                _modify_delete_experience(doc)
            else:
                _view_document(doc)
        elif choice == "10":
            if doc.doc_type == 'resume':
                _add_education(doc)
            else:
                _render_document(doc)
        elif choice == "11" and doc.doc_type == 'resume':
            _modify_delete_education(doc)
        elif choice == "12" and doc.doc_type == 'resume':
            _add_skills(doc)
        elif choice == "13" and doc.doc_type == 'resume':
            _modify_delete_skills(doc)
        elif choice == "14" and doc.doc_type == 'resume':
            _update_summary(doc)
        elif choice == "15" and doc.doc_type == 'resume':
            _change_theme(doc)
        elif choice == "16" and doc.doc_type == 'resume':
            _view_document(doc)
        elif choice == "17" and doc.doc_type == 'resume':
            _render_document(doc)
        else:
            max_opt = "17" if doc.doc_type == 'resume' else "10"
            print(f"Please choose a valid option (0-{max_opt}).")


def _add_project_from_analysis(ctx: AppContext, doc: RenderCVDocument) -> None:
    """
    Add a project to the document from a saved local analysis.

    Lists all saved project analyses from the default save directory and allows
    the user to select one. The selected analysis is converted to a resume item
    using GenerateLocalResume and added to the document.

    Args:
        ctx: Application context containing the default save directory path
        doc: The RenderCVDocument instance to add the project to

    Returns:
        None: Prints success/error message and returns
    """
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
    """
    Add a project to the document using AI-powered analysis.

    Requires external consent to be enabled. Lists saved project analyses and
    uses GenerateProjectResume to create an AI-generated resume item from the
    project root path stored in the analysis.

    Args:
        ctx: Application context containing external consent flag and save directory
        doc: The RenderCVDocument instance to add the project to

    Returns:
        None: Prints success/error message and returns
    """
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


def _add_project_manually(doc: RenderCVDocument) -> None:
    """
    Manually add a project to the document through user input.

    Prompts the user to enter project details including name, dates, summary,
    and highlights. Creates a Project object and adds it to the document.

    Args:
        doc: The RenderCVDocument instance to add the project to

    Returns:
        None: Prints success/error message and returns
    """
    print("\n=== Add Project Manually ===")

    name = input("Project name: ").strip()
    if not name:
        print("[ERROR] Project name is required.")
        return

    start_date = input("Start date (YYYY-MM, optional): ").strip()
    end_date = input("End date (YYYY-MM, optional): ").strip()

    print("\nEnter a brief summary of the project:")
    summary = input("> ").strip()

    print("\nEnter highlights/key features (one per line, empty line to finish):")
    highlights = []
    while True:
        h = input("  - ").strip()
        if not h:
            break
        highlights.append(h)

    project = Project(
        name=name,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        summary=summary if summary else None,
        highlights=highlights if highlights else None
    )

    result = doc.add_project(project)
    print(f"[SUCCESS] {result}")


def _edit_contact_info(doc: RenderCVDocument) -> None:
    """
    Edit contact information in the document.

    Prompts the user to update name, email, phone, location, and website.
    Empty input preserves the existing value for each field.

    Args:
        doc: The RenderCVDocument instance to update

    Returns:
        None: Prints success message after updating contact information
    """
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


def _add_connection(doc: RenderCVDocument) -> None:
    """
    Add a social network connection to the document.

    Prompts the user for a network name and username, then creates a
    Connections object and adds it to the document.

    Args:
        doc: The RenderCVDocument instance to add the connection to

    Returns:
        None: Prints success/error message and returns
    """
    print("\n=== Add Social Network Connection ===")
    print("Common networks: LinkedIn, GitHub, GitLab, Twitter, Instagram, YouTube\n")

    network = input("Network name (e.g., LinkedIn, GitHub): ").strip()
    if not network:
        print("[ERROR] Network name is required.")
        return

    username = input("Username/Handle: ").strip()
    if not username:
        print("[ERROR] Username is required.")
        return

    connection = Connections(network=network, username=username)
    result = doc.add_connection(connection)
    print(f"[SUCCESS] {result}")


def _modify_delete_connections(doc: RenderCVDocument) -> None:
    """
    Display menu to modify or delete social network connections from the document.

    Lists all social network connections and allows the user to select one for
    modification or deletion. Runs in a loop until user selects back option.

    Args:
        doc: The RenderCVDocument instance containing the connections

    Returns:
        None: Returns when user selects back option or no connections exist
    """
    cv_data = doc.data.get('cv', {})
    connections = cv_data.get('social_networks', [])

    if not connections:
        print("\n[INFO] No social network connections to modify or delete.")
        return

    while True:
        # Refresh connections list
        connections = doc.data.get('cv', {}).get('social_networks', [])

        if not connections:
            print("\n[INFO] No more connections.")
            return

        print("\n=== Modify/Delete Social Networks ===")
        for i, conn in enumerate(connections, start=1):
            network = conn.get('network', 'Unknown')
            username = conn.get('username', 'N/A')
            print(f"  {i}) {network}: {username}")
        print("  0) Back")

        sel = input("\nSelect a connection: ").strip()
        if not sel or sel == "0":
            return

        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(connections):
                print("[ERROR] Invalid selection.")
                continue
        except ValueError:
            print("[ERROR] Please enter a number.")
            continue

        conn = connections[idx]
        print(f"\nSelected: {conn.get('network', 'Unknown')}: {conn.get('username', 'N/A')}")
        print("1) Modify")
        print("2) Delete")
        print("0) Cancel")

        action = input("Select action: ").strip()

        if action == "1":
            _modify_connection_entry(doc, idx, conn)
        elif action == "2":
            confirm = input(f"Delete '{conn.get('network')}' connection? (y/n): ").strip().lower()
            if confirm == 'y':
                connections.pop(idx)
                doc.save()
                print("[SUCCESS] Connection deleted.")
        elif action == "0":
            continue


def _modify_connection_entry(doc: RenderCVDocument, idx: int, conn: dict) -> None:
    """
    Modify a single social network connection entry.

    Prompts the user to update the network name and username.
    Empty input preserves existing values.

    Args:
        doc: The RenderCVDocument instance containing the connection
        idx: Zero-based index of the connection in the social_networks list
        conn: Dictionary containing the current connection data

    Returns:
        None: Saves changes and prints success message
    """
    print("\n=== Modify Connection ===")
    print("(Press Enter to keep current value)\n")

    network = input(f"Network [{conn.get('network', '')}]: ").strip()
    username = input(f"Username [{conn.get('username', '')}]: ").strip()

    connections = doc.data.get('cv', {}).get('social_networks', [])

    if network:
        connections[idx]['network'] = network
    if username:
        connections[idx]['username'] = username

    doc.save()
    print("[SUCCESS] Connection updated.")


def _add_experience(doc: RenderCVDocument) -> None:
    """
    Add work experience entry to a resume document.

    Prompts the user for company, position, dates, location, and highlights.
    Creates an Experience object and adds it to the document.

    Args:
        doc: The RenderCVDocument instance to add the experience to

    Returns:
        None: Prints success/error message and returns
    """
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
    """
    Add education entry to a resume document.

    Prompts the user for institution, field of study, degree, dates,
    location, GPA, and highlights. Creates an Education object and
    adds it to the document.

    Args:
        doc: The RenderCVDocument instance to add the education to

    Returns:
        None: Prints success/error message and returns
    """
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
    """
    Add a skill category to a resume document.

    Prompts the user for a skill category label and comma-separated list
    of skills. Creates a Skills object and adds it to the document.

    Args:
        doc: The RenderCVDocument instance to add the skills to

    Returns:
        None: Prints success/error message and returns
    """
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


def _modify_delete_projects(doc: RenderCVDocument) -> None:
    """
    Display menu to modify or delete existing projects from the document.

    Lists all projects in the document and allows the user to select one for
    modification or deletion. Modifications are handled by _modify_project.

    Args:
        doc: The RenderCVDocument instance containing the projects

    Returns:
        None: Returns when user selects back option or no projects exist
    """
    sections = doc.data.get('cv', {}).get('sections', {})
    projects = sections.get('projects', [])

    if not projects:
        print("\n[INFO] No projects to modify or delete.")
        return

    while True:
        print("\n=== Modify/Delete Projects ===")
        for i, p in enumerate(projects, start=1):
            print(f"  {i}) {p.get('name', 'Unnamed')}")
        print("  0) Back")

        sel = input("\nSelect a project: ").strip()
        if not sel or sel == "0":
            return

        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(projects):
                print("[ERROR] Invalid selection.")
                continue
        except ValueError:
            print("[ERROR] Please enter a number.")
            continue

        project = projects[idx]
        print(f"\nSelected: {project.get('name', 'Unnamed')}")
        print("1) Modify")
        print("2) Delete")
        print("0) Cancel")

        action = input("Select action: ").strip()

        if action == "1":
            _modify_project(doc, idx, project)
            projects = doc.data.get('cv', {}).get('sections', {}).get('projects', [])
        elif action == "2":
            confirm = input(f"Delete '{project.get('name')}'? (y/n): ").strip().lower()
            if confirm == 'y':
                projects.pop(idx)
                doc.save()
                print("[SUCCESS] Project deleted.")
        elif action == "0":
            continue


def _modify_project(doc: RenderCVDocument, idx: int, project: dict) -> None:
    """
    Modify a single project entry in the document.

    Prompts the user to update project name, summary, and highlights.
    Empty input preserves existing values.

    Args:
        doc: The RenderCVDocument instance containing the project
        idx: Zero-based index of the project in the projects list
        project: Dictionary containing the current project data

    Returns:
        None: Saves changes and prints success message
    """
    print("\n=== Modify Project ===")
    print("(Press Enter to keep current value)\n")

    name = input(f"Name [{project.get('name', '')}]: ").strip()
    summary = input(f"Summary [{project.get('summary', '')[:50]}...]: ").strip()

    print(f"\nCurrent highlights:")
    for h in project.get('highlights', []):
        print(f"  - {h}")

    edit_highlights = input("\nEdit highlights? (y/n): ").strip().lower()
    highlights = None
    if edit_highlights == 'y':
        print("Enter new highlights (one per line, empty line to finish):")
        highlights = []
        while True:
            h = input("  - ").strip()
            if not h:
                break
            highlights.append(h)

    sections = doc.data.get('cv', {}).get('sections', {})
    projects = sections.get('projects', [])

    if name:
        projects[idx]['name'] = name
    if summary:
        projects[idx]['summary'] = summary
    if highlights is not None:
        projects[idx]['highlights'] = highlights

    doc.save()
    print("[SUCCESS] Project updated.")


def _modify_delete_experience(doc: RenderCVDocument) -> None:
    """
    Display menu to modify or delete experience entries from the document.

    Lists all experience entries and allows the user to select one for
    modification or deletion. Runs in a loop until user selects back option.

    Args:
        doc: The RenderCVDocument instance containing the experience entries

    Returns:
        None: Returns when user selects back option or no entries exist
    """
    sections = doc.data.get('cv', {}).get('sections', {})
    experience = sections.get('experience', [])

    if not experience:
        print("\n[INFO] No experience entries to modify or delete.")
        return

    while True:
        print("\n=== Modify/Delete Experience ===")
        for i, e in enumerate(experience, start=1):
            print(f"  {i}) {e.get('position', 'N/A')} at {e.get('company', 'Unknown')}")
        print("  0) Back")

        sel = input("\nSelect an experience entry: ").strip()
        if not sel or sel == "0":
            return

        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(experience):
                print("[ERROR] Invalid selection.")
                continue
        except ValueError:
            print("[ERROR] Please enter a number.")
            continue

        exp = experience[idx]
        print(f"\nSelected: {exp.get('position', 'N/A')} at {exp.get('company', 'Unknown')}")
        print("1) Modify")
        print("2) Delete")
        print("0) Cancel")

        action = input("Select action: ").strip()

        if action == "1":
            _modify_experience(doc, idx, exp)
            experience = doc.data.get('cv', {}).get('sections', {}).get('experience', [])
        elif action == "2":
            confirm = input(f"Delete '{exp.get('position')} at {exp.get('company')}'? (y/n): ").strip().lower()
            if confirm == 'y':
                experience.pop(idx)
                doc.save()
                print("[SUCCESS] Experience entry deleted.")
        elif action == "0":
            continue


def _modify_experience(doc: RenderCVDocument, idx: int, exp: dict) -> None:
    """
    Modify a single experience entry in the document.

    Prompts the user to update company, position, dates, location, and highlights.
    Empty input preserves existing values.

    Args:
        doc: The RenderCVDocument instance containing the experience
        idx: Zero-based index of the experience in the experience list
        exp: Dictionary containing the current experience data

    Returns:
        None: Saves changes and prints success message
    """
    print("\n=== Modify Experience ===")
    print("(Press Enter to keep current value)\n")

    company = input(f"Company [{exp.get('company', '')}]: ").strip()
    position = input(f"Position [{exp.get('position', '')}]: ").strip()
    start_date = input(f"Start date [{exp.get('start_date', '')}]: ").strip()
    end_date = input(f"End date [{exp.get('end_date', '')}]: ").strip()
    location = input(f"Location [{exp.get('location', '')}]: ").strip()

    print(f"\nCurrent highlights:")
    for h in exp.get('highlights', []):
        print(f"  - {h}")

    edit_highlights = input("\nEdit highlights? (y/n): ").strip().lower()
    highlights = None
    if edit_highlights == 'y':
        print("Enter new highlights (one per line, empty line to finish):")
        highlights = []
        while True:
            h = input("  - ").strip()
            if not h:
                break
            highlights.append(h)

    sections = doc.data.get('cv', {}).get('sections', {})
    experience = sections.get('experience', [])

    if company:
        experience[idx]['company'] = company
    if position:
        experience[idx]['position'] = position
    if start_date:
        experience[idx]['start_date'] = start_date
    if end_date:
        experience[idx]['end_date'] = end_date
    if location:
        experience[idx]['location'] = location
    if highlights is not None:
        experience[idx]['highlights'] = highlights

    doc.save()
    print("[SUCCESS] Experience entry updated.")


def _modify_delete_education(doc: RenderCVDocument) -> None:
    """
    Display menu to modify or delete education entries from the document.

    Lists all education entries and allows the user to select one for
    modification or deletion. Runs in a loop until user selects back option.

    Args:
        doc: The RenderCVDocument instance containing the education entries

    Returns:
        None: Returns when user selects back option or no entries exist
    """
    sections = doc.data.get('cv', {}).get('sections', {})
    education = sections.get('education', [])

    if not education:
        print("\n[INFO] No education entries to modify or delete.")
        return

    while True:
        print("\n=== Modify/Delete Education ===")
        for i, e in enumerate(education, start=1):
            print(f"  {i}) {e.get('degree', '')} {e.get('area', '')} at {e.get('institution', 'Unknown')}")
        print("  0) Back")

        sel = input("\nSelect an education entry: ").strip()
        if not sel or sel == "0":
            return

        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(education):
                print("[ERROR] Invalid selection.")
                continue
        except ValueError:
            print("[ERROR] Please enter a number.")
            continue

        edu = education[idx]
        print(f"\nSelected: {edu.get('degree', '')} {edu.get('area', '')} at {edu.get('institution', 'Unknown')}")
        print("1) Modify")
        print("2) Delete")
        print("0) Cancel")

        action = input("Select action: ").strip()

        if action == "1":
            _modify_education_entry(doc, idx, edu)
            education = doc.data.get('cv', {}).get('sections', {}).get('education', [])
        elif action == "2":
            confirm = input(f"Delete '{edu.get('degree')} at {edu.get('institution')}'? (y/n): ").strip().lower()
            if confirm == 'y':
                education.pop(idx)
                doc.save()
                print("[SUCCESS] Education entry deleted.")
        elif action == "0":
            continue


def _modify_education_entry(doc: RenderCVDocument, idx: int, edu: dict) -> None:
    """
    Modify a single education entry in the document.

    Prompts the user to update institution, field of study, degree, dates,
    location, GPA, and highlights. Empty input preserves existing values.

    Args:
        doc: The RenderCVDocument instance containing the education entry
        idx: Zero-based index of the education in the education list
        edu: Dictionary containing the current education data

    Returns:
        None: Saves changes and prints success message
    """
    print("\n=== Modify Education ===")
    print("(Press Enter to keep current value)\n")

    institution = input(f"Institution [{edu.get('institution', '')}]: ").strip()
    area = input(f"Field of study [{edu.get('area', '')}]: ").strip()
    degree = input(f"Degree [{edu.get('degree', '')}]: ").strip()
    start_date = input(f"Start date [{edu.get('start_date', '')}]: ").strip()
    end_date = input(f"End date [{edu.get('end_date', '')}]: ").strip()
    location = input(f"Location [{edu.get('location', '')}]: ").strip()
    gpa = input(f"GPA [{edu.get('gpa', '')}]: ").strip()

    print(f"\nCurrent highlights:")
    for h in edu.get('highlights', []):
        print(f"  - {h}")

    edit_highlights = input("\nEdit highlights? (y/n): ").strip().lower()
    highlights = None
    if edit_highlights == 'y':
        print("Enter new highlights (one per line, empty line to finish):")
        highlights = []
        while True:
            h = input("  - ").strip()
            if not h:
                break
            highlights.append(h)

    sections = doc.data.get('cv', {}).get('sections', {})
    education = sections.get('education', [])

    if institution:
        education[idx]['institution'] = institution
    if area:
        education[idx]['area'] = area
    if degree:
        education[idx]['degree'] = degree
    if start_date:
        education[idx]['start_date'] = start_date
    if end_date:
        education[idx]['end_date'] = end_date
    if location:
        education[idx]['location'] = location
    if gpa:
        education[idx]['gpa'] = gpa
    if highlights is not None:
        education[idx]['highlights'] = highlights

    doc.save()
    print("[SUCCESS] Education entry updated.")


def _modify_delete_skills(doc: RenderCVDocument) -> None:
    """
    Display menu to modify or delete skill entries from the document.

    Lists all skill categories and allows the user to select one for
    modification or deletion. Runs in a loop until user selects back option.

    Args:
        doc: The RenderCVDocument instance containing the skill entries

    Returns:
        None: Returns when user selects back option or no entries exist
    """
    sections = doc.data.get('cv', {}).get('sections', {})
    skills = sections.get('skills', [])

    if not skills:
        print("\n[INFO] No skill entries to modify or delete.")
        return

    while True:
        print("\n=== Modify/Delete Skills ===")
        for i, s in enumerate(skills, start=1):
            print(f"  {i}) {s.get('label', 'Unknown')}: {s.get('details', '')[:40]}...")
        print("  0) Back")

        sel = input("\nSelect a skill entry: ").strip()
        if not sel or sel == "0":
            return

        try:
            idx = int(sel) - 1
            if idx < 0 or idx >= len(skills):
                print("[ERROR] Invalid selection.")
                continue
        except ValueError:
            print("[ERROR] Please enter a number.")
            continue

        skill = skills[idx]
        print(f"\nSelected: {skill.get('label', 'Unknown')}")
        print("1) Modify")
        print("2) Delete")
        print("0) Cancel")

        action = input("Select action: ").strip()

        if action == "1":
            _modify_skill_entry(doc, idx, skill)
            skills = doc.data.get('cv', {}).get('sections', {}).get('skills', [])
        elif action == "2":
            confirm = input(f"Delete skill category '{skill.get('label')}'? (y/n): ").strip().lower()
            if confirm == 'y':
                skills.pop(idx)
                doc.save()
                print("[SUCCESS] Skill entry deleted.")
        elif action == "0":
            continue


def _modify_skill_entry(doc: RenderCVDocument, idx: int, skill: dict) -> None:
    """
    Modify a single skill entry in the document.

    Prompts the user to update the skill category label and skills list.
    Empty input preserves existing values.

    Args:
        doc: The RenderCVDocument instance containing the skill entry
        idx: Zero-based index of the skill in the skills list
        skill: Dictionary containing the current skill data

    Returns:
        None: Saves changes and prints success message
    """
    print("\n=== Modify Skill ===")
    print("(Press Enter to keep current value)\n")

    label = input(f"Category [{skill.get('label', '')}]: ").strip()
    details = input(f"Skills [{skill.get('details', '')}]: ").strip()

    sections = doc.data.get('cv', {}).get('sections', {})
    skills = sections.get('skills', [])

    if label:
        skills[idx]['label'] = label
    if details:
        skills[idx]['details'] = details

    doc.save()
    print("[SUCCESS] Skill entry updated.")


def _update_summary(doc: RenderCVDocument) -> None:
    """
    Update the professional summary section in a resume document.

    Displays the current summary and prompts the user to enter a new one.
    Empty input leaves the summary unchanged.

    Args:
        doc: The RenderCVDocument instance to update

    Returns:
        None: Prints success/info message and returns
    """
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
    """
    Display the current document contents in a formatted view.

    Shows contact information, social networks, and all sections including
    projects, experience, education, and skills (for resumes).

    Args:
        doc: The RenderCVDocument instance to display

    Returns:
        None: Waits for user to press Enter before returning
    """
    doc_type_label = "Resume" if doc.doc_type == 'resume' else "Portfolio"

    print(f"\n{'=' * 60}")
    print(f"  {doc_type_label.upper()}: {doc.name.replace('_', ' ')}")
    print(f"{'=' * 60}")

    cv = doc.data.get('cv', {})

    # Contact info
    print(f"\nContact:")
    print(f"  Name: {cv.get('name', 'N/A')}")
    print(f"  Email: {cv.get('email', 'N/A')}")
    print(f"  Phone: {cv.get('phone', 'N/A')}")
    print(f"  Location: {cv.get('location', 'N/A')}")
    print(f"  Website: {cv.get('website', 'N/A')}")

    # Social networks
    if cv.get('social_networks'):
        print(f"\nSocial Networks:")
        for sn in cv['social_networks']:
            network = sn.get('network', 'Unknown')
            username = sn.get('username', '')
            status = username if username else '(not set)'
            print(f"  {network}: {status}")

    # Sections
    sections = cv.get('sections', {})

    if doc.doc_type == 'resume' and sections.get('summary'):
        print(f"\nSummary:")
        for s in sections['summary']:
            print(f"  {s}")

    if sections.get('projects'):
        print(f"\nProjects ({len(sections['projects'])}):")
        for i, p in enumerate(sections['projects'], start=1):
            print(f"\n  [{i}] {p.get('name', 'Unnamed')}")
            if p.get('start_date') or p.get('end_date'):
                print(f"      Date: {p.get('start_date', 'N/A')} to {p.get('end_date', 'N/A')}")
            if p.get('summary'):
                print(f"      Summary: {p.get('summary')}")
            if p.get('highlights'):
                print(f"      Highlights:")
                for h in p['highlights']:
                    print(f"        - {h}")

    if doc.doc_type == 'resume':
        if sections.get('experience'):
            print(f"\nExperience ({len(sections['experience'])}):")
            for i, e in enumerate(sections['experience'], start=1):
                print(f"\n  [{i}] {e.get('position', 'N/A')} at {e.get('company', 'Unknown')}")
                if e.get('start_date') or e.get('end_date'):
                    print(f"      Date: {e.get('start_date', 'N/A')} to {e.get('end_date', 'N/A')}")
                if e.get('location'):
                    print(f"      Location: {e.get('location')}")
                if e.get('highlights'):
                    print(f"      Highlights:")
                    for h in e['highlights']:
                        print(f"        - {h}")

        if sections.get('education'):
            print(f"\nEducation ({len(sections['education'])}):")
            for i, e in enumerate(sections['education'], start=1):
                degree_info = f"{e.get('degree', '')} {e.get('area', '')}".strip()
                print(f"\n  [{i}] {degree_info} at {e.get('institution', 'Unknown')}")
                if e.get('start_date') or e.get('end_date'):
                    print(f"      Date: {e.get('start_date', 'N/A')} to {e.get('end_date', 'N/A')}")
                if e.get('location'):
                    print(f"      Location: {e.get('location')}")
                if e.get('gpa'):
                    print(f"      GPA: {e.get('gpa')}")
                if e.get('highlights'):
                    print(f"      Highlights:")
                    for h in e['highlights']:
                        print(f"        - {h}")

        if sections.get('skills'):
            print(f"\nSkills:")
            for s in sections['skills']:
                print(f"  {s.get('label')}: {s.get('details')}")

    print(f"\n{'=' * 60}")
    input("Press Enter to continue...")


def _change_theme(doc: RenderCVDocument) -> None:
    """
    Change the visual theme of the document.

    Displays available RenderCV themes and allows the user to select one.
    Available themes include classic, engineeringclassic, engineeringresumes,
    moderncv, and sb2nov.

    Args:
        doc: The RenderCVDocument instance to update

    Returns:
        None: Prints success/error message and returns
    """
    current_theme = doc.data.get('design', {}).get('theme', 'sb2nov')

    print("\n=== Change Document Theme ===")
    print(f"Current theme: {current_theme}\n")
    print("Available themes:")
    print("  1) classic          - Classic CV theme")
    print("  2) engineeringclassic - Engineering-focused CV theme")
    print("  3) engineeringresumes - Engineering resume theme")
    print("  4) moderncv         - Modern CV theme")
    print("  5) sb2nov           - Clean resume theme (default)")
    print("  0) Cancel")

    theme_map = {
        "1": "classic",
        "2": "engineeringclassic",
        "3": "engineeringresumes",
        "4": "moderncv",
        "5": "sb2nov"
    }

    choice = input("\nSelect a theme: ").strip()

    if choice == "0" or choice not in theme_map:
        if choice != "0":
            print("[ERROR] Invalid selection.")
        return

    selected_theme = theme_map[choice]

    if selected_theme == current_theme:
        print(f"[INFO] Theme is already set to '{selected_theme}'.")
        return

    try:
        result = doc.update_theme(selected_theme)
        print(f"[SUCCESS] {result}")
    except ValueError as e:
        print(f"[ERROR] {e}")


def _render_document(doc: RenderCVDocument) -> None:
    """
    Render the document to PDF with a progress indicator.

    Runs the render process in a background thread while displaying a progress
    bar. Optionally allows the user to save the PDF to a custom location.

    Args:
        doc: The RenderCVDocument instance to render

    Returns:
        None: Prints success/error message with PDF path and returns
    """
    import shutil
    import threading

    print("\n=== Rendering Document to PDF ===")

    # Use tqdm for progress indication
    render_steps = [
        "Validating document",
        "Processing template",
        "Generating LaTeX",
        "Compiling PDF",
        "Finalizing output"
    ]

    pdf_path = None
    status = None
    error = None
    render_complete = False

    def do_render():
        nonlocal pdf_path, status, error, render_complete
        try:
            status, pdf_path = doc.render()
        except Exception as e:
            error = e
        finally:
            render_complete = True

    # Start render in background thread
    render_thread = threading.Thread(target=do_render)
    render_thread.start()

    # Show progress bar - cycle through all steps
    step_progress = 100 // len(render_steps)
    with tqdm(total=100, bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}") as pbar:
        for i, step_name in enumerate(render_steps):
            pbar.set_description(step_name)

            # Wait a bit for each step (min 0.4s per step for visibility)
            for _ in range(4):
                time.sleep(0.1)
                if render_complete and i >= len(render_steps) - 2:
                    # If render finished and we're near the end, complete quickly
                    break

            # Update progress
            if i < len(render_steps) - 1:
                pbar.update(step_progress)
            else:
                pbar.n = 100
                pbar.refresh()

    render_thread.join()

    if error:
        print(f"\n[ERROR] Could not render PDF: {error}")
        return

    print(f"\n[INFO] Render status: {status}")

    if pdf_path:
        print(f"[SUCCESS] PDF generated at: {pdf_path}")

        save_custom = input("\nSave PDF to a custom location? (y/n): ").strip().lower()
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
