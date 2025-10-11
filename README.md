# 🧠 Capstone Project — Team 2

> *A capstone software project for COSC 499 (Winter 2025), designed and implemented by Team 2 at UBC Okanagan.*

---

## 📚 Table of Contents

1. [Project Overview](#project-overview)  
2. [Features](#features)  
3. [System Architecture](#system-architecture)  
4. [DFD Level 1](#dfd-level-1)  
5. [Work Breakdown Structure](#work-breakdown-structure)  
6. [Project Structure](#project-structure)  
7. [Getting Started](#getting-started)  
8. [Usage](#usage)  
9. [Dependencies](#dependencies)  
10. [Contributing](#contributing)  
11. [License](#license)  
12. [Contact](#contact)

---

## 📝 Project Overview

This project is being developed as part of **COSC 499: Capstone Project** at UBCO.  
The project is **Mining Digital Work Artifacts** is tool designed to help individual analyze reflect on their digtal creavtive and professional output. The main focus is  on extracting and analyzing artifacts generated udring the course of everyday work activites, including **Programming coce**, **Repositories**, **documents**, **notes**, **desgin sketches** and **media files** through the collecting of the user data and the associated metadata, the system will provide insight into the user's contribution, creative direction, and project evolution. This will allow the user/individuals to gain better insight into their work habbits, showcase their contributions, and also highlight their personal growth 

The platform target users are **graduating students** and **early career professionals** who want to improve their **personal portfolio**

- **Course:** COSC 499 (Winter 2025)  
- **Team:** Team 2  
- **Tech Stack:** Python
- **Team Members**:
   - Immanuel Wiessler(20803375)
   - Sam Smith
   - Puneet Maan
   - Samantha Manranda
   - Cameron Gillespie
   - Mahi Gangal (27227875)

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

## 🧭 DFD Level 1

The following Data Flow Diagram (DFD) represents how data moves through the system — from user input to backend processing and output generation.

![DFD Level 1](docs/dfd_level1.png) <!-- Replace with your actual image path -->

**Entities & Processes**

| Entity / Process        | Description                                      |
|--------------------------|--------------------------------------------------|
| External User            | End user interacting with the system             |
| Authentication Service   | Handles login, registration, and user validation |
| Database (SQLite)        | Stores user data and system information          |
| API Handlers             | Coordinates requests and business logic          |

---

## 🧰 Work Breakdown Structure

Below is the **high-level WBS** outlining the major phases of the project:

[📊 View the Google Sheet](https://docs.google.com/spreadsheets/d/1zsUdvJTiAwR4KajjdB9kgwPiE1tOSrDV0mg0tFfgSF8/edit?usp=sharing)

