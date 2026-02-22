# API Endpoint Reference

This document is the source-of-truth reference for every FastAPI endpoint registered in `src/API/general_API.py`.

## Base Information

- App module: `src/API/general_API.py`
- Title/version: `DevDoc API` / `1.0.0`
- Interactive docs (when server is running):
  - Swagger UI: `/docs`
  - ReDoc: `/redoc`
  - OpenAPI JSON: `/openapi.json`

## Common Request Models

### PrivacyConsentRequest
```json
{
  "data_consent": true,
  "external_consent": false
}
```

### PreferencesPayload (all fields optional)
```json
{
  "project_order": ["Project A", "Project B"],
  "chronology_corrections": {
    "Project A": {
      "start_date": "2024-01",
      "end_date": "2024-12"
    }
  },
  "comparison_attributes": ["impact", "complexity"],
  "highlight_skills": ["Python", "FastAPI"],
  "showcase_projects": ["Project A"]
}
```

### GenerateResumeRequest
```json
{
  "name": "John_Doe",
  "theme": "sb2nov",
  "overwrite": false
}
```

### EditResumeRequest
```json
{
  "edits": [
    {
      "section": "summary",
      "item_name": "",
      "field": "",
      "new_value": "Updated summary text"
    }
  ]
}
```

### GeneratePortfolioRequest
```json
{
  "name": "Jane_Doe",
  "theme": "sb2nov",
  "overwrite": false
}
```

### EditProjectRequest (portfolio)
```json
{
  "edits": [
    {
      "section": "projects",
      "item_name": "MyProject",
      "field": "summary",
      "new_value": "Updated project summary"
    }
  ]
}
```

### ProjectRequest (resume/portfolio add-project override)
```json
{
  "name": "My Capstone Project",
  "start_date": "2024-09",
  "end_date": "2025-04",
  "location": "Kelowna, BC",
  "summary": "Built a developer portfolio generation tool.",
  "highlights": ["Designed REST API", "Integrated RenderCV"]
}
```

### SaveRequest (custom export target)
```json
{
  "path": "/absolute/or/relative/output/directory"
}
```

### ProjectRoleOverrideRequest
```json
{
  "role": "Backend Developer"
}
```

## 1. Analysis

### `GET /analyze/`
Performs analysis for the current uploaded project.

- Query params:
  - `use_ai` (bool, default `false`): enables AI-assisted analysis.
  - `project_name` (string, optional): explicit project name override.
- Success `200`:
  ```json
  {
    "status": "Analysis Finished and Saved",
    "dedup": {},
    "snapshots": []
  }
  ```
- Notes:
  - Uses `runtimeAppContext.currently_uploaded_file` set by upload flows.
  - On internal failures, this endpoint currently still returns `200` with an error string inside `status`.

## 2. Projects and Thumbnails

### `POST /projects/upload`
Uploads a ZIP for later analysis.

- Content type: `multipart/form-data`
- Form field: `upload_file`
- Success `200`:
  ```json
  {
    "status": "ok",
    "filename": "my_project.zip",
    "stored_path": "/tmp/.../my_project_xxxxxxxx.zip"
  }
  ```
- Validation failure `200`:
  ```json
  {
    "status": "error",
    "message": "file is not a zip file"
  }
  ```

### `GET /projects/`
Returns saved project names.

- Success `200`: `[]` or `['project_1', 'project_2']`

### `GET /projects/{id}`
Returns one saved project analysis.

- Path params:
  - `id`: project name with or without `.json` suffix.
- Success `200`:
  ```json
  {
    "project_name": "my_project",
    "source": "database",
    "analysis": {}
  }
  ```
- Errors:
  - `404`: project not found.
  - `500`: failed to parse local JSON file.

### `DELETE /projects/{id}`
Deletes project data from DB and/or filesystem.

- Path params:
  - `id`: project name with or without `.json`.
- Query params:
  - `save_path` (optional): explicit local file path to delete.
- Success `200`: status payload with `dbstatus` and `status` fields.
- Notes:
  - Internal artifact files are protected and return informational statuses.
  - Path traversal/deletion outside allowed directories is refused with warning status text.

### `GET /projects/{id}/delete`
Legacy compatibility endpoint for deletion.

- Calls the same logic as `DELETE /projects/{id}`.
- Query params:
  - `save_path` (optional)

### `POST /projects/{id}/thumbnail`
Uploads and links a thumbnail to a project insight.

- Path params:
  - `id`: insight UUID or project name.
- Query params:
  - `resize` (bool, default `true`)
- Content type: `multipart/form-data`
- Form field: `thumbnail`
- Success `200`:
  ```json
  {
    "status": "Thumbnail uploaded successfully",
    "project_id": "proj-uuid-123",
    "project_name": "MyProject",
    "thumbnail": {
      "path": "/.../proj-uuid-123.png",
      "filename": "proj-uuid-123.png"
    }
  }
  ```
- Errors:
  - `400`: invalid filename/extension or thumbnail save failure.
  - `404`: project insight not found.
  - `500`: thumbnail saved but not linkable in insights metadata.

### `GET /projects/{id}/thumbnail`
Returns thumbnail metadata for a project.

- Path params:
  - `id`: insight UUID or project name.
- Success `200`:
  ```json
  {
    "project_id": "proj-uuid-123",
    "project_name": "MyProject",
    "thumbnail": {
      "path": "/.../proj-uuid-123.png",
      "filename": "proj-uuid-123.png"
    }
  }
  ```
- Errors:
  - `404`: no thumbnail found.

### `DELETE /projects/{id}/thumbnail`
Deletes a project thumbnail and unlinks it from insights metadata.

- Path params:
  - `id`: insight UUID or project name.
- Success `200`:
  ```json
  {
    "status": "Thumbnail deleted successfully",
    "project_id": "proj-uuid-123",
    "project_name": "MyProject"
  }
  ```
- Errors:
  - `404`: no thumbnail found.

## 3. Consent and Config

### `POST /privacy-consent`
Persists privacy consent and updates runtime flags.

- Body: `PrivacyConsentRequest`
- Success `200`:
  ```json
  {
    "data_consent": true,
    "external_consent": false
  }
  ```
- Errors:
  - `400`: `external_consent=true` while `data_consent=false`.
  - `500`: failed to persist consent.

### `POST /config/update`
Saves a full config dictionary.

- Body: arbitrary JSON object
- Success `200`: empty response body (`null`)
- Errors:
  - `500`: config persistence failure.

### `GET /config/get`
Returns current config dictionary.

- Success `200`: JSON config object.
- Errors:
  - `500`: config load failure.

## 4. Skills

### `GET /skills`
Returns skills extracted from project insights.

- Query params:
  - `detailed` (bool, default `false`)
- Success `200`:
  - `detailed=false`: sorted unique skill list, e.g. `['Docker', 'FastAPI', 'Python']`
  - `detailed=true`: full history entries per project.
- Errors:
  - `404`: no insights recorded.
  - `500`: retrieval/storage errors.

## 5. Representation Preferences

Router prefix: `/representation`

### `GET /representation/preferences`
Returns saved representation preferences.

- Success `200`: preferences object.

### `POST /representation/preferences`
Updates representation preferences (partial updates supported).

- Body: `PreferencesPayload`
- Success `200`: updated preferences object.

### `GET /representation/projects`
Returns projects ordered/filtered by current representation preferences.

- Query params:
  - `only_showcase` (bool, default `false`)
  - `snapshot_label` (string, optional)
- Success `200`:
  ```json
  {
    "projects": [],
    "preferences": {},
    "applied_filters": {}
  }
  ```
- Errors:
  - `404`: no project insights available.
  - `500`: unexpected failure applying preferences.

## 6. Resume Generator

### `POST /resume/generate`
Creates a new resume document ID and YAML.

- Body: `GenerateResumeRequest`
- Success `200`:
  ```json
  {
    "resume_id": "John_Doe_a1b2c3d4",
    "status": "Resume created successfully"
  }
  ```
- Errors:
  - `400`: invalid theme.
  - `409`: resume already exists and `overwrite=false`.

### `GET /resume/{id}`
Returns full resume data.

- Success `200`: includes `name`, `contact`, `theme`, `summary`, `experience`, `education`, `projects`, `skills`, `connections`.
- Errors:
  - `404`: resume not found.

### `POST /resume/{id}/edit`
Applies one or more edits to resume sections.

- Body: `EditResumeRequest`
- Valid `section` values: `experience`, `education`, `projects`, `skills`, `summary`, `contact`, `theme`
- Success `200`:
  ```json
  {
    "results": ["Successfully updated summary", "..."]
  }
  ```
- Errors:
  - `400`: unknown section/field, invalid theme, or operation-specific validation failure.
  - `404`: resume not found.

### `POST /resume/{id}/render`
Renders resume as PDF (default shortcut).

- Same behavior as `POST /resume/{id}/render/pdf`.

### `POST /resume/{id}/render/{format}`
Renders resume and streams file response.

- Path params:
  - `format`: `pdf`, `html`, or `markdown`
- Success `200`: file response with `X-Resume-ID` response header.
- Errors:
  - `400`: unsupported format.
  - `404`: resume not found.
  - `500`: render failure.

### `POST /resume/{id}/export/{format}`
Renders resume and saves to default output directory.

- Path params:
  - `format`: `pdf`, `html`, or `markdown`
- Success `200`:
  ```json
  {
    "status": "Saved successfully",
    "path": "/.../resume_<id>.pdf"
  }
  ```
- Errors:
  - `400`: unsupported format.
  - `404`: resume not found.
  - `500`: render failure.

### `POST /resume/{id}/export/{format}/custom`
Renders resume and saves to a custom directory.

- Body: `SaveRequest`
- Success `200`: same payload shape as default export.
- Errors:
  - `400`: unsupported format or non-existent directory.
  - `404`: resume not found.
  - `500`: render failure.

### `POST /resume/{id}/add/project/{project_name}`
Adds an analyzed project to resume projects.

- Body: optional `ProjectRequest`
- Success `200`:
  ```json
  {
    "status": "Successfully added project 'ProjectName'"
  }
  ```
- Errors:
  - `400`: project record exists but has no `resume_item` data.
  - `404`: resume or project record not found.
  - `500`: unexpected add/save failure.

### `DELETE /resume/{id}`
Deletes resume YAML.

- Success `200`:
  ```json
  {
    "status": "Successfully deleted resume '<id>'"
  }
  ```
- Errors:
  - `404`: resume not found.
  - `500`: filesystem deletion failure.

## 7. Portfolio Generator

### `POST /portfolio-showcase/{project_name}/role`
Sets a manual showcase role override for a project.

- Body: `ProjectRoleOverrideRequest`
- Success `200`:
  ```json
  {
    "project_name": "MyProject",
    "role": "Backend Developer",
    "status": "Role override saved successfully"
  }
  ```
- Errors:
  - `400`: empty role.
  - `500`: persistence failure.

### `GET /portfolio-showcase/{project_name}/role`
Gets showcase role override.

- Success `200`:
  ```json
  {
    "project_name": "MyProject",
    "role": "Backend Developer"
  }
  ```
- Errors:
  - `404`: no role override saved.

### `POST /portfolio/generate`
Creates a new portfolio document ID and YAML.

- Body: `GeneratePortfolioRequest`
- Success `200`:
  ```json
  {
    "portfolio_id": "Jane_Doe_a1b2c3d4",
    "status": "Portfolio created successfully"
  }
  ```
- Errors:
  - `400`: invalid theme.
  - `409`: portfolio already exists and `overwrite=false`.

### `GET /portfolio/{portfolio_id}`
Returns full portfolio data.

- Success `200`: includes `name`, `contact`, `theme`, `summary`, `projects`, `skills`, `connections`.
- Errors:
  - `404`: portfolio not found.

### `POST /portfolio/{portfolio_id}/edit`
Applies one or more edits to portfolio sections.

- Body: `EditProjectRequest`
- Valid `section` values: `projects`, `skills`, `summary`, `contact`, `theme`
- Success `200`:
  ```json
  {
    "results": ["Successfully modified project", "..."]
  }
  ```
- Errors:
  - `400`: unknown section or invalid theme.
  - `404`: portfolio not found.

### `POST /portfolio/{portfolio_id}/add/project/{project_name}`
Adds an analyzed project to portfolio projects.

- Body: optional `ProjectRequest`
- Success `200`:
  ```json
  {
    "status": "Successfully added project 'ProjectName'"
  }
  ```
- Errors:
  - `404`: portfolio or project record not found, or project missing `resume_item` data.
  - `500`: unexpected add/save failure.

### `POST /portfolio/{portfolio_id}/render`
Renders portfolio as PDF (default shortcut).

- Same behavior as `POST /portfolio/{portfolio_id}/render/pdf`.

### `POST /portfolio/{portfolio_id}/render/{format}`
Renders portfolio and streams file response.

- Path params:
  - `format`: `pdf`, `html`, or `markdown`
- Success `200`: file response with `X-Portfolio-ID` response header.
- Errors:
  - `400`: unsupported format.
  - `404`: portfolio not found.
  - `500`: render failure.

### `POST /portfolio/{portfolio_id}/export/{format}`
Renders portfolio and saves to default output directory.

- Path params:
  - `format`: `pdf`, `html`, or `markdown`
- Success `200`:
  ```json
  {
    "status": "Saved successfully",
    "path": "/.../portfolio_<id>.pdf"
  }
  ```
- Errors:
  - `400`: unsupported format.
  - `404`: portfolio not found.
  - `500`: render failure.

### `POST /portfolio/{portfolio_id}/export/{format}/custom`
Renders portfolio and saves to a custom directory.

- Body: `SaveRequest`
- Success `200`: same payload shape as default export.
- Errors:
  - `400`: unsupported format or non-existent directory.
  - `404`: portfolio not found.
  - `500`: render failure.

### `DELETE /portfolio/{portfolio_id}`
Deletes portfolio YAML.

- Success `200`:
  ```json
  {
    "status": "Successfully deleted portfolio '<portfolio_id>'"
  }
  ```
- Errors:
  - `404`: portfolio not found.
  - `500`: filesystem deletion failure.

## Endpoint Coverage Checklist

The endpoints documented above map exactly to all route decorators currently present in:

- `src/API/analysis_API.py`
- `src/API/project_io_API.py`
- `src/API/consent_API.py`
- `src/API/skills_API.py`
- `src/API/representation_API.py`
- `src/API/Resume_Generator_API.py`
- `src/API/Portfolio_Generator_API.py`
