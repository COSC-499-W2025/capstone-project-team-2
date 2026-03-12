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
import { fetchProjectInsights } from "../../lib/api";

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
 * Produces a rank score for project ordering.
 *
 * @param {any} project
 * @returns {number}
 */
function scoreProject(project) {
  const stats = project?.stats || {};
  const topCount = Number(stats.top_contribution_count || 0);
  const topPct = Number(stats.top_contribution_percentage || 0);
  const skillCount = Number(stats.skill_count || (project.skills || []).length || 0);
  return topCount * 100 + topPct + skillCount * 3;
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
              <th key={m}>{m}</th>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        const data = await fetchProjectInsights();
        if (!ignore) setProjects(Array.isArray(data) ? data : []);
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

  const sortedDates = projects.map((p) => parseDate(p.analyzed_at)).filter(Boolean).sort((a, b) => b - a);
  const latestDate = sortedDates[0] ? sortedDates[0].toISOString().slice(0, 10) : "Unknown";
  const uniqueSkills = new Set(projects.flatMap((p) => (Array.isArray(p.skills) ? p.skills : [])));
  const topProjects = [...projects].sort((a, b) => scoreProject(b) - scoreProject(a)).slice(0, 3);

  return (
    <LiquidShell
      title="Dashboard"
      subtitle="Timeline, activity heatmap, and top projects from project insight history."
    >
      <div className="page-stack">
        {loading ? <p className="muted">Loading insights...</p> : null}
        {error ? <p className="error">{error}</p> : null}

        {!loading && !error ? (
          <>
            <div className="grid three-col">
              <GlassCard title="Projects">
                <p className="metric-value">{projects.length}</p>
              </GlassCard>
              <GlassCard title="Unique Skills">
                <p className="metric-value">{uniqueSkills.size}</p>
              </GlassCard>
              <GlassCard title="Latest Analysis">
                <p className="metric-value metric-date">{latestDate}</p>
              </GlassCard>
            </div>

            <div className="grid two-col">
              <GlassCard title="Skills Timeline" hint="Project-level skill count progression.">
                <TimelineBars projects={projects} />
              </GlassCard>
              <GlassCard title="Activity Heatmap" hint="Code, test, design, document, and other buckets.">
                <ActivityHeatmap projects={projects} />
              </GlassCard>
            </div>

            <GlassCard title="Top 3 Projects" hint="Ranked by contribution and skill signal.">
              <div className="grid three-col">
                {topProjects.length ? (
                  topProjects.map((project, index) => (
                    <div className="sub-card" key={`${project.project_name || "project"}-${index}`}>
                      <h3>{project.project_name || "Unknown"}</h3>
                      <p className="muted">{String(project.project_type || "unknown")}</p>
                      <p>{String(project.summary || "No summary available.").slice(0, 220)}</p>
                      <p className="hint">Skills: {(project.skills || []).length}</p>
                    </div>
                  ))
                ) : (
                  <p className="muted">No projects available.</p>
                )}
              </div>
            </GlassCard>
          </>
        ) : null}
      </div>
    </LiquidShell>
  );
}
