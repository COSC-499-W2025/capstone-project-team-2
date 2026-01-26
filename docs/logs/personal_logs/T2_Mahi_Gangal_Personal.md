# Mahi Gangal T2 Weekly Individual Logs 

## Weekly Overview
- [Week 2 (Jan 12 - Jan 18)](#week-2-jan-12---jan-18)
- [Week 3 (Jan 19 - Jan 25)](#week-3-jan-19jan-25)

## Week 2 (Jan 12 - Jan 18)

### Peer Eval Screenshot: 

<img width="1079" height="551" alt="mg T2w2" src="https://github.com/user-attachments/assets/137e2373-15d4-4657-896a-8a5dca03b6f2" />

### Tasks Worked On
- Implemented RenderCV integration for non-LLM portfolio generation
- Updated portfolio PDF generation to align with AI-generated resume workflow
- Addressed reviewer feedback and refactored code to use the correct portfolio RenderCV system
- Fixed persistence and UX issues related to portfolio saving
- Ensured all automated tests passed after changes
- Reviewed teammates' PRs 

### Individual Contributions 

- **[PR #290 – RenderCV Integration for Portfolio Generation](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/290)**

Implemented RenderCV as the primary PDF generator for portfolio showcases, mirroring the AI resume workflow for consistency. Added graceful fallback to the legacy PDF generator if RenderCV fails and improved UX by requesting folder paths only when necessary.

### Tests Implemented
- **[PR #290 – RenderCV Integration for Portfolio Generation](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/290)**

Ensured portfolio generation works end-to-end, including RenderCV rendering, data handling, and fallback behavior. All tests passed locally.
  - `test_portfolio_service.py`: Validates portfolio showcase construction and CLI display formatting
  - `test_portfolio_rendercv_service.py`: Tests service initialization, project conversion, CRUD operations, and PDF rendering


### PRs Reviewed

- [**PR #287 – Added Docstring for `user_consent.py`**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/287)
- [**PR #301 – C++ Analysis**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/301)
- [**PR #303 – Cameron Documentation Refactor**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/303)
- [**PR #307 – Team 2 Week 2 Team Log**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/307)


### Additional Details
This week’s work directly builds on last week’s implementation of the new portfolio showcase format, where I fixed issues with the portfolio not displaying correctly in the CLI menu and analysis service and introduced PDF generation for portfolios while separating portfolio and analysis outputs. Based on reviewer feedback, I was asked to integrate the RenderCV library to maintain consistency with the system’s existing resume generation workflow, which became my primary focus this week. Since I had no prior experience working with RenderCV, the integration was challenging and time-consuming, particularly because the portfolio and analysis formats were repeatedly being generated identically despite having separate implementations. Additionally, I encountered input-handling errors when prompting users for a custom save location for generated portfolio PDFs, which required multiple iterations to resolve. Despite these challenges, I successfully refactored the workflow to use RenderCV, preserved the separation between portfolio and analysis logic, addressed all reviewer comments, and achieved full PR approval with all tests passing. In the upcoming week, I plan to take on one of the remaining Milestone 2 requirements and work closely with the team to finalize the project prototype in preparation for peer testing.


## Week 3 (Jan 19–Jan 25)

### Peer Eval Screenshot: 

<img width="1077" height="612" alt="mg t2 w3" src="https://github.com/user-attachments/assets/9023504d-d9ee-438b-98a3-b6aedff791ba" />

### Tasks Worked On
- Implemented new backend API endpoints for privacy consent handling and skill retrieval
- Added and validated unit tests for newly introduced API endpoints
- Designed and implemented a unified OOP aggregation report across multiple programming languages
- Refactored and extended the analysis orchestrator to C++ and C# languages analyzer already implemented.
- Verified all automated tests passed after feature integration
- Reviewed teammates’ pull requests and provided constructive feedback

### Individual Contributions 

- **[PR #322 – Added API endpoint for POST /privacy-consent and GET /skills](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/322)**

Implemented backend API endpoints to handle user privacy consent submission and skill retrieval. Added proper request handling, response formatting, and validation logic, along with comprehensive unit tests to ensure reliability and correctness.

- **[PR #333 – OOP Aggregator Unified Report](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/333)**

Designed and implemented a unified OOP analysis report that aggregates results across multiple languages, including Python, JavaScript, C, C++, and C#. Updated the analysis orchestrator to dynamically trigger language-specific analyzers and produce a single consolidated report, improving scalability and consistency of analysis output.

### Tests Implemented
- **[PR #322 – Added API endpoint for POST /privacy-consent and GET /skills](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/322)**
1. test_consent_API.py: Validates POST /privacy-consent request handling and persistence logic
2. test_skills_API.py: Ensures GET /skills returns accurate and correctly formatted data
  
- **[PR #333 – OOP Aggregator Unified Report](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/333)**
1. test_analysis_service.py

### PRs Reviewed

- [**PR #334 - Add local document analysis insights, CLI display, and tests**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/334)
- [**PR #337 - Team Log T2 Week 3**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/337)
- [**PR #328 - Upload file api**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/328)


### Additional Details
This week’s work focused on both backend API development and advancing the system’s OOP analysis capabilities. I first implemented and tested new API endpoints for privacy consent and skill retrieval, ensuring they met functional and testing requirements. I then worked on a larger feature to unify OOP analysis reporting across multiple programming languages, which required refactoring the analysis orchestrator and coordinating outputs from several language-specific analyzers. The most challenging aspect was ensuring consistent aggregation behavior across languages while keeping the design extensible and compatible with existing services. In the upcoming week, I plan to continue working on remaining Milestone 2 requirements, focus on the peer testing feedback and support the team.

