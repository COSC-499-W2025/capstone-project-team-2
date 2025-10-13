# 🧠 Capstone Project — Team 2

> *A capstone software project for COSC 499 (Winter 2025), designed and implemented by Team 2 at UBC Okanagan.*

---

## 📚 Table of Contents

1. [Project Overview](#project-overview)  
2. [Features](#features)  
3. [System Architecture](#system-architecture)  
4. [DFD Level 1](#dfd-level-1)  
5. [Work Breakdown Structure](#work-breakdown-structure)  


---

## 📝 Project Overview

This project is being developed as part of **COSC 499: Capstone Project** at UBCO.  
The project, titled **Mining Digital Work Artifacts**, is a tool designed to help individuals analyze and reflect on their digtal creative and professional output. The main focus is on extracting and analyzing artifacts generated during the course of everyday work activites, including **Programming code**, **Repositories**, **documents**, **notes**, **desgin sketches** and **media files**. Through the collection of the users data and associated metadata, the system will provide insight into the user's contribution, creative direction, and project evolution. This will allow the user/individual to gain better insight into their work habits, showcase their contributions, and highlight their personal growth. 

The platforms target users are **graduating students** and **early career professionals** who want to improve their **personal portfolio**

- **Course:** COSC 499 (Winter 2025)  
- **Team:** Team 2  
- **Tech Stack:** Python
- **Team Members**:
   - Immanuel Wiessler
   - Sam Smith
   - Puneet Maan
   - Samantha Manranda
   - Cameron Gillespie
   - Mahi Gangal

---

## ✨ Features

- Modular backend and frontend architecture  
- Streamlined user interface and authentication system  
- Structured project documentation (WBS, DFDs, Architecture diagrams)  
- CI/CD deployment pipelines  
- Database integration with SQLite

---

## 🏗️ System Architecture

This system architecture illustrates the structural design of the application, showing how the frontend, backend, database, and external services interact. It emphasizes modularity, scalability, and maintainability through a three-layered design.

<img width="2000" height="1600" alt="Copy of Copy of CAPSTONE 499 System design Team2 -Page-1 drawio" src="https://github.com/user-attachments/assets/bf6d49ac-18c0-4691-b845-ab9ccff00b70" />


**Key Components:**

- **Frontend (Presentation Layer)**: Built using DearPyGui or FreeSimpleGUI, the frontend provides a simple and interactive interface for users to upload files, view metadata, and interact with the application’s features.
- **Backend (Application Layer)**: Handles file parsing, validation, and metadata extraction using os, shutil, zipfile, and pymdeco. Implements logic for ranking projects, summarizing results, and managing errors. Click may optionally support a CLI version of the app.
- **Database Layer**: SQLite is used to store extracted metadata, configuration details, and logs during local development and testing.
- **External Services**: GitHub Actions supports CI/CD for automated testing and updates. Optional APIs may enhance metadata extraction or external integrations.
  
**Design Principles**

- Loose coupling – Components interact through well-defined interfaces
- Scalability through modularity – Each module can be developed and tested independently
- Reusability and maintainability – Code organization supports easy updates and debugging
---

## DFD Level 1

The Level 1 **Data Flow Diagram (DFD)** represents the main system components and how data flows between **external entities**, **core processes**, and **internal data stores**.

![DFD Level 1](https://github.com/COSC-499-W2025/capstone-project-team-2/blob/updated_dfd/level1%20dfd%20updated.png?raw=true)


### External Entities

| Entity              | Description |
|---------------------|-------------|
| **Project Owner**   | Grants consent, uploads zipped folders, provides filters, and retrieves résumé or portfolio-ready outputs. *(Milestone 1–3)* |
| **Maintainer/Admin**| Performs administrative actions like backups and deletions. *(Milestone 2–3)* |
| **Local File System** | Supplies input folders/files and stores output artifacts like reports, dashboards, backups. *(Milestone 1–3)* |
| **External Service** | (Optional) Services like LLMs, used to enhance insights if user consent is given. *(Milestone 2)* |

### Core Processes

| ID    | Process Name             | Description | Milestone |
|-------|--------------------------|-------------|-----------|
| **1.0** | Consent & Config         | Captures user/admin consent, configuration policies, and settings for analysis and privacy. | 1 |
| **2.0** | Ingest & Validate        | Validates, scans, and indexes artifacts from zipped folders. Handles file errors, duplicates, and metadata. | 1 |
| **3.0** | Analyze Projects         | Computes project metrics, contribution roles, timelines, languages, and skills from indexed data. Can interact with external services if consented. | 1–2 |
| **4.0** | Rank & Summarize         | Ranks projects based on user contributions, skill relevance, and recency. Generates summaries, timelines, and portfolio highlights. | 2 |
| **5.0** | Customize & Retrieve     | Lets users retrieve, edit, export, or delete items. Supports portfolio customization and resume ready output generation. | 2–3 |

### Internal Data Stores

| ID     | Data Store               | Description | Milestone |
|--------|--------------------------|-------------|-----------|
| **D1** | Configs & Consents       | Stores consent records, configuration settings, and admin policies. | 1 |
| **D2** | Artifacts & Metadata     | Indexed files, metadata, authorship, and timestamps used for analysis. | 1 |
| **D3** | Insights & Rankings      | Aggregated metrics, skills, rankings, and project timelines. | 2 |
| **D4** | Custom Items & Media     | User-edited descriptions, thumbnails, resume versions, and custom portfolio texts. | 2–3 |
| **D5** | Audit Logs               | Ingestion logs, analysis logs, external service interaction logs, and admin actions. | 2 |

---

### Milestone Overview

| Milestone | Focus | Key Additions |
|-----------|-------|----------------|
| **Milestone 1** | Core ingestion & analysis | Processes 1–3, Data Stores D1–D2 |
| **Milestone 2** | Personalization & logic | Processes 4–5, Data Stores D3–D5, External Services |
| **Milestone 3** | Frontend & outputs | UX/UI for portfolio and resume customization, deeper use of P5 and D4 |

---

## 🧰 Work Breakdown Structure

Below is the **high-level WBS** outlining the major phases of the project:

[📊 View the Google Sheet](https://docs.google.com/spreadsheets/d/1zsUdvJTiAwR4KajjdB9kgwPiE1tOSrDV0mg0tFfgSF8/edit?usp=sharing)

