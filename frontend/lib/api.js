/**
 * Centralized frontend API client.
 *
 * This module is the single source of truth for backend endpoint wiring.
 * Keeping requests here gives the team a predictable place to:
 * - inspect endpoint paths,
 * - update payload contracts,
 * - standardize error handling,
 * - and reuse request behavior across pages.
 *
 * Usage pattern:
 * 1. Import small endpoint helpers in route/components.
 * 2. Let this module handle fetch + parse + error translation.
 * 3. Keep UI files focused on state and rendering.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

/**
 * Converts backend error payloads into a readable string.
 *
 * Known backend shapes include:
 * - `"message"`
 * - `{ detail: "message" }`
 * - `{ detail: [{ msg: "..." }, ...] }` (validation style)
 *
 * @param {unknown} detail Raw `detail` value returned by backend.
 * @param {string} fallback Message used when shape is unknown.
 * @returns {string} User-facing error text.
 */
function resolveError(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg || JSON.stringify(d)).join("; ");
  return fallback;
}

/**
 * Shared fetch wrapper used by all endpoint helpers.
 *
 * Responsibilities:
 * - prepend `API_BASE`
 * - throw a friendly message on connectivity failure
 * - decode non-2xx responses and raise `Error`
 * - parse successful responses according to `expect`
 *
 * @param {string} path Relative API path (for example `/projects/`).
 * @param {RequestInit} [init={}] Native fetch init options.
 * @param {"json" | "blob" | "text"} [expect="json"] Response parse mode.
 * @returns {Promise<any>} Parsed response payload.
 * @throws {Error} If network fails or response is non-success.
 */
async function request(path, init = {}, expect = "json") {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error("Cannot reach API server. Is FastAPI running on port 8000?");
  }

  if (!response.ok) {
    let msg = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      msg = resolveError(payload?.detail, msg);
    } catch {
      try {
        const text = await response.text();
        if (text) msg = text;
      } catch {
        // Intentionally no-op: keep fallback message.
      }
    }
    const err = new Error(msg);
    err.status = response.status;
    throw err;
  }

  if (expect === "blob") return response.blob();
  if (expect === "text") return response.text();
  return response.json();
}

/**
 * Returns the currently configured backend base URL.
 *
 * Useful for diagnostics and environment validation.
 *
 * @returns {string}
 */
export function getApiBase() {
  return API_BASE;
}

/**
 * Fetches all analyzed project names available on the backend.
 *
 * @returns {Promise<any>}
 */
export function fetchProjects() {
  return request("/projects/");
}

/**
 * Fetches one analyzed project payload by project name.
 *
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function fetchProjectByName(projectName) {
  return request(`/projects/${encodeURIComponent(projectName)}`);
}

/**
 * Uploads a ZIP file to backend project ingestion.
 *
 * `nameOverride` is primarily used when the client synthesizes a `File`
 * object from another source (for example folder compression).
 *
 * @param {File} file
 * @param {string} [nameOverride=""]
 * @returns {Promise<any>}
 */
export function uploadProjectZip(file, nameOverride = "") {
  const form = new FormData();
  form.append("upload_file", file, nameOverride || file.name);
  return request("/projects/upload", { method: "POST", body: form });
}

/**
 * Starts analysis pipeline for uploaded project data.
 *
 * If `projectName` is empty, backend uses its default selection behavior.
 *
 * @param {string} [projectName=""]
 * @returns {Promise<any>}
 */
export function analyzeUploadedProject(projectName = "") {
  const query = projectName ? `?project_name=${encodeURIComponent(projectName)}` : "";
  return request(`/analyze${query}`);
}

/**
 * Fetches all project insight snapshots.
 *
 * @returns {Promise<any>}
 */
export function fetchProjectInsights() {
  return request("/insights/projects");
}

/**
 * Fetches persisted user configuration.
 *
 * @returns {Promise<any>}
 */
export function fetchConfig() {
  return request("/config/get");
}

/**
 * Persists privacy consent settings.
 *
 * @param {boolean} externalAllowed Whether external integrations are allowed.
 * @returns {Promise<any>}
 */
export function saveConsent(externalAllowed) {
  return request("/privacy-consent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data_consent: true, external_consent: externalAllowed })
  });
}

/**
 * Replaces config payload with provided object.
 *
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function updateConfig(payload) {
  return request("/config/update", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Fetches all saved resume IDs and display names.
 *
 * @returns {Promise<Array<{id: string, name: string}>>}
 */
export function fetchResumes() {
  return request("/resumes");
}

/**
 * Generates a resume document for a given person/theme.
 *
 * @param {string} name
 * @param {string} theme
 * @returns {Promise<any>}
 */
export function generateResume(name, theme) {
  return request("/resume/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, theme })
  });
}

/**
 * Lists all saved resume documents.
 *
 * @returns {Promise<Array<{id: string, display_name: string, created_at: number}>>}
 */
export function fetchResumes() {
  return request("/resumes");
}

/**
 * Lists all saved portfolio documents.
 *
 * @returns {Promise<Array<{id: string, display_name: string, created_at: number}>>}
 */
export function fetchPortfolios() {
  return request("/portfolios");
}

/**
 * Fetches one resume document by id.
 *
 * @param {string} id
 * @returns {Promise<any>}
 */
export function fetchResume(id) {
  return request(`/resume/${encodeURIComponent(id)}`);
}

/**
 * Deletes one resume document by id.
 *
 * @param {string} id
 * @returns {Promise<any>}
 */
export function deleteResume(id) {
  return request(`/resume/${encodeURIComponent(id)}`, { method: "DELETE" });
}

/**
 * Applies a batch of resume edits.
 *
 * @param {string} id
 * @param {any[]} edits
 * @returns {Promise<any>}
 */
export function editResume(id, edits) {
  return request(`/resume/${encodeURIComponent(id)}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ edits })
  });
}

/**
 * Adds an analyzed project entry to a resume.
 *
 * @param {string} id
 * @param {string} projectName
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addResumeProject(id, projectName, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
}

/**
 * Adds an analyzed project to a resume using AI-generated content.
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function addResumeProjectAI(id, projectName) {
  return request(`/resume/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}/ai`, { method: "POST" });
}

/**
 * Adds a resume education entry.
 *
 * @param {string} id
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addResumeEducation(id, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/education`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Removes a resume education entry by institution key.
 *
 * @param {string} id
 * @param {string} institution
 * @returns {Promise<any>}
 */
export function removeResumeEducation(id, institution) {
  return request(`/resume/${encodeURIComponent(id)}/education/${encodeURIComponent(institution)}`, {
    method: "DELETE"
  });
}

/**
 * Adds a resume experience entry.
 *
 * @param {string} id
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addResumeExperience(id, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/experience`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Removes a resume experience entry by company key.
 *
 * @param {string} id
 * @param {string} company
 * @returns {Promise<any>}
 */
export function removeResumeExperience(id, company) {
  return request(`/resume/${encodeURIComponent(id)}/experience/${encodeURIComponent(company)}`, {
    method: "DELETE"
  });
}

/**
 * Renders a resume into requested export format.
 *
 * @param {string} id
 * @param {string} format
 * @returns {Promise<Blob>}
 */
export function renderResume(id, format) {
  return request(`/resume/${encodeURIComponent(id)}/render/${format}`, { method: "POST" }, "blob");
}

/**
 * Renders a resume and saves it to the default output directory.
 *
 * @param {string} id
 * @param {string} format
 * @returns {Promise<any>}
 */
export function exportResume(id, format) {
  return request(`/resume/${encodeURIComponent(id)}/export/${format}`, { method: "POST" });
}

/**
 * Renders a resume and saves it to a custom directory.
 *
 * @param {string} id
 * @param {string} format
 * @param {string} path Target directory path.
 * @returns {Promise<any>}
 */
export function exportResumeCustom(id, format, path) {
  return request(`/resume/${encodeURIComponent(id)}/export/${format}/custom`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path })
  });
}

/**
 * Adds a project entry to a resume with fully manual data (no DB lookup).
 *
 * @param {string} id
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addResumeProjectManual(id, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/project/manual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Adds a new skill category to a resume.
 *
 * @param {string} id
 * @param {{ label: string, details: string }} payload
 * @returns {Promise<any>}
 */
export function addResumeSkill(id, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/skill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Appends items to an existing skill category on a resume.
 *
 * @param {string} id
 * @param {string} label Exact skill category label.
 * @param {string} details Comma-separated items to append.
 * @returns {Promise<any>}
 */
export function appendResumeSkill(id, label, details) {
  return request(`/resume/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}/append`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ details })
  });
}

/**
 * Removes a skill category from a resume by label.
 *
 * @param {string} id
 * @param {string} label Exact skill category label.
 * @returns {Promise<any>}
 */
export function removeResumeSkill(id, label) {
  return request(`/resume/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}`, {
    method: "DELETE"
  });
}

/**
 * Fetches all saved portfolio IDs and display names.
 *
 * @returns {Promise<Array<{id: string, name: string}>>}
 */
export function fetchPortfolios() {
  return request("/portfolios");
}

/**
 * Generates a portfolio document for a given person/theme.
 *
 * @param {string} name
 * @param {string} theme
 * @returns {Promise<any>}
 */
export function generatePortfolio(name, theme) {
  return request("/portfolio/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, theme })
  });
}

/**
 * Fetches one portfolio document by id.
 *
 * @param {string} id
 * @returns {Promise<any>}
 */
export function fetchPortfolio(id) {
  return request(`/portfolio/${encodeURIComponent(id)}`);
}

/**
 * Deletes one portfolio document by id.
 *
 * @param {string} id
 * @returns {Promise<any>}
 */
export function deletePortfolio(id) {
  return request(`/portfolio/${encodeURIComponent(id)}`, { method: "DELETE" });
}

/**
 * Applies a batch of portfolio edits.
 *
 * @param {string} id
 * @param {any[]} edits
 * @returns {Promise<any>}
 */
export function editPortfolio(id, edits) {
  return request(`/portfolio/${encodeURIComponent(id)}/edit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ edits })
  });
}

/**
 * Adds an analyzed project entry to a portfolio.
 *
 * @param {string} id
 * @param {string} projectName
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addPortfolioProject(id, projectName, payload) {
  return request(`/portfolio/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {})
  });
}

/**
 * Renders a portfolio into requested export format.
 *
 * @param {string} id
 * @param {string} format
 * @returns {Promise<Blob>}
 */
/**
 * Adds an analyzed project to a portfolio using AI-generated content.
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function addPortfolioProjectAI(id, projectName) {
  return request(`/portfolio/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}/ai`, { method: "POST" });
}

export function renderPortfolio(id, format) {
  return request(`/portfolio/${encodeURIComponent(id)}/render/${format}`, { method: "POST" }, "blob");
}

/**
 * Renders a portfolio and saves it to the default output directory.
 *
 * @param {string} id
 * @param {string} format
 * @returns {Promise<any>}
 */
export function exportPortfolio(id, format) {
  return request(`/portfolio/${encodeURIComponent(id)}/export/${format}`, { method: "POST" });
}

/**
 * Renders a portfolio and saves it to a custom directory.
 *
 * @param {string} id
 * @param {string} format
 * @param {string} path Target directory path.
 * @returns {Promise<any>}
 */
export function exportPortfolioCustom(id, format, path) {
  return request(`/portfolio/${encodeURIComponent(id)}/export/${format}/custom`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path })
  });
}

/**
 * Adds a project entry to a portfolio with fully manual data (no DB lookup).
 *
 * @param {string} id
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addPortfolioProjectManual(id, payload) {
  return request(`/portfolio/${encodeURIComponent(id)}/add/project/manual`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Adds a new skill category to a portfolio.
 *
 * @param {string} id
 * @param {{ label: string, details: string }} payload
 * @returns {Promise<any>}
 */
export function addPortfolioSkill(id, payload) {
  return request(`/portfolio/${encodeURIComponent(id)}/add/skill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Appends items to an existing skill category on a portfolio.
 *
 * @param {string} id
 * @param {string} label Exact skill category label.
 * @param {string} details Comma-separated items to append.
 * @returns {Promise<any>}
 */
export function appendPortfolioSkill(id, label, details) {
  return request(`/portfolio/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}/append`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ details })
  });
}

/**
 * Removes a skill category from a portfolio by label.
 *
 * @param {string} id
 * @param {string} label Exact skill category label.
 * @returns {Promise<any>}
 */
export function removePortfolioSkill(id, label) {
  return request(`/portfolio/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}`, {
    method: "DELETE"
  });
}

/**
 * Saves a human-authored role override for a project's portfolio showcase.
 *
 * @param {string} projectName
 * @param {string} role
 * @returns {Promise<any>}
 */
export function setPortfolioShowcaseRole(projectName, role) {
  return request(`/portfolio-showcase/${encodeURIComponent(projectName)}/role`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role })
  });
}

/**
 * Retrieves the saved role override for a project's portfolio showcase.
 *
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function getPortfolioShowcaseRole(projectName) {
  return request(`/portfolio-showcase/${encodeURIComponent(projectName)}/role`);
}

/**
 * Removes one project entry from a portfolio.
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function removeResumeProject(id, projectName) {
  return request(`/resume/${encodeURIComponent(id)}/project/${encodeURIComponent(projectName)}`, {
    method: "DELETE"
  });
}

export function removePortfolioProject(id, projectName) {
  return request(`/portfolio/${encodeURIComponent(id)}/project/${encodeURIComponent(projectName)}`, {
    method: "DELETE"
  });
}

/**
 * Removes a resume project entry by project name.
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function removeResumeProject(id, projectName) {
  return request(`/resume/${encodeURIComponent(id)}/project/${encodeURIComponent(projectName)}`, {
    method: "DELETE"
  });
}

/**
 * Adds a project to a resume using AI-generated content (no manual payload).
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function addResumeProjectAI(id, projectName) {
  return request(`/resume/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
}

/**
 * Adds a project to a portfolio using AI-generated content (no manual payload).
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function addPortfolioProjectAI(id, projectName) {
  return request(`/portfolio/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
}

/**
 * Adds a new skill category to a resume.
 *
 * @param {string} id
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addResumeSkill(id, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/skill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Appends items to an existing resume skill category.
 *
 * @param {string} id
 * @param {string} label
 * @param {Record<string, any>} details
 * @returns {Promise<any>}
 */
export function appendResumeSkill(id, label, details) {
  return request(`/resume/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}/append`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(details)
  });
}

/**
 * Removes a skill category from a resume.
 *
 * @param {string} id
 * @param {string} label
 * @returns {Promise<any>}
 */
export function removeResumeSkill(id, label) {
  return request(`/resume/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}`, {
    method: "DELETE"
  });
}

/**
 * Adds a new skill category to a portfolio.
 *
 * @param {string} id
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function addPortfolioSkill(id, payload) {
  return request(`/portfolio/${encodeURIComponent(id)}/add/skill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Appends items to an existing portfolio skill category.
 *
 * @param {string} id
 * @param {string} label
 * @param {Record<string, any>} details
 * @returns {Promise<any>}
 */
export function appendPortfolioSkill(id, label, details) {
  return request(`/portfolio/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}/append`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(details)
  });
}

/**
 * Removes a skill category from a portfolio.
 *
 * @param {string} id
 * @param {string} label
 * @returns {Promise<any>}
 */
export function removePortfolioSkill(id, label) {
  return request(`/portfolio/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}`, {
    method: "DELETE"
  });
}
