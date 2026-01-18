# Mahi Gangal T2 Weekly Individual Logs 

## Weekly Overview
- [Week 2 (Jan 12 - Jan 18)](#week-1-jan-12---jan-18)

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
