/**
 * Shared representation preference defaults used by the route and tests.
 */
export const DEFAULT_REPRESENTATION_PREFERENCES = {
  project_order: [],
  chronology_corrections: {},
  comparison_attributes: ["languages", "frameworks", "duration_estimate"],
  highlight_skills: [],
  showcase_projects: [],
  project_overrides: {}
};

/**
 * Ensures a full representation preference object shape exists.
 *
 * @param {unknown} data
 * @returns {Record<string, any>}
 */
export function normalizeRepresentationPreferences(data) {
  return {
    ...DEFAULT_REPRESENTATION_PREFERENCES,
    ...(data && typeof data === "object" ? data : {})
  };
}

/**
 * Merges saved project order with currently available projects.
 *
 * Existing ordered names stay first, and newly discovered project names
 * are appended once in backend order.
 *
 * @param {string[]} preferred
 * @param {Array<{ project_name?: string }>} projects
 * @returns {string[]}
 */
export function mergeProjectOrder(preferred, projects) {
  const available = new Set(
    (Array.isArray(projects) ? projects : [])
      .map((project) => project?.project_name)
      .filter(Boolean)
  );
  const merged = [];
  for (const name of Array.isArray(preferred) ? preferred : []) {
    if (name && available.has(name) && !merged.includes(name)) merged.push(name);
  }
  for (const project of Array.isArray(projects) ? projects : []) {
    const name = project?.project_name;
    if (name && !merged.includes(name)) merged.push(name);
  }
  return merged;
}

/**
 * Filters a saved project-name list against currently available projects.
 *
 * Preserves input order while dropping deleted/missing names and duplicates.
 *
 * @param {string[]} selected
 * @param {Array<{ project_name?: string }>} projects
 * @returns {string[]}
 */
export function filterAvailableProjects(selected, projects) {
  const available = new Set(
    (Array.isArray(projects) ? projects : [])
      .map((project) => project?.project_name)
      .filter(Boolean)
  );
  const filtered = [];
  for (const name of Array.isArray(selected) ? selected : []) {
    if (name && available.has(name) && !filtered.includes(name)) filtered.push(name);
  }
  return filtered;
}

/**
 * Converts a comma-separated skill input into a normalized array.
 *
 * @param {string} value
 * @returns {string[]}
 */
export function parseListInput(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

/**
 * Flattens stored chronology corrections for form input rendering.
 *
 * @param {Record<string, { analyzed_at?: string }>} corrections
 * @returns {Record<string, string>}
 */
export function formatChronologyInputs(corrections) {
  const inputs = {};
  if (!corrections || typeof corrections !== "object") return inputs;
  for (const [projectName, value] of Object.entries(corrections)) {
    if (value && typeof value === "object" && value.analyzed_at) {
      const formatted = toDateTimeLocalValue(String(value.analyzed_at));
      if (formatted) inputs[projectName] = formatted;
    }
  }
  return inputs;
}

/**
 * Converts chronology input fields into the backend payload shape.
 *
 * Blank values are omitted so they do not overwrite stored entries.
 *
 * @param {Record<string, string>} inputs
 * @returns {Record<string, { analyzed_at: string }>}
 */
export function buildChronologyPayload(inputs) {
  const payload = {};
  for (const [projectName, value] of Object.entries(inputs || {})) {
    const cleaned = String(value || "").trim();
    if (!cleaned) continue;

    const isoValue = toIsoDateTimeValue(cleaned);
    if (!isoValue) {
      throw new Error(`Enter a valid date and time for ${projectName}.`);
    }
    payload[projectName] = { analyzed_at: isoValue };
  }
  return payload;
}

/**
 * Converts a stored timestamp into an HTML `datetime-local` field value.
 *
 * @param {string} value
 * @returns {string}
 */
export function toDateTimeLocalValue(value) {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "";

  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
}

/**
 * Converts an HTML `datetime-local` field value into an ISO timestamp.
 *
 * @param {string} value
 * @returns {string}
 */
export function toIsoDateTimeValue(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "" : date.toISOString();
}

/**
 * Formats stored analyzed timestamps for card display.
 *
 * @param {string} value
 * @returns {string}
 */
export function formatDateLabel(value) {
  if (!value) return "Unknown date";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}
