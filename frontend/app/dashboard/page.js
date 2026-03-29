"use client";

/**
 * Dashboard route module.
 *
 * This file combines:
 * - lightweight data classification helpers,
 * - visualization components for trends/heatmaps,
 * - and page-level insight orchestration.
 */
import { useEffect, useMemo, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { LiquidSegmentedControl } from "../../components/LiquidPillControl";
import { fetchRepresentationProjects, fetchTopProjectHistories } from "../../lib/api";

/**
 * Extension and naming heuristics used to classify hierarchy files
 * into reporting buckets.
 */
const CODE_EXTENSIONS = new Set([
  ".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".c", ".cpp", ".h", ".hpp",
  ".cs", ".go", ".rb", ".php", ".swift", ".kt", ".rs", ".sql", ".sh"
]);
/** Path/name patterns that strongly indicate test artifacts. */
const TEST_HINTS = ["/test/", "/tests/", "_test.", "test_", "spec."];
/** Path/name patterns that strongly indicate design assets or UX files. */
const DESIGN_HINTS = ["/design", "/ui", "/ux", "figma", "sketch", "wireframe", "mockup"];
/** Path/name patterns that strongly indicate documentation artifacts. */
const DOC_HINTS = ["/doc", "/docs", "readme", "report", "notes"];
/** File extensions considered design-oriented in heatmap categorization. */
const DESIGN_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".fig"]);
/** File extensions considered documentation-oriented in categorization. */
const DOC_EXTENSIONS = new Set([".md", ".txt", ".pdf", ".doc", ".docx", ".ppt", ".pptx"]);
/** Render order and labels for activity heatmap rows. */
const ACTIVITY_TYPES = ["code", "test", "design", "document", "other"];
const DASHBOARD_MODE_KEY = "dashboardMode";

/**
 * Parses an ISO-like date string safely.
 *
 * @param {string} value
 * @returns {Date | null}
 */
function parseDate(value) {
  if (!value || typeof value !== "string") return null;
  const d = new Date(value);
  return Number.isNaN(d.valueOf()) ? null : d;
}

/**
 * Formats a timestamp into YYYY-MM granularity.
 *
 * @param {string} value
 * @returns {string}
 */
function getMonth(value) {
  const d = parseDate(value);
  if (!d) return "";
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/**
 * Recursively flattens hierarchy nodes into path/node tuples.
 *
 * @param {any} node
 * @param {string} [prefix=""]
 * @returns {[string, any][]}
 */
function flattenFiles(node, prefix = "") {
  if (!node || typeof node !== "object") return [];
  const name = String(node.name || "");
  const path = prefix ? `${prefix}/${name}` : name;
  const children = Array.isArray(node.children) ? node.children : [];
  const isDir = String(node.type || "").toUpperCase() === "DIR";

  let items = [];
  if (!isDir) items.push([path, node]);
  for (const child of children) {
    items = items.concat(flattenFiles(child, path));
  }
  return items;
}

/**
 * Assigns a file path into an activity bucket for heatmap reporting.
 *
 * @param {string} path
 * @param {string} [nodeType=""]
 * @returns {"code" | "test" | "design" | "document" | "other"}
 */
function classify(path, nodeType = "") {
  const lower = path.toLowerCase();
  const ext = lower.includes(".") ? lower.slice(lower.lastIndexOf(".")) : "";
  const type = String(nodeType).toLowerCase();

  if (TEST_HINTS.some((hint) => lower.includes(hint))) return "test";
  if (DESIGN_HINTS.some((hint) => lower.includes(hint)) || DESIGN_EXTENSIONS.has(ext)) return "design";
  if (DOC_HINTS.some((hint) => lower.includes(hint)) || DOC_EXTENSIONS.has(ext)) return "document";
  if (CODE_EXTENSIONS.has(ext) || CODE_EXTENSIONS.has(`.${type}`)) return "code";
  return "other";
}

/**
 * Formats an evolution date range for the top-project card.
 *
 * @param {any} evolution
 * @returns {string}
 */
function formatEvolutionDateRange(evolution) {
  const first = evolution?.first_analyzed_at ? String(evolution.first_analyzed_at).slice(0, 10) : "";
  const latest = evolution?.latest_analyzed_at ? String(evolution.latest_analyzed_at).slice(0, 10) : "";
  if (!first && !latest) return "No history dates available.";
  if (first && latest && first !== latest) return `${first} to ${latest}`;
  return first || latest;
}

/**
 * Builds short, readable evolution evidence lines for one top project.
 *
 * @param {any} item
 * @returns {string[]}
 */
function buildEvolutionHighlights(item) {
  const evolution = item?.evolution || {};
  const snapshotCount = Number(item?.snapshot_count || 0);
  const highlights = [];

  if (snapshotCount > 1) {
    highlights.push(`${snapshotCount} snapshots across ${formatEvolutionDateRange(evolution)}`);
  } else {
    highlights.push("No evolution history yet");
  }

  if (Array.isArray(evolution.new_skills) && evolution.new_skills.length) {
    highlights.push(`Added skills: ${evolution.new_skills.slice(0, 3).join(", ")}`);
  }

  if (Array.isArray(evolution.new_languages) && evolution.new_languages.length) {
    highlights.push(`Expanded languages: ${evolution.new_languages.slice(0, 3).join(", ")}`);
  }

  if (Number.isFinite(evolution.file_count_delta) && evolution.file_count_delta > 0) {
    highlights.push(`File count grew by ${evolution.file_count_delta}`);
  }

  if (evolution.summary_changed) {
    highlights.push("Project summary changed over time");
  }

  if (evolution.project_type_changed) {
    highlights.push("Project type changed across snapshots");
  }

  return highlights;
}

/**
 * Normalizes project names before comparing API payloads from different sources.
 *
 * @param {any} value
 * @returns {string}
 */
function normalizeProjectName(value) {
  return String(value || "").trim().toLowerCase();
}

/**
 * Produces a rank score for project ordering.
 *
 * @param {any} project
 * @returns {number}
 */
function scoreProject(project, weights = { countWeight: 100, percentWeight: 1, skillWeight: 3 }) {
  const stats = project?.stats || {};
  const topCount = Number(stats.top_contribution_count || 0);
  const topPct = Number(stats.top_contribution_percentage || 0);
  const skillCount = Number(stats.skill_count || (project.skills || []).length || 0);
  return topCount * weights.countWeight + topPct * weights.percentWeight + skillCount * weights.skillWeight;
}

/**
 * Renders timeline bars for skill-count progression over time.
 *
 * @param {{ projects: any[] }} props
 * @returns {JSX.Element}
 */
function TimelineBars({ projects }) {
  const rows = useMemo(() => {
    return projects
      .map((p) => ({
        name: p.project_name || "Unknown",
        date: parseDate(p.analyzed_at),
        skillCount: Array.isArray(p.skills) ? p.skills.length : 0
      }))
      .filter((x) => x.date)
      .sort((a, b) => a.date - b.date);
  }, [projects]);

  const maxValue = Math.max(1, ...rows.map((r) => r.skillCount));

  if (!rows.length) {
    return <p className="muted">No timeline data available.</p>;
  }

  return (
    <div className="mini-chart">
      {rows.map((row) => (
        <div className="mini-bar-row" key={`${row.name}-${row.date.toISOString()}`}>
          <span className="bar-label">{row.date.toISOString().slice(0, 10)}</span>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(row.skillCount / maxValue) * 100}%` }} />
          </div>
          <span className="bar-value">{row.skillCount}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Renders a month/activity matrix based on analyzed hierarchy files.
 *
 * @param {{ projects: any[] }} props
 * @returns {JSX.Element}
 */
function ActivityHeatmap({ projects }) {
  const matrix = useMemo(() => {
    const months = [];
    const map = {};

    for (const project of projects) {
      const month = getMonth(project?.analyzed_at);
      if (!month) continue;
      if (!months.includes(month)) months.push(month);
      if (!map[month]) map[month] = { code: 0, test: 0, design: 0, document: 0, other: 0 };

      const hierarchy = project?.hierarchy;
      if (hierarchy && typeof hierarchy === "object") {
        for (const [path, node] of flattenFiles(hierarchy)) {
          const bucket = classify(path, node?.type);
          map[month][bucket] += 1;
        }
      }
    }

    months.sort();
    return { months, map };
  }, [projects]);

  if (!matrix.months.length) return <p className="muted">No hierarchy data for heatmap.</p>;

  return (
    <div className="heatmap-table-wrap">
      <table className="heatmap-table">
        <thead>
          <tr>
            <th>Activity</th>
            {matrix.months.map((m) => (
              <th key={m}>{m} (count)</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ACTIVITY_TYPES.map((activity) => (
            <tr key={activity}>
              <td>{activity}</td>
              {matrix.months.map((month) => {
                const value = matrix.map[month]?.[activity] || 0;
                return (
                  <td key={`${activity}-${month}`} data-intensity={Math.min(5, Math.ceil(value / 4))}>
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Dashboard route showing project insights, trends, and top projects.
 *
 * @returns {JSX.Element}
 */
export default function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [highlightSkills, setHighlightSkills] = useState([]);
  const [showcaseProjects, setShowcaseProjects] = useState([]);
  const [topProjectHistories, setTopProjectHistories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mode, setMode] = useState("private");
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [skillFilter, setSkillFilter] = useState("all");
  const [topProjectCount, setTopProjectCount] = useState(3);
  const [countWeight, setCountWeight] = useState(100);
  const [percentWeight, setPercentWeight] = useState(1);
  const [skillWeight, setSkillWeight] = useState(3);
  const [showTimeline, setShowTimeline] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showTopProjects, setShowTopProjects] = useState(true);
  const [isDockOpen, setIsDockOpen] = useState(false);
  const [hasHydratedMode, setHasHydratedMode] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(DASHBOARD_MODE_KEY);
    if (stored === "private" || stored === "public") {
      setMode(stored);
    }
    setHasHydratedMode(true);
  }, []);

  useEffect(() => {
    if (!hasHydratedMode) return;
    window.localStorage.setItem(DASHBOARD_MODE_KEY, mode);
  }, [mode, hasHydratedMode]);

  useEffect(() => {
    if (mode === "public" && isDockOpen) setIsDockOpen(false);
  }, [mode, isDockOpen]);

  useEffect(() => {
    if (!isDockOpen) return undefined;
    function onKeyDown(event) {
      if (event.key === "Escape") setIsDockOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isDockOpen]);

  useEffect(() => {
    let ignore = false;
    /**
     * Fetches insight history and normalizes it into array state.
     * Includes unmount guard to avoid stale state writes.
     *
     * @returns {Promise<void>}
     */
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [representationPayload, historyPayload] = await Promise.all([
          fetchRepresentationProjects(),
          fetchTopProjectHistories({ topN: 10, activeOnly: true })
        ]);
        if (!ignore) {
          const currentProjects = Array.isArray(representationPayload?.projects) ? representationPayload.projects : [];
          const currentProjectSet = new Set(currentProjects.map((item) => normalizeProjectName(item?.project_name)));
          setProjects(currentProjects);
          setHighlightSkills(Array.isArray(representationPayload?.highlight_skills) ? representationPayload.highlight_skills : []);
          setShowcaseProjects(Array.isArray(representationPayload?.showcase_projects) ? representationPayload.showcase_projects : []);
          setTopProjectHistories(
            (Array.isArray(historyPayload) ? historyPayload : [])
              .filter((item) => currentProjectSet.has(normalizeProjectName(item?.project_name)))
          );
        }
      } catch (err) {
        if (!ignore) setError(err.message || "Failed to load insights.");
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
    return () => {
      ignore = true;
    };
  }, []);

  const availableTypes = useMemo(() => {
    return Array.from(new Set(projects.map((p) => String(p.project_type || "unknown")))).sort();
  }, [projects]);

  const availableSkills = useMemo(() => {
    return Array.from(new Set(projects.flatMap((p) => (Array.isArray(p.skills) ? p.skills : [])))).sort();
  }, [projects]);

  const historyByProject = useMemo(() => {
    return new Map(topProjectHistories.map((item) => [normalizeProjectName(item?.project_name), item]));
  }, [topProjectHistories]);

  const projectNameSuggestions = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    const names = Array.from(
      new Set(projects.map((project) => String(project?.project_name || "").trim()).filter(Boolean))
    ).sort((a, b) => a.localeCompare(b));
    if (!normalizedQuery) return names.slice(0, 8);
    return names.filter((name) => name.toLowerCase().includes(normalizedQuery)).slice(0, 8);
  }, [projects, searchQuery]);

  const filteredProjects = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    return projects.filter((project) => {
      const name = String(project.project_name || "").toLowerCase();
      const summary = String(project.summary || "").toLowerCase();
      const pType = String(project.project_type || "unknown");
      const pSkills = Array.isArray(project.skills) ? project.skills : [];

      const queryMatch = !normalizedQuery || name.includes(normalizedQuery) || summary.includes(normalizedQuery);
      const typeMatch = typeFilter === "all" || pType === typeFilter;
      const skillMatch = skillFilter === "all" || pSkills.includes(skillFilter);
      return queryMatch && typeMatch && skillMatch;
    });
  }, [projects, searchQuery, typeFilter, skillFilter]);

  const sortedDates = filteredProjects.map((p) => parseDate(p.analyzed_at)).filter(Boolean).sort((a, b) => b - a);
  const latestDate = sortedDates[0] ? sortedDates[0].toISOString().slice(0, 10) : "Unknown";
  const uniqueSkills = new Set(filteredProjects.flatMap((p) => (Array.isArray(p.skills) ? p.skills : [])));
  const scoringWeights = mode === "private"
    ? { countWeight, percentWeight, skillWeight }
    : { countWeight: 100, percentWeight: 1, skillWeight: 3 };
  const effectiveTopCount = mode === "private" ? Math.max(1, Math.min(10, Number(topProjectCount) || 3)) : 3;
  const showcaseSet = new Set(showcaseProjects);
  const showcasedProjectsInOrder = filteredProjects.filter((project) => showcaseSet.has(project.project_name));
  const nonShowcasedProjects = filteredProjects.filter((project) => !showcaseSet.has(project.project_name));
  const rankedProjects = [...filteredProjects].sort(
    (a, b) => scoreProject(b, scoringWeights) - scoreProject(a, scoringWeights)
  );
  const rankedNonShowcased = [...nonShowcasedProjects].sort(
    (a, b) => scoreProject(b, scoringWeights) - scoreProject(a, scoringWeights)
  );
  const topProjects = (mode === "public"
    ? (showcasedProjectsInOrder.length ? showcasedProjectsInOrder : filteredProjects)
    : (showcasedProjectsInOrder.length ? [...showcasedProjectsInOrder, ...rankedNonShowcased] : rankedProjects)
  ).slice(0, effectiveTopCount);
  const showTimelinePanel = mode === "private" ? showTimeline : true;
  const showHeatmapPanel = mode === "private" ? showHeatmap : true;
  const showTopProjectsPanel = mode === "private" ? showTopProjects : true;

  return (
    <LiquidShell
      title="Dashboard"
      subtitle="Timeline, activity heatmap, and top projects from project insight history."
    >
      <div className="page-stack">
        <div className="button-row" style={{ justifyContent: "flex-start" }}>
          <LiquidSegmentedControl
            ariaLabel="Dashboard mode"
            options={[
              { value: "private", label: "Private" },
              { value: "public", label: "Public" }
            ]}
            value={mode}
            onChange={setMode}
          />
        </div>

        <div className="sub-card dashboard-inline-search-row">
          <label className="dashboard-inline-search-field">
            <span className="dashboard-inline-search-label">Search</span>
            <input
              className="settings-control"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Find by project name or summary"
              list="dashboard-project-suggestions"
            />
            <datalist id="dashboard-project-suggestions">
              {projectNameSuggestions.map((projectName) => (
                <option key={projectName} value={projectName} />
              ))}
            </datalist>
          </label>
          <label className="dashboard-inline-select-field">
            <span className="dashboard-inline-search-label">Type</span>
            <select className="settings-control" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
              <option value="all">All</option>
              {availableTypes.map((projectType) => (
                <option key={projectType} value={projectType}>{projectType}</option>
              ))}
            </select>
          </label>
          <label className="dashboard-inline-select-field">
            <span className="dashboard-inline-search-label">Skill</span>
            <select className="settings-control" value={skillFilter} onChange={(event) => setSkillFilter(event.target.value)}>
              <option value="all">All</option>
              {availableSkills.map((skill) => (
                <option key={skill} value={skill}>{skill}</option>
              ))}
            </select>
          </label>
          {mode === "private" ? (
            <button
              type="button"
              className="liquid-btn solid"
              aria-expanded={isDockOpen}
              aria-controls="dashboard-filter-modal"
              onClick={() => setIsDockOpen((prev) => !prev)}
            >
              {isDockOpen ? "Close Filters" : "Open Filters"}
            </button>
          ) : null}
        </div>

        {loading ? <p className="muted">Loading insights...</p> : null}
        {error ? <p className="error">{error}</p> : null}

        {!loading && !error ? (
          <>
            <div className="grid three-col">
              <GlassCard title="Projects">
                <p className="metric-value">{filteredProjects.length}</p>
              </GlassCard>
              <GlassCard title="Unique Skills">
                <p className="metric-value">{uniqueSkills.size}</p>
              </GlassCard>
              <GlassCard title="Latest Analysis">
                <p className="metric-value metric-date">{latestDate}</p>
              </GlassCard>
            </div>

            {highlightSkills.length ? (
              <GlassCard title="Highlighted Skills" hint="Configured in Project Settings and emphasized in showcase cards.">
                <div className="button-row">
                  {highlightSkills.map((skill) => (
                    <span key={skill} className="data-chip">{skill}</span>
                  ))}
                </div>
              </GlassCard>
            ) : null}

            {showTimelinePanel || showHeatmapPanel ? (
              <div className="grid two-col">
                {showTimelinePanel ? (
                  <GlassCard title="Skills Timeline" hint="Project-level skill count progression.">
                    <TimelineBars projects={filteredProjects} />
                  </GlassCard>
                ) : null}
                {showHeatmapPanel ? (
                  <GlassCard title="Activity Heatmap" hint="Code, test, design, document, and other buckets. Values are counts of detected artifacts for the selected month.">
                    <ActivityHeatmap projects={filteredProjects} />
                  </GlassCard>
                ) : null}
              </div>
            ) : null}

            {showTopProjectsPanel ? (
              <GlassCard
                title={`Top ${effectiveTopCount} Projects`}
                hint={showcasedProjectsInOrder.length
                  ? "Showcase selections from Project Settings are prioritized, with evolution evidence shown when available."
                  : "Ranked by contribution and skill signal, with evolution evidence shown when available."}
              >
                <div className="grid three-col">
                  {topProjects.length ? (
                    topProjects.map((project, index) => {
                      const historyItem = historyByProject.get(normalizeProjectName(project?.project_name));
                      const evolutionHighlights = buildEvolutionHighlights(historyItem);
                      return (
                        <div className="sub-card" key={`${project.project_name || "project"}-${index}`}>
                          <h3>{project.project_name || "Unknown"}</h3>
                          <p className="muted">{String(project.project_type || "unknown")}</p>
                          <p>{String(project.summary || "No summary available.").slice(0, 220)}</p>
                          {highlightSkills.length ? (
                            <p className="hint">
                              Highlighted: {
                                (Array.isArray(project.skills) ? project.skills : [])
                                  .filter((skill) => highlightSkills.includes(skill))
                                  .join(", ") || "None"
                              }
                            </p>
                          ) : null}
                          <p className="hint">Skills: {(project.skills || []).length}</p>
                          <div className="settings-list compact">
                            {evolutionHighlights.map((line) => (
                              <div className="settings-row" key={`${project.project_name || "project"}-${line}`}>
                                <span className="settings-value">{line}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <p className="muted">No projects available.</p>
                  )}
                </div>
              </GlassCard>
            ) : null}

            {mode === "private" ? (
              <>
                <div
                  className={`dashboard-drawer-backdrop ${isDockOpen ? "open" : ""}`.trim()}
                  onClick={() => setIsDockOpen(false)}
                  aria-hidden={!isDockOpen}
                />
                <aside
                  id="dashboard-filter-modal"
                  className={`dashboard-drawer glass-panel ${isDockOpen ? "open" : ""}`.trim()}
                  role="dialog"
                  aria-modal="true"
                  aria-label="Dashboard controls"
                  aria-hidden={!isDockOpen}
                  onClick={(event) => event.stopPropagation()}
                >
                  <div className="dashboard-drawer-header">
                    <h3>Filters & Controls</h3>
                    <button type="button" className="liquid-btn btn-danger" onClick={() => setIsDockOpen(false)}>
                      Close
                    </button>
                  </div>
                  <p className="muted">Popup controls for dashboard tuning.</p>
                  <p className="dashboard-results-summary">Results: {filteredProjects.length} / {projects.length}</p>
                  <div className="dashboard-filter-grid">
                    <div className="sub-card dashboard-filter-card dashboard-ranking-card">
                      <p className="dashboard-filter-title">Ranking</p>
                      <div className="settings-list compact">
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Top projects shown</span>
                          <input
                            className="settings-control"
                            type="number"
                            min={1}
                            max={10}
                            value={topProjectCount}
                            onChange={(event) => setTopProjectCount(event.target.value)}
                          />
                        </label>
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Contribution count weight</span>
                          <input
                            className="settings-control"
                            type="number"
                            min={0}
                            value={countWeight}
                            onChange={(event) => setCountWeight(Number(event.target.value))}
                          />
                        </label>
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Contribution percent weight</span>
                          <input
                            className="settings-control"
                            type="number"
                            min={0}
                            value={percentWeight}
                            onChange={(event) => setPercentWeight(Number(event.target.value))}
                          />
                        </label>
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Skill count weight</span>
                          <input
                            className="settings-control"
                            type="number"
                            min={0}
                            value={skillWeight}
                            onChange={(event) => setSkillWeight(Number(event.target.value))}
                          />
                        </label>
                      </div>
                    </div>
                    <div className="sub-card dashboard-filter-card dashboard-visibility-card">
                      <p className="dashboard-filter-title">Visibility</p>
                      <div className="settings-list compact">
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Show Skills Timeline</span>
                          <input type="checkbox" checked={showTimeline} onChange={(event) => setShowTimeline(event.target.checked)} />
                        </label>
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Show Activity Heatmap</span>
                          <input type="checkbox" checked={showHeatmap} onChange={(event) => setShowHeatmap(event.target.checked)} />
                        </label>
                        <label className="settings-row settings-field-row">
                          <span className="settings-label">Show Top Projects</span>
                          <input type="checkbox" checked={showTopProjects} onChange={(event) => setShowTopProjects(event.target.checked)} />
                        </label>
                      </div>
                    </div>
                  </div>
                </aside>
              </>
            ) : null}
          </>
        ) : null}
      </div>
    </LiquidShell>
  );
}
