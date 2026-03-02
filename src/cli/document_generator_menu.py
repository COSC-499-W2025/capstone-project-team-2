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
import re
import shutil
from pathlib import Path
from typing import Optional, List

from src.core.app_context import runtimeAppContext
from src.reporting.Generate_AI_Resume import GenerateLocalResume
from src.reporting.Generate_Resume_AI_Ver2 import GenerateResumeAI_Ver2
from src.reporting.Generate_AI_RenderCV_Portfolio_and_Resume import (
    RenderCVDocument, Project, Education, Skills, Connections
)
from src.storage.saved_projects import list_saved_projects


def document_generator_menu() -> None:
    """
    Unified menu for creating and editing resumes and portfolios using RenderCV.

    Allows users to:
    - Create new resume or portfolio documents
    - Load existing documents
    - Add projects from saved analyses (local or AI-powered)
    - Edit contact information and sections
    - Render/Export to PDF, HTML, or Markdown

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
            name = input("Enter your name (0 to cancel): ").strip()
            if name == "0":
                continue
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
            _document_edit_menu(doc)
        elif choice == "2":
            name = input("Enter your name (0 to cancel): ").strip()
            if name == "0":
                print("[INFO] Resume Creation Cancelled")
                continue
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
            _document_edit_menu(doc)
        elif choice == "3":
            _load_existing_document_menu()
        else:
            print("Please choose a valid option (0-3).")


def _load_existing_document_menu() -> None:
    """
    Load an existing resume or portfolio document from saved files.

    Displays a menu for selecting document type (resume/portfolio), then lists
    all existing documents of that type and allows the user to select one to load.

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
        _document_edit_menu(doc)
    except FileNotFoundError:
        print(f"[ERROR] No {doc_type} found for '{selected_name}'.")
    except Exception as e:
        print(f"[ERROR] Could not load document: {e}")


def _document_edit_menu(doc: RenderCVDocument) -> None:
    """
    Display and handle the edit menu for a loaded RenderCV document.

    Presents different menu options based on document type (resume vs portfolio).
    Resume documents have additional sections for education, skills,
    and summary that are not available for portfolios.

    Args:
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
        print("  6) Manage social networks")

        if doc.doc_type == 'resume':
            print("\n-- Education & Skills --")
            print("  7) Manage education")
            print("  8) Manage skills")

            print("\n-- Summary --")
            print("  9) Update summary")

            print("\n-- Document --")
            print("  10) View full document")
            print("  11) Render/Export")
        else:
            # Portfolio uses sequential numbering
            print("\n-- Document --")
            print("  7) View full document")
            print("  8) Render/Export")

        print(f"\n{'─' * 50}")
        print("  0) Save and return")

        choice = input("Select an option: ").strip()

        if choice == "0":
            doc.save()
            print("[SUCCESS] Document saved.")
            return
        elif choice == "1":
            _add_project_from_analysis(doc)
        elif choice == "2":
            _add_project_from_ai(doc)
        elif choice == "3":
            _add_project_manually(doc)
        elif choice == "4":
            _modify_delete_projects(doc)
        elif choice == "5":
            _edit_contact_info(doc)
        elif choice == "6":
            _manage_connections(doc)
        elif choice == "7":
            if doc.doc_type == 'resume':
                _manage_education(doc)
            else:
                _view_document(doc)
        elif choice == "8":
            if doc.doc_type == 'resume':
                _manage_skills(doc)
            else:
                _render_document(doc)
        elif choice == "9" and doc.doc_type == 'resume':
            _update_summary(doc)
        elif choice == "10" and doc.doc_type == 'resume':
            _view_document(doc)
        elif choice == "11" and doc.doc_type == 'resume':
            _render_document(doc)
        else:
            max_opt = "11" if doc.doc_type == 'resume' else "8"
            print(f"Please choose a valid option (0-{max_opt}).")


def _build_summary(resume_item, evidence: dict, doc_type: str, data: dict | None = None) -> str:
    """
    Compose a richer project summary for the document from the already-generated
    ResumeItem fields, the evidence block, and the full saved analysis data.

    For resumes: one-sentence line + impact statement (kept concise).
    For portfolios: full detailed narrative + impact + contributor context +
    OOP narrative + doc-type signals — aimed at a paragraph-length overview.

    Args:
        resume_item: ResumeItem produced by GenerateLocalResume.generate().
        evidence: Evidence dict from data["resume_item"]["evidence"].
        doc_type: "resume" or "portfolio".
        data: Full saved analysis JSON dict (optional). Used for portfolio
              to pull oop_analysis narrative and document_analysis signals
              that are stored at the top level rather than in evidence.

    Returns:
        A multi-sentence summary string ready to set on the Project dataclass.
    """
    parts = []

    # Resume: one sentence + impact only — keep it to ~2 lines
    if doc_type != "portfolio":
        if resume_item.one_sentence_summary:
            parts.append(resume_item.one_sentence_summary)
        if resume_item.impact:
            parts.append(resume_item.impact)
        return " ".join(parts)

    # Portfolio base: detailed summary (base summary + OOP class narrative)
    if resume_item.detailed_summary and resume_item.detailed_summary != "No detailed analysis available.":
        parts.append(resume_item.detailed_summary)
    elif resume_item.one_sentence_summary:
        parts.append(resume_item.one_sentence_summary)

    # Append the impact statement
    if resume_item.impact:
        parts.append(resume_item.impact)

    # --- Portfolio: build a richer paragraph-length narrative ---
    analysis = data or {}

    # 1. OOP narrative paragraphs (data_structures and complexity add real depth)
    oop = analysis.get("oop_analysis") or {}
    narrative = oop.get("narrative") or {}
    for section in ("data_structures", "complexity"):
        text = narrative.get(section, "").strip()
        if text and text not in " ".join(parts):
            parts.append(text)

    # 2. Contributor context — who built it and how collaborative was it
    contributors = analysis.get("contributors") or {}
    contributor_count = len(contributors)
    contributor_names = sorted(contributors.keys())
    if contributor_count > 1:
        names_str = ", ".join(contributor_names[:3])
        suffix = " and others" if contributor_count > 3 else ""
        parts.append(
            f"Built collaboratively by {contributor_count} contributors: {names_str}{suffix}."
        )
    elif contributor_count == 1:
        parts.append(f"Sole contributor: {contributor_names[0]}.")

    # 3. Document signals from document_analysis (stored at top level in the JSON)
    doc_analysis = analysis.get("document_analysis") or {}
    _valuable_types = {"research paper", "report", "proposal", "manual/guide", "specification"}
    found_types: list = []
    doc_key_points: list = []
    _sentence_verbs = {
        "built", "created", "designed", "implemented", "analyzed",
        "evaluated", "proposed", "achieved", "demonstrated", "showed",
        "reduced", "improved", "increased", "developed", "authored",
    }
    for doc in (doc_analysis.get("documents") or []):
        doc_type_info = doc.get("doc_type") or {}
        label = doc_type_info.get("label", "")
        confidence = doc_type_info.get("confidence", "")
        if label in _valuable_types and confidence in ("medium", "high") and label not in found_types:
            found_types.append(label)
        for kp in (doc.get("key_points") or []):
            kp_clean = kp.strip()
            kp_lower = kp_clean.lower()
            if (
                kp_clean not in doc_key_points
                and len(kp_clean) >= 40
                and any(v in kp_lower for v in _sentence_verbs)
                and kp_clean.rstrip().endswith(".", )
            ):
                doc_key_points.append(kp_clean)

    if len(found_types) == 1:
        parts.append(f"Accompanied by a {found_types[0]}.")
    if doc_key_points:
        parts.append(f"Key finding: {doc_key_points[0]}")

    # 4. Tech stack last as supplementary context
    if resume_item.tech_stack and resume_item.tech_stack != "Not detected":
        parts.append(f"Tech stack: {resume_item.tech_stack}.")

    return " ".join(parts)


def _build_evidence_bullets(evidence: dict, doc_type: str) -> list:
    """
    Convert the evidence block saved by generate_resume_item() into
    human-readable highlight bullets.

    For resumes, only high-signal items (test coverage, duration) are included
    to keep bullets concise. For portfolios, the full set of evidence signals
    is surfaced so reviewers can see concrete proof of project substance.

    Args:
        evidence: The evidence dict from the saved analysis JSON
                  (data["resume_item"]["evidence"]).
        doc_type: "resume" or "portfolio".

    Returns:
        List of bullet strings to append to the project's highlights.
    """
    bullets = []
    if not evidence:
        return bullets

    # Test file count — relevant for both doc types
    test_count = evidence.get("test_file_count", 0)
    if test_count:
        bullets.append(f"Includes {test_count} test file(s) demonstrating commitment to code quality.")

    # Duration — relevant for both doc types
    duration = evidence.get("duration")
    if duration and duration != "unavailable" and duration != "—":
        bullets.append(f"Estimated project duration: {duration}.")

    # The signals below are richer context — surface them for portfolios only
    if doc_type == "portfolio":
        # Metrics extracted from project documents (e.g. benchmarks, evaluation scores).
        # Filter out bare numbers/percentages with no surrounding label — they are
        # meaningless without context (e.g. "31%; 12%" tells the reader nothing).
        doc_metrics = evidence.get("doc_metrics") or []
        meaningful_metrics = [
            m for m in doc_metrics
            if not re.fullmatch(r"[\d,.\s]+\s*%?", m.strip()) and len(m.strip()) > 5
        ]
        if meaningful_metrics:
            metrics_str = "; ".join(meaningful_metrics[:4])
            bullets.append(f"Documented metrics: {metrics_str}.")

        # Key points from project documentation.
        # Only include if it reads like a proper sentence (has a verb and ends with
        # punctuation), not a raw code/module descriptor line.
        doc_key_points = evidence.get("doc_key_points") or []
        _sentence_verbs = {
            "built", "created", "designed", "implemented", "analyzed",
            "evaluated", "proposed", "achieved", "demonstrated", "showed",
            "reduced", "improved", "increased", "developed", "authored",
        }
        for kp in doc_key_points[:1]:
            kp_lower = kp.lower()
            looks_like_sentence = (
                any(v in kp_lower for v in _sentence_verbs)
                and kp.rstrip().endswith(("." , "!", "?"))
                and len(kp) >= 40
            )
            if looks_like_sentence:
                bullets.append(f"Key finding: {kp}")

        # Document types — only surface when there is a single clear type,
        # listing many types ("specification, report, research paper") is noise.
        doc_types = evidence.get("doc_types_found") or []
        _valuable_types = {"research paper", "report", "proposal", "manual/guide", "specification"}
        valuable_doc_types = [t for t in doc_types if t in _valuable_types]
        if len(valuable_doc_types) == 1:
            bullets.append(f"Project includes a {valuable_doc_types[0]}.")

        # Contributor breakdown as evidence of collaboration
        breakdown = evidence.get("contributor_breakdown") or {}
        if breakdown:
            contrib_parts = [f"{name} ({pct})" for name, pct in list(breakdown.items())[:3]]
            bullets.append(f"Contributor breakdown: {', '.join(contrib_parts)}.")

    return bullets


def _add_project_from_analysis(doc: RenderCVDocument) -> None:
    """
    Add a project to the document from a saved local analysis.

    Lists all saved project analyses from the default save directory and allows
    the user to select one. The selected analysis is converted to a resume item
    using GenerateLocalResume and added to the document.

    Args:
        doc: The RenderCVDocument instance to add the project to

    Returns:
        None: Prints success/error message and returns
    """
    folder = Path(runtimeAppContext.default_save_dir).resolve()
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
        evidence = (data.get("resume_item") or {}).get("evidence") or {}

        summary = _build_summary(resume_item, evidence, doc.doc_type, data=data)

        start_date = input("Start date (YYYY-MM, or press Enter to skip): ").strip()
        end_date = input("End date (YYYY-MM, or press Enter to skip): ").strip()

        # Start with the responsibilities generated by GenerateLocalResume
        highlights = list(resume_item.key_responsibilities or [])

        # Pull evidence signals saved by generate_resume_item() during analysis
        # and append them as additional highlight bullets.
        evidence_bullets = _build_evidence_bullets(evidence, doc.doc_type)
        highlights.extend(evidence_bullets)

        project = Project(
            name=resume_item.project_title,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            summary=summary,
            highlights=highlights,
        )

        result = doc.add_project(project)
        print(f"[SUCCESS] {result}")
    except Exception as e:
        print(f"[ERROR] Could not add project: {e}")


def _add_project_from_ai(doc: RenderCVDocument) -> None:
    """
    Add a project to the document using AI-powered analysis.

    Requires external consent to be enabled. Lists analyzed projects from the
    database and uses GenerateResumeAI_Ver2 to create an AI-generated resume
    entry via Gemini LLM.

    Args:
        doc: The RenderCVDocument instance to add the project to

    Returns:
        None: Prints success/error message and returns
    """
    if not runtimeAppContext.external_consent:
        print("\n[INFO] External services are disabled in your consent settings.")
        print("Enable external services in Settings to use AI analysis.\n")
        return

    # List all analyzed projects from the database
    projects_list = runtimeAppContext.store.get_all_projects_with_versions()

    if not projects_list:
        print("[INFO] No analyzed projects found in the database.")
        print("Analyze a project first using 'Analyze project' from the main menu.")
        return

    print("\nAnalyzed projects:")
    for i, p in enumerate(projects_list, start=1):
        name = p.get("project_name", "Unknown")
        versions = p.get("total_versions", 1)
        print(f"  {i}) {name} ({versions} version{'s' if versions != 1 else ''})")

    sel = input("\nSelect a project for AI analysis (or 0 to cancel): ").strip()
    if not sel or sel == "0":
        return

    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(projects_list):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    project_name = projects_list[idx].get("project_name")

    print("[INFO] Generating AI resume entry... (this may take a moment)")
    try:
        generator = GenerateResumeAI_Ver2(project_name)
        ai_resume = generator.generate_AI_Resume_entry()

        if ai_resume is None:
            print("[ERROR] Could not generate AI resume entry.")
            return

        summary = ai_resume.one_sentence_summary
        if ai_resume.tech_stack:
            summary = f"{summary} Tech stack: {ai_resume.tech_stack}"

        print("[INFO] AI resume entry generated successfully.")
        start_date = input("Start date (YYYY-MM, or press Enter to skip): ").strip()
        end_date = input("End date (YYYY-MM, or press Enter to skip): ").strip()

        project = Project(
            name=ai_resume.project_title,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
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
    print("(Enter 0 to cancel)\n")
    name = input("Project name: ").strip()
    if name == "0":
        print("[INFO] Cancelled adding project.")
        return
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


def _manage_connections(doc: RenderCVDocument) -> None:
    """
    Unified menu for managing social network connections.

    Provides options to add, modify, or delete social network connections
    in a single submenu interface.

    Args:
        doc: The RenderCVDocument instance to manage connections for

    Returns:
        None: Returns when user selects back option
    """
    while True:
        cv_data = doc.data.get('cv', {})
        connections = cv_data.get('social_networks', [])

        print("\n=== Manage Social Networks ===")
        print("Common networks: LinkedIn, GitHub, GitLab, Twitter, Instagram, YouTube\n")

        if connections:
            print("Current connections:")
            for i, conn in enumerate(connections, start=1):
                network = conn.get('network', 'Unknown')
                username = conn.get('username', 'N/A')
                print(f"  {i}) {network}: {username}")
            print()

        print("Actions:")
        print("  a) Add new connection")
        if connections:
            print("  m) Modify existing connection")
            print("  d) Delete connection")
        print("  0) Back")

        choice = input("\nSelect an action: ").strip().lower()

        if choice == "0":
            return
        elif choice == "a":
            _add_connection(doc)
        elif choice == "m" and connections:
            _select_and_modify_connection(doc, connections)
        elif choice == "d" and connections:
            _select_and_delete_connection(doc, connections)
        else:
            print("[ERROR] Invalid option.")


def _select_and_modify_connection(doc: RenderCVDocument, connections: list) -> None:
    """
    Select and modify a social network connection.

    Args:
        doc: The RenderCVDocument instance
        connections: List of current connections
    """
    sel = input("Enter connection number to modify: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(connections):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    _modify_connection_entry(doc, idx, connections[idx])


def _select_and_delete_connection(doc: RenderCVDocument, connections: list) -> None:
    """
    Select and delete a social network connection.

    Args:
        doc: The RenderCVDocument instance
        connections: List of current connections
    """
    sel = input("Enter connection number to delete: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(connections):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    conn = connections[idx]
    confirm = input(f"Delete '{conn.get('network')}' connection? (y/n): ").strip().lower()
    if confirm == 'y':
        connections.pop(idx)
        doc.save()
        print("[SUCCESS] Connection deleted.")


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


def _manage_education(doc: RenderCVDocument) -> None:
    """
    Unified menu for managing education entries.

    Provides options to add, modify, or delete education entries
    in a single submenu interface.

    Args:
        doc: The RenderCVDocument instance to manage education for

    Returns:
        None: Returns when user selects back option
    """
    while True:
        sections = doc.data.get('cv', {}).get('sections', {})
        education = sections.get('education', [])

        print("\n=== Manage Education ===\n")

        if education:
            print("Current education entries:")
            for i, e in enumerate(education, start=1):
                degree_info = f"{e.get('degree', '')} {e.get('area', '')}".strip()
                print(f"  {i}) {degree_info} at {e.get('institution', 'Unknown')}")
            print()

        print("Actions:")
        print("  a) Add new education")
        if education:
            print("  m) Modify existing education")
            print("  d) Delete education")
        print("  0) Back")

        choice = input("\nSelect an action: ").strip().lower()

        if choice == "0":
            return
        elif choice == "a":
            _add_education(doc)
        elif choice == "m" and education:
            _select_and_modify_education(doc, education)
        elif choice == "d" and education:
            _select_and_delete_education(doc, education)
        else:
            print("[ERROR] Invalid option.")


def _select_and_modify_education(doc: RenderCVDocument, education: list) -> None:
    """
    Select and modify an education entry.

    Args:
        doc: The RenderCVDocument instance
        education: List of current education entries
    """
    sel = input("Enter education number to modify: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(education):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    _modify_education_entry(doc, idx, education[idx])


def _select_and_delete_education(doc: RenderCVDocument, education: list) -> None:
    """
    Select and delete an education entry.

    Args:
        doc: The RenderCVDocument instance
        education: List of current education entries
    """
    sel = input("Enter education number to delete: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(education):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    edu = education[idx]
    confirm = input(f"Delete '{edu.get('degree')} at {edu.get('institution')}'? (y/n): ").strip().lower()
    if confirm == 'y':
        education.pop(idx)
        doc.save()
        print("[SUCCESS] Education entry deleted.")


def _manage_skills(doc: RenderCVDocument) -> None:
    """
    Unified menu for managing skill entries.

    Provides options to add, modify, or delete skill entries
    in a single submenu interface.

    Args:
        doc: The RenderCVDocument instance to manage skills for

    Returns:
        None: Returns when user selects back option
    """
    while True:
        sections = doc.data.get('cv', {}).get('sections', {})
        skills = sections.get('skills', [])

        print("\n=== Manage Skills ===\n")

        if skills:
            print("Current skill categories:")
            for i, s in enumerate(skills, start=1):
                print(f"  {i}) {s.get('label', 'Unknown')}: {s.get('details', '')[:40]}...")
            print()

        print("Actions:")
        print("  a) Add new skill category")
        if skills:
            print("  m) Modify existing skill")
            print("  d) Delete skill")
        print("  0) Back")

        choice = input("\nSelect an action: ").strip().lower()

        if choice == "0":
            return
        elif choice == "a":
            _add_skills(doc)
        elif choice == "m" and skills:
            _select_and_modify_skill(doc, skills)
        elif choice == "d" and skills:
            _select_and_delete_skill(doc, skills)
        else:
            print("[ERROR] Invalid option.")


def _select_and_modify_skill(doc: RenderCVDocument, skills: list) -> None:
    """
    Select and modify a skill entry.

    Args:
        doc: The RenderCVDocument instance
        skills: List of current skill entries
    """
    sel = input("Enter skill number to modify: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(skills):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    _modify_skill_entry(doc, idx, skills[idx])


def _select_and_delete_skill(doc: RenderCVDocument, skills: list) -> None:
    """
    Select and delete a skill entry.

    Args:
        doc: The RenderCVDocument instance
        skills: List of current skill entries
    """
    sel = input("Enter skill number to delete: ").strip()
    try:
        idx = int(sel) - 1
        if idx < 0 or idx >= len(skills):
            print("[ERROR] Invalid selection.")
            return
    except ValueError:
        print("[ERROR] Please enter a number.")
        return

    skill = skills[idx]
    confirm = input(f"Delete skill category '{skill.get('label')}'? (y/n): ").strip().lower()
    if confirm == 'y':
        skills.pop(idx)
        doc.save()
        print("[SUCCESS] Skill entry deleted.")


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
    start_date = input(f"Start date (YYYY-MM) [{project.get('start_date', '')}]: ").strip()
    end_date = input(f"End date (YYYY-MM) [{project.get('end_date', '')}]: ").strip()
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
    if start_date:
        projects[idx]['start_date'] = start_date
    if end_date:
        projects[idx]['end_date'] = end_date
    if summary:
        projects[idx]['summary'] = summary
    if highlights is not None:
        projects[idx]['highlights'] = highlights

    doc.save()
    print("[SUCCESS] Project updated.")



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

    current = doc.sections.get('summary', [''])[0] if doc.sections and doc.sections.get('summary') else ''
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

def _prompt_export_formats() -> List[str]:
    """
    Prompt user to select one or more export formats.

    Returns:
        List[str]: Selected formats (pdf/html/markdown)
    """
    options = [
        ("1", "pdf", "PDF"),
        ("2", "html", "HTML"),
        ("3", "markdown", "Markdown"),
    ]

    print("\nSelect export formats (comma-separated).")
    for code, fmt, label in options:
        print(f"  {code}. {label}")
    raw = input("Formats [default: PDF]: ").strip()

    if not raw:
        return ["pdf"]

    selected: List[str] = []
    for part in raw.split(","):
        token = part.strip()
        for code, fmt, _label in options:
            if token == code and fmt not in selected:
                selected.append(fmt)
                break

    return selected or ["pdf"]

def _render_document(doc: RenderCVDocument) -> None:
    """
    Render the document to selected output formats.

    Calls the render method on the document and optionally allows
    the user to save outputs to a custom location.

    Args:
        doc: The RenderCVDocument instance to render

    Returns:
        None: Prints success/error message with PDF path and returns
    """
    print("\n=== Rendering Document ===")
    formats = _prompt_export_formats()
    print("Rendering... (this may take a moment)")

    try:
        status, outputs = doc.render_outputs(formats)
    except Exception as error:
        print(f"\n[ERROR] Could not render document: {error}")
        return

    if not outputs:
        print(f"\n[ERROR] {status}")
        return

    print(f"\n[INFO] Render status: {status}")

    for fmt in formats:
        for output_path in outputs.get(fmt, []):
            print(f"[SUCCESS] {fmt.upper()} generated at: {output_path}")

    all_outputs = [p for paths in outputs.values() for p in paths]
    if not all_outputs:
        print(f"[ERROR] {status}")
        return

    save_custom = input("\nSave exported files to a custom location? (y/n): ").strip().lower()
    if save_custom == "y":
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            custom_folder = input("Enter the folder path: ").strip()
            if os.path.exists(custom_folder):
                for output_path in all_outputs:
                    custom_path = Path(custom_folder) / output_path.name
                    shutil.copy2(output_path, custom_path)
                    print(f"[SUCCESS] Saved to: {custom_path}")
                break
            else:
                attempts += 1
                print(f"[ERROR] Path not found. ({attempts}/{max_attempts})")
        else:
            print("[WARN] Max attempts reached. Files remain at default location.")