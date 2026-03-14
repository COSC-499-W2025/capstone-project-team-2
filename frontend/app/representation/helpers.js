/**
 * Shared representation preference defaults used by the route and tests.
 */
export const DEFAULT_REPRESENTATION_PREFERENCES = {
  project_order: [],
  chronology_corrections: {},
  comparison_attributes: ["languages", "frameworks", "duration_estimate"],
  highlight_skills: [],
  showcase_projects: []
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
  const merged = [];
  for (const name of Array.isArray(preferred) ? preferred : []) {
    if (name && !merged.includes(name)) merged.push(name);
  }
  for (const project of Array.isArray(projects) ? projects : []) {
    const name = project?.project_name;
    if (name && !merged.includes(name)) merged.push(name);
  }
  return merged;
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
      inputs[projectName] = String(value.analyzed_at);
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
    if (cleaned) payload[projectName] = { analyzed_at: cleaned };
  }
  return payload;
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
