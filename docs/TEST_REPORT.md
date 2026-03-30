# Test Report

## Scope

This report documents:
- The automated test files currently used by this system.
- The testing strategies used to validate behavior.

## How To Run Tests

From the repository root:

```bash
python3 -m pip install -r src/requirements.txt
python3 -m pytest -q -rs test
```

Optional (if using project virtualenv):

```bash
./.venv/bin/python -m pytest -q -rs test
```

Frontend unit/API tests:

```bash
cd frontend
npm test
```

Frontend Playwright/e2e tests:

```bash
cd frontend
npm run test:e2e
```

## Latest Execution Results

Latest local test execution summary:

- Backend (`./.venv/bin/python -m pytest -q -rs test`):
  - `564 passed, 3 subtests passed, 0 skipped, 0 failed`
- Frontend unit/API (`cd frontend && npm test`):
  - `86 passed, 0 failed, 0 skipped`
- Frontend Playwright/e2e (`cd frontend && npm run test:e2e`):
  - `22 passed, 0 failed`

## Test Files That Work With The System

### Test File Inventory

The following Python test files are present in `test/` and form the automated suite (56 files):

<details>
<summary><strong>Backend Test File Inventory (56) — Click to Expand</strong></summary>

```text
test/test_AI_generated_resume.py
test/test_Generate_AI_RenderCV_portfolio.py
test/test_Generate_Render_CV_Resume.py
test/test_Generate_Resume_AI_Ver2.py
test/test_analysis_API.py
test/test_analysis_service.py
test/test_app_context.py
test/test_c_analyzer.py
test/test_consent_API.py
test/test_contribution_skill_association.py
test/test_core_extraction.py
test/test_cpp_analyzer.py
test/test_csharp_analyzer.py
test/test_data_extraction.py
test/test_db_helper_functions.py
test/test_db_versioning_functions.py
test/test_dedup_index.py
test/test_document_analysis.py
test/test_file_traverser.py
test/test_get_contributors_percentage.py
test/test_individual_contribution_detection.py
test/test_java_analyzer.py
test/test_javascript_oop_analyzer.py
test/test_json_saving.py
test/test_load_json_save.py
test/test_local_resume_generator.py
test/test_multi_project_handler.py
test/test_portfolio.py
test/test_portfolio_generator_API.py
test/test_portfolio_rendercv_service.py
test/test_portfolio_service.py
test/test_project_duration.py
test/test_project_insights.py
test/test_project_insights_API.py
test/test_project_io_API.py
test/test_project_skills.py
test/test_project_stack_detection.py
test/test_project_thumbnail_API.py
test/test_project_type_detection.py
test/test_project_upload_page.py
test/test_python_analyzer.py
test/test_representation_API.py
test/test_resume_exporter.py
test/test_resume_exporter_json_validation.py
test/test_resume_generator_API.py
test/test_resume_item_generator.py
test/test_resume_pdf_generator.py
test/test_saved_projects.py
test/test_skills_API.py
test/test_sqlite_db.py
test/test_startup_pull.py
test/test_user_config_store.py
test/test_user_configuration_integration.py
test/test_user_consent.py
test/test_user_consent_update.py
test/test_utility_methods.py
```

</details>

The following frontend test files are present in `frontend/test/` and are executed by `npm test` (5 files):

<details>
<summary><strong>Frontend Test File Inventory (5) — Click to Expand</strong></summary>

```text
frontend/test/api.test.js
frontend/test/config-helpers.test.js
frontend/test/liquid-shell-helpers.test.js
frontend/test/representation-helpers.test.js
frontend/test/resume_and_portfolio_api.test.js
```

</details>

The following Playwright end-to-end test files are present in `frontend/e2e/` and are executed by `npm run test:e2e` (3 files):

<details>
<summary><strong>Frontend Playwright E2E Inventory (3) — Click to Expand</strong></summary>

```text
frontend/e2e/accessibility.spec.js
frontend/e2e/milestone3-flows.spec.js
frontend/e2e/wcag22-signoff.spec.js
```

</details>

## Test Strategies Used

- Unit testing:
  - Core business logic and utility functions are validated in isolation.
  - Examples: analyzers, resume/portfolio helpers, extraction and traversal logic.

- API endpoint testing (FastAPI `TestClient`):
  - Routes are tested through HTTP-style requests and response assertions.
  - Examples: `test_*_API.py` files (consent, analysis, project IO, skills, resume, portfolio, thumbnails).

- Frontend API/client testing (Node test runner):
  - Frontend API helper modules are tested through request construction and response/error handling assertions.
  - Examples: `frontend/test/api.test.js`, `frontend/test/resume_and_portfolio_api.test.js`.

- Frontend end-to-end testing (Playwright):
  - Browser-level user flows and accessibility checks are validated through Playwright specs.
  - Examples: `frontend/e2e/milestone3-flows.spec.js`, `frontend/e2e/accessibility.spec.js`, `frontend/e2e/wcag22-signoff.spec.js`.

- Mocking and patching:
  - External dependencies and side effects are isolated with `unittest.mock.patch`, `MagicMock`, and `monkeypatch`.
  - Used for filesystem, AI integrations, service layers, and persistence boundaries.

- Integration-style testing:
  - Cross-module workflows are exercised (for example, configuration + consent + API flows).
  - Example: `test_user_configuration_integration.py`.

- Database testing:
  - SQLite behavior is validated with in-memory databases and schema checks.
  - Examples: `test_sqlite_db.py`, `test_db_helper_functions.py`, `test_db_versioning_functions.py`.

- Filesystem and path-safety testing:
  - ZIP ingestion, unsafe paths, save/load, and project file operations are tested using temporary directories.
  - Common fixtures: `tmp_path`, patched save dirs.

- Parameterized and edge-case testing:
  - Multiple inputs and boundary/error cases are covered using `pytest.mark.parametrize` and explicit exception assertions (`pytest.raises`).

- Mixed framework compatibility:
  - The suite uses `pytest` as the main runner while containing both `pytest`-style and `unittest.TestCase` tests.

## Notes

- Latest recorded runs: backend 564 passed (plus 3 subtests), frontend 86 passed.
- External-dependency and platform-sensitive paths are covered using deterministic mocks/stubs.
- This report reflects the current repository state and should be updated when tests are added, removed, or renamed.
