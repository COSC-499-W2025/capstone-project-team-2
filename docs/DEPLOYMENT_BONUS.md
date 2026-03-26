# Deployment Bonus Runbook (Milestone 3)

This runbook documents how to deploy this project as a bonus feature using Render Blueprint.

## 1. Pre-deploy checks

From repo root:

```bash
docker compose -f docker-compose.deploy.yml config
```

Optional local smoke test (requires Docker Desktop running):

```bash
docker compose -f docker-compose.deploy.yml up --build -d
```

## 2. Push repository changes

Commit and push these deployment files:

- `Dockerfile.backend`
- `Dockerfile.frontend`
- `docker-compose.deploy.yml`
- `render.yaml`
- `src/API/general_API.py` (CORS env support)
- `README.md`

## 3. Deploy with Render Blueprint

1. Open Render dashboard.
2. Click **New** -> **Blueprint**.
3. Connect/select this GitHub repository.
4. Render detects `render.yaml` and proposes two services:
   - `capstone-backend`
   - `capstone-frontend`
5. Create both services.

## 4. Set required/optional environment variables

Backend service (`capstone-backend`):

- `CORS_ORIGINS` = your frontend URL (comma-separated if multiple)
  - Example: `https://capstone-frontend.onrender.com`
- `GOOGLE_API_KEY` = optional (needed for AI-backed features)
- `GITHUB_TOKEN` = optional (needed for GitHub contributor analysis)

Frontend service (`capstone-frontend`):

- `NEXT_PUBLIC_API_BASE` = backend URL
  - Example: `https://capstone-backend.onrender.com`

## 5. Post-deploy verification

After services are live:

- Frontend page loads at frontend URL.
- Backend docs load at:
  - `https://<backend-domain>/docs`
- Backend health quick-check:
  - `https://<backend-domain>/openapi.json`
- Frontend can call backend without CORS errors in browser console.

## 6. Demo evidence for bonus grading

Capture these screenshots for your README/report:

1. Render services list with both services live.
2. Frontend home page at Render URL.
3. Backend `/docs` page.
4. A successful API call from frontend workflow (e.g., project listing/upload flow).

## 7. Common issues

- `Cannot connect to Docker daemon` locally:
  - Start Docker Desktop, then rerun local smoke test.
- Browser CORS errors:
  - Ensure backend `CORS_ORIGINS` exactly includes frontend URL.
- Frontend cannot reach backend:
  - Ensure `NEXT_PUBLIC_API_BASE` uses full `https://` backend URL.
