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
- Database integration with MySQL + Docker

---

## 🏗️ System Architecture

This system architecture illustrates the structural design of the application, showing how the frontend, backend, database, and external services interact. It emphasizes modularity, scalability, and maintainability through a three-layered design.

<img width="2000" height="1600" alt="Copy of Copy of CAPSTONE 499 System design Team2 -Page-1 drawio" src="https://github.com/user-attachments/assets/bf6d49ac-18c0-4691-b845-ab9ccff00b70" />



**Project setup:**
Please look at our video demo otherwise follow the steps below:
1. Install dependencies: `pip install -r requirements.txt`
2. Set up Environment Variables: 
```env
GOOGLE_API_KEY=your_google_api_key_here
GITHUB_TOKEN=your_github_token_here

```



**Key Components:**

- **Frontend (Presentation Layer)**: Built using **streamlit** or **FreeSimpleGUI***, offering an intutive menu-driven interface for users to navigate and interact with the application.Key features include:
  - **Interactive menus**: For project analysis,viewing saved projects, portfolio gneration, and configuration management.
  - **User consent workflow**: Guides users through the process of providing consent and configuring for external services permissions
  - **Portfolio generation**: Enables users to generate a portfolio-ready resume or portfolio 



- **Backend (Application Layer)**: The backend powers the core analysis engine, leveraging multiple technologies for comprehensive project insights
  - **File Processing**: Handles ZIP extraction, directory traversal, and      metadata collection achieved using `os`, `shutil`, `zipfile`, and `pathlib`.
  - **Mult-language OOP Analysis**: Analyzes Python source files via the `ast` module and for Java source files via the `javalang` module. Returning unified metrics on inheritance, encapsulation, polymorphism, and code complexity
  - **AI-Powered Analysis**: Integrates with Ollama(Via LangChain) for local LLM-based code review and Google Gemini for improved code review and for generating prototype-ready project summaries
  - **Contributor Detection**: Identifies project collaborators through git history(via GitPython and PyGithub) or file metadata analysis for non-git project
  - **Stack Detection**: Automatically identifies programming languages, frameworks, and skills through scanning dependency files(`requirements.txt`, `package.json`, `composer.json`) and source file extensions, 

- **Database (Storage Layer)**: The application uses MySQL as its primary databases for persistent storage and data management.
 - **Project Data Storage**: stores analyzed project metadata, Json analysis reports, and file blobs for later retrieval.
 - **Containerized Deployment**: MySQL runs within a Docker container(`app_database`),
 with connection details dynamicly set and found in the `DockerFinder` Utiliy.
 
 - **External Services Integration**:
   - **GitHub API**: Enables commit history analysis and contributor statistics for Git-based projects via **PyGithub**

   - **Google Gemini API**: Powers AI-generated resume summaries and project descriptions (requires `GOOGLE_API_KEY`)

  
**Design Principles**

- Loose coupling – Components interact through well-defined interfaces
- Scalability through modularity – Each module can be developed and tested independently
- Reusability and maintainability – Code organization supports easy updates and debugging

---

## DFD Level 1

The Level 1 **Data Flow Diagram (DFD)** represents the main system components and how data flows between **external entities**, **core processes**, and **internal data stores**.

![DFD Level 1](<docs/design/level1 dfd updated.png>)

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

