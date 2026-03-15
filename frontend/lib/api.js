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
 * Fetches a saved portfolio showcase role override for one project.
 *
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function getPortfolioShowcaseRole(projectName) {
  return request(`/portfolio-showcase/${encodeURIComponent(projectName)}/role`);
}

/**
 * Saves a portfolio showcase role override for one project.
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
export function renderPortfolio(id, format) {
  return request(`/portfolio/${encodeURIComponent(id)}/render/${format}`, { method: "POST" }, "blob");
}

/**
 * Removes one project entry from a portfolio.
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function removePortfolioProject(id, projectName) {
  return request(`/portfolio/${encodeURIComponent(id)}/project/${encodeURIComponent(projectName)}`, {
    method: "DELETE"
  });
}
