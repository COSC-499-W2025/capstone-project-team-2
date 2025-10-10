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
The project is **Mining Digital Work Artifcats** is tool
designed to help individual analyze reflect on their 
digtal creavtive and professional output. The main focus is  on extracting and analyzing artifacts generated udring the course of everyday work activites, Including
**Programming coce**, **Repositories**, **documents**,
**notes**,**desgin sketches** and **media files** through the collecting of the user data and the associated metadata, the system will provide insight into the user's contribution, creative direction, and project evolution. This will allow the user/individuals to gain better insight into their work habbits, showcase their contributions,and also highlight their personal growth 

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

---

## ✨ Features

- Modular backend and frontend architecture  
- Streamlined user interface and authentication system  
- Structured project documentation (WBS, DFDs, Architecture diagrams)  
- CI/CD deployment pipelines  
- Database integration with SQLite

---

## 🏗️ System Architecture

The architecture of the system follows a **modular layered design**, separating concerns across the **presentation**, **application**, and **data** layers.

![System Architecture](docs/architecture_diagram.png) <!-- Replace with your actual image path -->

**Key Components:**

- **Frontend (Presentation Layer)**: Streamlit UI or web-based interface  
- **Backend (Application Layer)**: Python-based logic and API handlers  
- **Database Layer**: SQLite for local development and testing  
- **External Services**: GitHub Actions for CI/CD, optional API integrations

**Design Principles**

- Loose coupling between components  
- Scalability through modularity  
- Reusability and maintainability

---

## 🧭 DFD Level 1

The **Level 1 Data Flow Diagram** provides a more detailed view of data movement between processes, entities, and data stores.

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

