# API Endpoints

FastAPI app entrypoint: `src/API/general_API.py`

When the app is running:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Notes and Quirks
- `GET /projects` and `GET /projects/` both work in practice.
- Requirement wording may use `{id}`; portfolio routes are implemented with `{portfolio_id}`.

## Analysis

### `GET /analyze/`
- Purpose: analyze the currently uploaded project.
- Query:
  - `use_ai` (bool, default `false`)
  - `project_name` (optional string)
  - `remove_duplicates` (bool, default `true`)
    - `true`: detect duplicates and delete duplicate copies
    - `false`: detect/report duplicates only (no deletion)
- Returns `200`:
  - `{"status":"Analysis Finished and Saved","project_name":"...","dedup":{...},"snapshots":[...]}`
- Errors:
  - `400` no uploaded project has been set
  - `404` uploaded path no longer exists
  - `500` analysis pipeline failure

## Projects and Thumbnails

### `POST /projects/upload`
- Purpose: upload project ZIP for later analysis.
- Body: `multipart/form-data`, file field `upload_file`.
- Returns `200` success:
  - `{"status":"ok","filename":"my_project.zip","stored_path":"...","project_name":"my_project"}`
- Returns `400` validation failure:
  - `{"detail":"file is not a zip file"}`

### `GET /projects/`
- Purpose: list saved project names.
- Returns `200`: `[]` or `["project_1","project_2"]`

### `GET /projects/{id}`
- Purpose: fetch one saved project analysis.
- Path:
  - `id` = project name, with or without `.json`
- Returns `200`:
  - `{"project_name":"my_project","source":"database|filesystem","analysis":{...}}`
- Errors:
  - `404` not found
  - `500` parse/read failure

### `DELETE /projects/{id}`
- Purpose: delete project from DB and/or filesystem.
- Path:
  - `id` = project name, with or without `.json`
- Query:
  - `save_path` (optional path override)
- Returns `200` with status fields:
  - `{"dbstatus":"...","status":"..."}`

### `GET /projects/{id}/delete`
- Purpose: legacy delete route (same behavior as `DELETE /projects/{id}`).
- Query:
  - `save_path` (optional)

### `POST /projects/{id}/type`
- Purpose: Update typing of project in database
- Path:
 - `id` = project name, with or without `.json`
- Query:
 - `project_type` (str): individual or collaborative project
- Returns `200`:
 - `{"message": "Updated successfully", "type": new typing}`
- Errors:
 - `404` project not found

### `POST /projects/{id}/thumbnail`
- Purpose: upload and link a thumbnail.
- Path:
  - `id` = insight UUID or project name
- Query:
  - `resize` (bool, default `true`)
- Body: `multipart/form-data`, file field `thumbnail`.
- Returns `200`:
  - `{"status":"Thumbnail uploaded successfully","project_id":"...","project_name":"...","thumbnail":{"path":"...","filename":"..."}}`
- Errors:
  - `400` bad extension or save failure
  - `404` project insight not found
  - `500` linked metadata update failed

### `GET /projects/{id}/thumbnail`
- Purpose: get thumbnail metadata.
- Path:
  - `id` = insight UUID or project name
- Returns `200`:
  - `{"project_id":"...","project_name":"...","thumbnail":{"path":"...","filename":"..."}}`
- Errors:
  - `404` thumbnail not found

### `DELETE /projects/{id}/thumbnail`
- Purpose: delete thumbnail and unlink metadata.
- Path:
  - `id` = insight UUID or project name
- Returns `200`:
  - `{"status":"Thumbnail deleted successfully","project_id":"...","project_name":"..."}`
- Errors:
  - `404` thumbnail not found

## Consent and Config

### `POST /privacy-consent`
- Purpose: persist consent flags and update runtime flags.
- JSON body:
  - `{"data_consent": true, "external_consent": false}`
- Returns `200` with saved flags.
- Errors:
  - `400` when `external_consent=true` and `data_consent=false`
  - `500` persistence failure

### `POST /config/update`
- Purpose: overwrite user config with a JSON object.
- JSON body: arbitrary object.
- Returns `200` with empty body (`null`).
- Errors:
  - `500` save failure

### `GET /config/get`
- Purpose: read current user config.
- Returns `200` config JSON object.
- Errors:
  - `500` load failure

## Skills

### `GET /skills`
- Purpose: read skills from project insights.
- Query:
  - `detailed` (bool, default `false`)
- Returns `200`:
  - `detailed=false`: sorted unique list (example: `["Docker","FastAPI","Python"]`)
  - `detailed=true`: full per-project history
- Errors:
  - `404` no insights
  - `500` retrieval failure

## Representation Preferences

Router prefix: `/representation`

### `GET /representation/preferences`
- Purpose: fetch saved representation preferences.
- Returns `200` preferences object.

### `POST /representation/preferences`
- Purpose: update preferences (partial update supported).
- JSON body fields (all optional):
  - `project_order`
  - `chronology_corrections`
  - `comparison_attributes`
  - `highlight_skills`
  - `showcase_projects`
- Returns `200` updated preferences object.

### `GET /representation/projects`
- Purpose: list projects after applying preference rules.
- Query:
  - `only_showcase` (bool, default `false`)
  - `snapshot_label` (optional string)
- Returns `200`:
  - `{"projects":[...],"preferences":{...},"applied_filters":{...}}`
- Errors:
  - `404` no insights available
  - `500` preference application failure

## Insights

Router prefix: `/insights`

### `GET /insights/projects`
- Purpose: chronologically list all analyzed projects, with optional filters.
- Query:
  - `language` (optional string) — filter by programming language
  - `skill` (optional string) — filter by skill
  - `since_str` (optional string) — only projects analyzed after this date
- Returns `200`: list of project insight dictionaries in chronological order.

### `GET /insights/skills`
- Purpose: chronologically list all skills and the projects they appear in, with optional filters.
- Query:
  - `skill` (optional string) — filter by skill name
  - `since_str` (optional string) — only entries analyzed after this date
- Returns `200`: list of skill-history dictionaries in chronological order.

### `GET /insights/top-projects`
- Purpose: return the top unique projects using the latest snapshot for ranking and attach evolution evidence from snapshot history.
- Ranking: sorts by latest snapshot contribution score first, then latest skill count, then latest analysis recency.
- Query:
  - `top_n` (optional integer, default `3`) — max number of unique projects to return
  - `contributor` (optional string) — rank by a specific contributor's contribution score
  - `active_only` (optional boolean, default `false`) — when `true`, include only projects that still exist in saved project storage
- Returns `200`: list of dictionaries, each including:
  - `project_name` (string)
  - `snapshot_count` (integer)
  - `score` (number) — contribution score used for ranking
  - `latest` (object) — latest stored project insight snapshot
  - `evolution` (object), including:
    - `first_analyzed_at`
    - `latest_analyzed_at`
    - `new_skills`
    - `new_languages`
    - `file_count_delta`
    - `summary_changed`
    - `project_type_changed`

## Resume

### `GET /resumes`
- Purpose: list all saved resume documents.
- Returns `200`: array of objects, each with:
  - `id` (string) — resume identifier (file stem without `_Resume_CV`)
  - `name` (string) — display name with spaces (UUID suffix stripped)
  - `created_at` (string) — file creation timestamp in ISO-8601 format
- Results are sorted newest-first.

### `POST /resume/generate`
- Purpose: create a new resume YAML document.
- JSON body:
  - `name` (string, required)
  - `theme` (optional, default `sb2nov`)
  - `overwrite` (optional bool, default `false`)
- Returns `200`:
  - `{"resume_id":"John_Doe_a1b2c3d4","status":"Resume created successfully"}`
- Errors:
  - `400` invalid theme
  - `409` already exists and `overwrite=false`

### `GET /resume/{id}`
- Purpose: fetch full resume content.
- Returns `200` with:
  - `name`, `contact`, `theme`, `summary`, `experience`, `education`, `projects`, `skills`, `awards`, `connections`
- Errors:
  - `404` not found

### `POST /resume/{id}/edit`
- Purpose: apply one or more edits.
- JSON body:
  - `{"edits":[{"section":"...","item_name":"...","field":"...","new_value":...}]}`
- Valid sections:
  - `experience`, `education`, `projects`, `skills`, `awards`, `summary`, `contact`, `theme`, `connections`
- Returns `200`:
  - `{"results":[...]}`
- Errors:
  - `400` invalid section/field/theme or validation failure
  - `404` resume not found

### `POST /resume/{id}/render`
- Purpose: render resume as PDF.
- Equivalent to: `POST /resume/{id}/render/pdf`

### `POST /resume/{id}/render/{format}`
- Purpose: render and stream file.
- Path:
  - `format` in `pdf|html|markdown`
- Returns `200` file response with header `X-Resume-ID`.
- Errors:
  - `400` unsupported format
  - `404` resume not found
  - `500` render failure

### `POST /resume/{id}/export/{format}`
- Purpose: render and save to default output directory.
- Path:
  - `format` in `pdf|html|markdown`
- Returns `200`:
  - `{"status":"Saved successfully","path":"..."}`
- Errors:
  - `400` unsupported format
  - `404` resume not found
  - `500` render failure

### `POST /resume/{id}/export/{format}/custom`
- Purpose: render and save to custom directory.
- Path:
  - `format` in `pdf|html|markdown`
- JSON body:
  - `{"path":"/target/directory"}`
- Returns `200`:
  - `{"status":"Saved successfully","path":"..."}`
- Errors:
  - `400` unsupported format or invalid directory
  - `404` resume not found
  - `500` render failure

### `POST /resume/{id}/add/project/manual`
- Purpose: add a project entry with fully manual data (no database lookup).
- JSON body:
  - `name` (string, required)
  - `start_date` (optional string)
  - `end_date` (optional string)
  - `location` (optional string)
  - `summary` (optional string)
  - `highlights` (optional list of strings)
- Returns `200`:
  - `{"status":"..."}`
- Errors:
  - `400` add failure
  - `404` resume not found
  - `500` unexpected error

### `POST /resume/{id}/add/project/{project_name}/ai`
- Purpose: add a project entry to a resume using AI-generated content (Gemini).
- Path:
  - `id` = resume identifier
  - `project_name` = name of the analysed project in the database
- Returns `200`:
  - `{"status":"..."}`
- Errors:
  - `400` AI generation returned no data
  - `404` resume or project not found
  - `500` AI generation or save failure

### `POST /resume/{id}/add/project/{project_name}`
- Purpose: add analyzed project to resume projects.
- JSON body: optional project override fields:
  - `name`, `start_date`, `end_date`, `location`, `summary`, `highlights`
- Returns `200`:
  - `{"status":"Successfully added project 'ProjectName'"}`
- Errors:
  - `400` project record exists but has no `resume_item`
  - `404` resume or project record not found
  - `500` add/save failure

### `DELETE /resume/{id}/project/{project_name}`
- Purpose: remove a project entry from a resume by exact project name.
- Path:
  - `id` = resume identifier
  - `project_name` = exact project name to remove
- Returns `200`:
  - `{"status":"Successfully removed ..."}`
- Errors:
  - `404` resume or project not found

### `POST /resume/{id}/add/education`
- Purpose: add a new education entry to a resume.
- Path:
  - `id` = resume identifier
- JSON body:
  - `institution` (string, required)
  - `area` (optional string)
  - `degree` (optional string)
  - `start_date` (optional string)
  - `end_date` (optional string)
  - `location` (optional string)
  - `gpa` (optional string)
  - `highlights` (optional list of strings)
- Returns `200`:
  - `{"status":"Successfully added education"}`
- Errors:
  - `400` invalid payload or add failure
  - `404` resume not found
  - `409` duplicate institution

### `DELETE /resume/{id}/education/{institution_name}`
- Purpose: remove an education entry from a resume by institution name.
- Path:
  - `id` = resume identifier
  - `institution_name` = exact institution name to remove
- Returns `200`:
  - `{"status":"Successfully removed ..."}`
- Errors:
  - `404` resume or institution not found

### `POST /resume/{id}/add/experience`
- Purpose: add a new experience entry to a resume.
- Path:
  - `id` = resume identifier
- JSON body:
  - `company` (string, required)
  - `position` (optional string)
  - `start_date` (optional string)
  - `end_date` (optional string)
  - `location` (optional string)
  - `highlights` (optional list of strings)
- Returns `200`:
  - `{"status":"Successfully added experience"}`
- Errors:
  - `400` invalid payload or add failure
  - `404` resume not found

### `DELETE /resume/{id}/experience/{company_name}`
- Purpose: remove an experience entry from a resume by company name.
- Path:
  - `id` = resume identifier
  - `company_name` = exact company name to remove
- Returns `200`:
  - `{"status":"Successfully removed ..."}`
- Errors:
  - `404` resume or company not found

### `POST /resume/{id}/add/skill`
- Purpose: add a new skill category to a resume.
- JSON body:
  - `label` (string, required) — category name (e.g., "Languages")
  - `details` (string, required) — comma-separated skills (e.g., "Python, Java, C++")
- Returns `200`:
  - `{"status":"Successfully added skill"}`
- Errors:
  - `400` empty label or add failure
  - `404` resume not found
  - `409` skill with same label already exists

### `POST /resume/{id}/skill/{label}/append`
- Purpose: append items to an existing skill category on a resume.
- Path:
  - `id` = resume identifier
  - `label` = exact skill category label (e.g., "Languages")
- JSON body:
  - `details` (string, required) — comma-separated items to append
- Returns `200`:
  - `{"status":"...","details":"<full updated details string>"}`
- Errors:
  - `400` append failure
  - `404` resume or skill label not found

### `DELETE /resume/{id}/skill/{label}`
- Purpose: remove an entire skill category from a resume by label.
- Path:
  - `id` = resume identifier
  - `label` = exact skill category label to remove
- Returns `200`:
  - `{"status":"..."}`
- Errors:
  - `404` resume or skill label not found

### `POST /resume/{id}/skill/{label}/level`
- Purpose: update the proficiency level of an individual skill within a category.
- Path:
  - `id` = resume identifier
  - `label` = exact skill category label (e.g., "Languages")
- JSON body:
  - `skill_name` (string, required) — exact skill name within the category
  - `level` (string, required) — proficiency level; no server-side validation, any string is accepted. UI uses `Beginner`, `Intermediate`, `Advanced`
- Note: level is stored as markdown bold, e.g. `Python (**Advanced**)`
- Returns `200`:
  - `{"status":"...","details":"<full updated details string>"}`
- Errors:
  - `404` resume, skill category, or individual skill not found

### `POST /resume/{id}/add/award`
- Purpose: add a new award entry to a resume.
- Path:
  - `id` = resume identifier
- JSON body:
  - `name` (string, required)
  - `date` (optional string, `YYYY-MM` format)
  - `location` (optional string) — city/state or issuing organization
  - `highlights` (optional list of strings)
  - `website` (optional string) — injected as `"Link: <url>"` at the end of highlights
- Returns `200`:
  - `{"status":"Successfully added award '<name>'"}`
- Errors:
  - `400` empty name or add failure
  - `404` resume not found
  - `409` award with same name already exists

### `DELETE /resume/{id}/award/{award_name}`
- Purpose: remove an award entry from a resume by exact award name.
- Path:
  - `id` = resume identifier
  - `award_name` = exact award name to remove
- Returns `200`:
  - `{"status":"Successfully deleted: <award_name>"}`
- Errors:
  - `404` resume or award not found

### `DELETE /resume/{id}`
- Purpose: delete resume YAML file.
- Returns `200`:
  - `{"status":"Successfully deleted resume '<id>'"}`
- Errors:
  - `404` not found
  - `500` filesystem delete failure

## Portfolio

### `POST /portfolio-showcase/{project_name}/role`
- Purpose: save custom showcase role text for a project.
- JSON body:
  - `{"role":"Backend Developer"}`
- Returns `200`:
  - `{"project_name":"MyProject","role":"Backend Developer","status":"Role override saved successfully"}`
- Errors:
  - `400` empty role
  - `500` save failure

### `GET /portfolio-showcase/{project_name}/role`
- Purpose: read saved showcase role override.
- Returns `200`:
  - `{"project_name":"MyProject","role":"Backend Developer"}`
- Errors:
  - `404` no saved role

### `GET /portfolios`
- Purpose: list all saved portfolio documents.
- Returns `200`: array of objects, each with:
  - `id` (string) — portfolio identifier (file stem without `_Portfolio_CV`)
  - `name` (string) — display name with spaces (UUID suffix stripped)
  - `created_at` (string) — file creation timestamp in ISO-8601 format
- Results are sorted newest-first.

### `POST /portfolio/generate`
- Purpose: create a new portfolio YAML document.
- JSON body:
  - `name` (string, required)
  - `theme` (optional, default `sb2nov`)
  - `overwrite` (optional bool, default `false`)
- Returns `200`:
  - `{"portfolio_id":"Jane_Doe_a1b2c3d4","status":"Portfolio created successfully"}`
- Errors:
  - `400` invalid theme
  - `409` already exists and `overwrite=false`

### `GET /portfolio/{portfolio_id}`
- Purpose: fetch full portfolio content.
- Returns `200` with:
  - `name`, `contact`, `theme`, `summary`, `projects`, `skills`, `connections`
- Errors:
  - `404` not found

### `POST /portfolio/{portfolio_id}/edit`
- Purpose: apply one or more edits.
- JSON body:
  - `{"edits":[{"section":"...","item_name":"...","field":"...","new_value":"..."}]}`
- Valid sections:
  - `projects`, `skills`, `summary`, `contact`, `theme`, `connections`
- Returns `200`:
  - `{"results":[...]}`
- Errors:
  - `400` invalid section/theme
  - `404` portfolio not found

### `POST /portfolio/{portfolio_id}/add/project/manual`
- Purpose: add a project entry with fully manual data (no database lookup).
- JSON body:
  - `name` (string, required)
  - `start_date` (optional string)
  - `end_date` (optional string)
  - `location` (optional string)
  - `summary` (optional string)
  - `highlights` (optional list of strings)
- Returns `200`:
  - `{"status":"..."}`
- Errors:
  - `400` add failure
  - `404` portfolio not found
  - `500` unexpected error

### `POST /portfolio/{portfolio_id}/add/project/{project_name}`
- Purpose: add analyzed project to portfolio projects.
- JSON body: optional project override fields:
  - `name`, `start_date`, `end_date`, `location`, `summary`, `highlights`
- Returns `200`:
  - `{"status":"Successfully added project 'ProjectName'"}`
- Errors:
  - `404` portfolio/project not found, or missing `resume_item`
  - `500` add/save failure

### `POST /portfolio/{portfolio_id}/add/project/{project_name}/ai`
- Purpose: add a project entry to a portfolio using AI-generated content (Gemini).
- Path:
  - `portfolio_id` = portfolio identifier
  - `project_name` = name of the analysed project in the database
- JSON body (optional):
  - `start_date` (optional string)
  - `end_date` (optional string)
- Returns `200`:
  - `{"status":"..."}`
- Errors:
  - `400` AI generation returned no data
  - `404` portfolio or project not found
  - `500` AI generation or save failure

### `DELETE /portfolio/{portfolio_id}/project/{project_name}`
- Purpose: remove a project entry from a portfolio by exact project name.
- Path:
  - `portfolio_id` = portfolio identifier
  - `project_name` = exact project name to remove
- Returns `200`:
  - `{"status":"Successfully removed ..."}`
- Errors:
  - `404` portfolio or project not found

### `POST /portfolio/{portfolio_id}/render`
- Purpose: render portfolio as PDF.
- Equivalent to: `POST /portfolio/{portfolio_id}/render/pdf`

### `POST /portfolio/{portfolio_id}/render/{format}`
- Purpose: render and stream file.
- Path:
  - `format` in `pdf|html|markdown`
- Returns `200` file response with header `X-Portfolio-ID`.
- Errors:
  - `400` unsupported format
  - `404` portfolio not found
  - `500` render failure

### `POST /portfolio/{portfolio_id}/export/{format}`
- Purpose: render and save to default output directory.
- Path:
  - `format` in `pdf|html|markdown`
- Returns `200`:
  - `{"status":"Saved successfully","path":"..."}`
- Errors:
  - `400` unsupported format
  - `404` portfolio not found
  - `500` render failure

### `POST /portfolio/{portfolio_id}/export/{format}/custom`
- Purpose: render and save to custom directory.
- Path:
  - `format` in `pdf|html|markdown`
- JSON body:
  - `{"path":"/target/directory"}`
- Returns `200`:
  - `{"status":"Saved successfully","path":"..."}`
- Errors:
  - `400` unsupported format or invalid directory
  - `404` portfolio not found
  - `500` render failure

### `POST /portfolio/{portfolio_id}/add/skill`
- Purpose: add a new skill category to a portfolio.
- JSON body:
  - `label` (string, required) — category name (e.g., "Languages")
  - `details` (string, required) — comma-separated skills (e.g., "Python, Java, C++")
- Returns `200`:
  - `{"status":"Successfully added skills"}`
- Errors:
  - `400` empty label or add failure
  - `404` portfolio not found
  - `409` skill with same label already exists

### `POST /portfolio/{portfolio_id}/skill/{label}/append`
- Purpose: append items to an existing skill category on a portfolio.
- Path:
  - `portfolio_id` = portfolio identifier
  - `label` = exact skill category label (e.g., "Languages")
- JSON body:
  - `details` (string, required) — comma-separated items to append
- Returns `200`:
  - `{"status":"...","details":"<full updated details string>"}`
- Errors:
  - `404` portfolio or skill label not found

### `DELETE /portfolio/{portfolio_id}/skill/{label}`
- Purpose: remove an entire skill category from a portfolio by label.
- Path:
  - `portfolio_id` = portfolio identifier
  - `label` = exact skill category label to remove
- Returns `200`:
  - `{"status":"..."}`
- Errors:
  - `404` portfolio or skill label not found

### `POST /portfolio/{portfolio_id}/skill/{label}/level`
- Purpose: update the proficiency level of an individual skill within a category.
- Path:
  - `portfolio_id` = portfolio identifier
  - `label` = exact skill category label (e.g., "Languages")
- JSON body:
  - `skill_name` (string, required) — exact skill name within the category
  - `level` (string, required) — proficiency level; no server-side validation, any string is accepted. UI uses `Beginner`, `Intermediate`, `Advanced`
- Note: level is stored as markdown bold, e.g. `Python (**Advanced**)`
- Returns `200`:
  - `{"status":"...","details":"<full updated details string>"}`
- Errors:
  - `404` portfolio, skill category, or individual skill not found

### `DELETE /portfolio/{portfolio_id}`
- Purpose: delete portfolio YAML file.
- Returns `200`:
  - `{"status":"Successfully deleted portfolio '<portfolio_id>'"}`
- Errors:
  - `404` not found
  - `500` filesystem delete failure

## Requirement Mapping and Tests

All required endpoints are implemented and tested over HTTP style requests using FastAPI `TestClient` (no live server process).

| Requirement wording | Implemented route | HTTP-style tests |
|---|---|---|
| `POST /projects/upload` | `POST /projects/upload` | `test/test_project_io_API.py`, `test/test_analysis_API.py` |
| `POST /privacy-consent` | `POST /privacy-consent` | `test/test_consent_API.py` |
| `GET /projects` | `GET /projects/` (also works as `/projects`) | `test/test_project_io_API.py` |
| `GET /projects/{id}` | `GET /projects/{id}` | `test/test_project_io_API.py` |
| `GET /skills` | `GET /skills` | `test/test_skills_API.py` |
| `GET /resumes` | `GET /resumes` | `test/test_resume_generator_API.py` |
| `GET /resume/{id}` | `GET /resume/{id}` | `test/test_resume_generator_API.py` |
| `POST /resume/generate` | `POST /resume/generate` | `test/test_resume_generator_API.py` |
| `POST /resume/{id}/edit` | `POST /resume/{id}/edit` | `test/test_resume_generator_API.py` |
| `POST /resume/{id}/add/project/{project_name}/ai` | `POST /resume/{id}/add/project/{project_name}/ai` | `test/test_resume_generator_API.py` |
| `DELETE /resume/{id}/project/{project_name}` | `DELETE /resume/{id}/project/{project_name}` | `test/test_resume_generator_API.py` |
| `POST /resume/{id}/add/education` | `POST /resume/{id}/add/education` | `test/test_resume_generator_API.py` |
| `DELETE /resume/{id}/education/{institution_name}` | `DELETE /resume/{id}/education/{institution_name}` | `test/test_resume_generator_API.py` |
| `POST /resume/{id}/add/experience` | `POST /resume/{id}/add/experience` | `test/test_resume_generator_API.py` |
| `DELETE /resume/{id}/experience/{company_name}` | `DELETE /resume/{id}/experience/{company_name}` | `test/test_resume_generator_API.py` |
| `POST /resume/{id}/add/award` | `POST /resume/{id}/add/award` | `test/test_resume_generator_API.py` |
| `DELETE /resume/{id}/award/{award_name}` | `DELETE /resume/{id}/award/{award_name}` | `test/test_resume_generator_API.py` |
| `GET /portfolio/{id}` | `GET /portfolio/{portfolio_id}` | `test/test_portfolio_generator_API.py` |
| `POST /portfolio/generate` | `POST /portfolio/generate` | `test/test_portfolio_generator_API.py` |
| `POST /portfolio/{id}/edit` | `POST /portfolio/{portfolio_id}/edit` | `test/test_portfolio_generator_API.py` |
| `DELETE /portfolio/{id}/project/{project_name}` | `DELETE /portfolio/{portfolio_id}/project/{project_name}` | `test/test_portfolio_generator_API.py` |

## Route Coverage

The endpoint list above covers all route decorators in:
- `src/API/analysis_API.py`
- `src/API/project_io_API.py`
- `src/API/consent_API.py`
- `src/API/skills_API.py`
- `src/API/representation_API.py`
- `src/API/Resume_Generator_API.py`
- `src/API/Portfolio_Generator_API.py`
- `src/API/project_insights_API.py`
