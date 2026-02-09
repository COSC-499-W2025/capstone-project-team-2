# Mahi Gangal T2 Weekly Individual Logs 

## Weekly Overview
- [Week 2 (Jan 12 - Jan 18)](#week-2-jan-12---jan-18)
- [Week 3 (Jan 19 - Jan 25)](#week-3-jan-19jan-25)
- [Week 4-5 (Jan 26 – Feb 8)](#week-4-5-jan-26feb-8)

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

## Week 4-5 (Jan 26–Feb 8)

### Peer Eval Screenshot: 

<img width="1096" height="618" alt="MG T2W5" src="https://github.com/user-attachments/assets/43901d1f-857d-4035-8868-31adc4b68a0f" />

### Tasks Worked On
- Fixed project duration estimation to correctly handle missing or incomplete timestamps.
- Updated the /skills API endpoint to return a 404 when insights are missing or empty instead of an empty 200 response.
- Fixed portfolio workflow so PDF generation is no longer forced by default.
- Extended the RenderCV pipeline to support multi-format exports (PDF, HTML, Markdown).
- Updated the RenderCV CLI menu to prompt users for their preferred export formats.
- Strengthened test coverage for all features by adding or updating comprehensive tests.
- Reviewed teammates’ pull requests and provided constructive feedback

### Individual Contributions 

- **[PR #355 – project duration fixed](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/355)**

Fixed project duration calculation and made the output human-readable. Improved fallback logic when timestamps were missing.

- **[PR #349 – Skills endpoint Error Handling](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/349)**

Made /skills return 404 when insights are missing or empty. Narrowed exception handling and added edge-case tests.

- **[PR #394 – Multiple export formats](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/394)**

Added PDF, HTML, and Markdown export options to RenderCV. Updated CLI prompts and output handling with new tests.

- **[PR #376 – User prompts added for Portfolio view](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/376)**

Made PDF generation optional instead of forced. Added clear user prompts and updated related tests.

### Tests Implemented

- **[PR #355 – project duration fixed](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/355)**
1. test_project_duration.py
- **[PR #349 – Skills endpoint Error Handling](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/349)**
1. test_skills_API.py: Ensures GET /skills returns accurate and correctly formatted data
- **[PR #394 – Multiple export formats](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/394)**
1. test_portfolio.py
- **[PR #376 – User prompts added for Portfolio view](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/376)**
1. test_document_generator_menu.py
2. test_Generate_Render_CV_Resume.py
3. test_portfolio_rendercv_service.py

### PRs Reviewed

- [**PR #340 – Peer Testing files**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/340)
- [**PR #345 – Fixed constent_md not showing up**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/345)
- [**PR #347 – PL for Week 18**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/347)
- [**PR #356 – Project file traverser for sorting files into analyzers**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/356)
- [**PR #378 – Immanuel Wiessler personal log Week 19 done**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/378)
- [**PR #382 – added code so that critical errors bubble up to api in individual_contribution_detection.py**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/382)
- [**PR #384 – errors in c_oop_analyzer.py to api**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/384)
- [**PR #393 – Update Sam_Smith_Personal.md**](https://github.com/COSC-499-W2025/capstone-project-team-2/pull/393)

### Additional Details

In Week 3, I created the initial /skills API endpoint, and in Week 4 I built on that work by adding proper error handling so the endpoint now returns a clear 404 when insights are missing or empty. I also fixed the project duration estimator in Week 4 in response to peer-testing feedback, improving fallback logic for missing timestamps and making outputs human-readable. In Week 5, I shifted focus toward bug fixes and usability improvements based on peer testing, including making PDF generation optional and enabling multiple export formats (PDF/HTML/Markdown) in RenderCV. Overall, Week 4 centered on correctness and reliability of core features, while Week 5 emphasized user experience and robustness. Next week, I plan to address any remaining peer-testing feedback and Milestone 2 requirements, and resolve any issues arising from my recent changes. The main challenges involved handling missing timestamps and updating tests after CLI behaviour changes; both were successfully resolved, and there are currently no major blockers.

