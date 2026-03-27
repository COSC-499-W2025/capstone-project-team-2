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
 * Deletes an analyzed project by name.
 *
 * The backend always returns HTTP 200; errors are signalled via status-string
 * prefixes. This helper translates [WARNING] and [INFO] responses into thrown
 * errors so callers can handle them uniformly.
 *
 * @param {string} projectName
 * @returns {Promise<void>}
 */
export async function deleteProject(projectName) {
  const result = await request(`/projects/${encodeURIComponent(projectName)}`, { method: "DELETE" });
  const status = result?.status ?? "";
  if (status.startsWith("[WARNING]")) {
    throw new Error(status);
  }
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
 * Fetches top unique projects with latest snapshot data and evolution evidence.
 *
 * @param {{ topN?: number, contributor?: string, activeOnly?: boolean }} [options={}]
 * @returns {Promise<any>}
 */
export function fetchTopProjectHistories(options = {}) {
  const params = new URLSearchParams();
  if (Number.isFinite(options.topN)) params.set("top_n", String(options.topN));
  if (options.contributor) params.set("contributor", options.contributor);
  if (options.activeOnly) params.set("active_only", "true");
  const query = params.toString();
  return request(`/insights/top-projects${query ? `?${query}` : ""}`);
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
 * Fetches stored representation preferences.
 *
 * @returns {Promise<any>}
 */
export function fetchRepresentationPreferences() {
  return request("/representation/preferences");
}

/**
 * Persists representation preferences.
 *
 * @param {Record<string, any>} payload
 * @returns {Promise<any>}
 */
export function updateRepresentationPreferences(payload) {
  return request("/representation/preferences", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Fetches projects with representation preferences applied.
 *
 * @param {{ onlyShowcase?: boolean, snapshotLabel?: string }} [options={}]
 * @returns {Promise<any>}
 */
export function fetchRepresentationProjects(options = {}) {
  const params = new URLSearchParams();
  if (options.onlyShowcase) params.set("only_showcase", "true");
  if (options.snapshotLabel) params.set("snapshot_label", options.snapshotLabel);
  const query = params.toString();
  return request(`/representation/projects${query ? `?${query}` : ""}`);
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
export function addResumeProjectAI(id, projectName, payload) {
  const opts = { method: "POST" };
  if (payload) {
    opts.headers = { "Content-Type": "application/json" };
    opts.body = JSON.stringify(payload);
  }
  return request(`/resume/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}/ai`, opts);
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
 * Adds a new award entry to an existing resume.
 *
 * @param {string} id
 * @param {{ name: string, date?: string, location?: string, highlights?: string[], website?: string }} payload
 * @returns {Promise<any>}
 */
export function addResumeAward(id, payload) {
  return request(`/resume/${encodeURIComponent(id)}/add/award`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

/**
 * Removes an award entry from an existing resume by award name.
 *
 * @param {string} id
 * @param {string} awardName
 * @returns {Promise<any>}
 */
export function removeResumeAward(id, awardName) {
  return request(`/resume/${encodeURIComponent(id)}/award/${encodeURIComponent(awardName)}`, {
    method: "DELETE"
  });
}

/**
 * Updates the proficiency level of an individual skill within a resume skill category.
 *
 * @param {string} id
 * @param {string} label Category label (e.g., "Languages")
 * @param {string} skillName Individual skill name (e.g., "Python")
 * @param {string} level New level (e.g., "Advanced")
 * @returns {Promise<any>}
 */
export function updateResumeSkillLevel(id, label, skillName, level) {
  return request(`/resume/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}/level`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skill_name: skillName, level })
  });
}

/**
 * Updates the proficiency level of an individual skill within a portfolio skill category.
 *
 * @param {string} id
 * @param {string} label Category label (e.g., "Languages")
 * @param {string} skillName Individual skill name (e.g., "Python")
 * @param {string} level New level (e.g., "Advanced")
 * @returns {Promise<any>}
 */
export function updatePortfolioSkillLevel(id, label, skillName, level) {
  return request(`/portfolio/${encodeURIComponent(id)}/skill/${encodeURIComponent(label)}/level`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skill_name: skillName, level })
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
/**
 * Adds an analyzed project to a portfolio using AI-generated content.
 *
 * @param {string} id
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function addPortfolioProjectAI(id, projectName, payload) {
  const opts = { method: "POST" };
  if (payload) {
    opts.headers = { "Content-Type": "application/json" };
    opts.body = JSON.stringify(payload);
  }
  return request(`/portfolio/${encodeURIComponent(id)}/add/project/${encodeURIComponent(projectName)}/ai`, opts);
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
 * Uploads a thumbnail image for an analyzed project.
 *
 * @param {string} projectName
 * @param {File} file
 * @returns {Promise<any>}
 */
export function uploadProjectThumbnail(projectName, file) {
  const form = new FormData();
  form.append("thumbnail", file, file.name);
  return request(`/projects/${encodeURIComponent(projectName)}/thumbnail`, { method: "POST", body: form });
}

/**
 * Deletes the thumbnail for an analyzed project.
 *
 * @param {string} projectName
 * @returns {Promise<any>}
 */
export function deleteProjectThumbnail(projectName) {
  return request(`/projects/${encodeURIComponent(projectName)}/thumbnail`, { method: "DELETE" });
}

/**
 * Returns the URL to directly load a project's thumbnail image.
 *
 * @param {string} projectName
 * @returns {string}
 */
export function projectThumbnailUrl(projectName) {
  return `${API_BASE}/projects/${encodeURIComponent(projectName)}/thumbnail/image`;
}

/**
 * Returns a success message and the updated duration created by the start and end dates
 *
 * @param {string} id
 * @param {string} start
 * @param {string} end
 * @returns {string}
 */
export function updateProjectDuration(id, start, end) {
  const query = start && end ? `?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}` : "";
  return request(`/projects/${encodeURIComponent(id)}/duration${query}`, {method: "POST"});
}

  /*
 * Returns a success message and the updated project type
 *
 * @param {string} id
 * @param {string} type
 * @returns {string}
 */
export function updateProjectType(id, type) {
  const query = type ? `?project_type=${encodeURIComponent(type)}` : "";
  return request(`/projects/${encodeURIComponent(id)}/type${query}`, {method: "POST"});
}