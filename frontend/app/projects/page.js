"use client";

/**
 * Project Management route.
 *
 * Lists all analyzed projects stored on the backend and provides
 * per-project view and delete controls.
 */
import { useEffect, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { deleteProject, fetchProjectByName, fetchProjects } from "../../lib/api";

/**
 * Inline detail panel showing human-readable fields from a project's resume_item.
 *
 * @param {{ data: any }} props
 * @returns {JSX.Element}
 */
function ProjectDetail({ data }) {
  const item = data?.analysis?.resume_item ?? data?.analysis ?? {};

  const chips = (arr) =>
    Array.isArray(arr) && arr.length
      ? arr.map((x) => (
          <span key={x} className="liquid-btn" style={{ cursor: "default", fontSize: "0.8rem", padding: "2px 10px" }}>
            {x}
          </span>
        ))
      : <span className="muted">None</span>;

  return (
    <div className="form-stack" style={{ marginTop: "0.75rem" }}>
      {item.summary ? (
        <div>
          <p className="hint" style={{ marginBottom: "0.25rem" }}>Summary</p>
          <p>{item.summary}</p>
        </div>
      ) : null}

      {Array.isArray(item.highlights) && item.highlights.length ? (
        <div>
          <p className="hint" style={{ marginBottom: "0.25rem" }}>Highlights</p>
          <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {item.highlights.map((h, i) => <li key={i}>{h}</li>)}
          </ul>
        </div>
      ) : null}

      <div className="settings-list compact" style={{ marginTop: "0.25rem" }}>
        {item.languages?.length ? (
          <div className="settings-row">
            <span className="settings-label">Languages</span>
            <div className="button-row">{chips(item.languages)}</div>
          </div>
        ) : null}
        {item.frameworks?.length ? (
          <div className="settings-row">
            <span className="settings-label">Frameworks</span>
            <div className="button-row">{chips(item.frameworks)}</div>
          </div>
        ) : null}
        {item.skills?.length ? (
          <div className="settings-row">
            <span className="settings-label">Skills</span>
            <div className="button-row">{chips(item.skills)}</div>
          </div>
        ) : null}
        {item.project_type ? (
          <div className="settings-row">
            <span className="settings-label">Project type</span>
            <span className="settings-value">{item.project_type}</span>
          </div>
        ) : null}
        {data?.analysis?.duration_estimate ? (
          <div className="settings-row">
            <span className="settings-label">Duration</span>
            <span className="settings-value">{data.analysis.duration_estimate}</span>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/**
 * Project management page.
 *
 * @returns {JSX.Element}
 */
export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [viewing, setViewing] = useState(null);
  const [viewData, setViewData] = useState({});

  async function loadProjects() {
    try {
      const data = await fetchProjects();
      setProjects(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function onToggleView(name) {
    if (viewing === name) {
      setViewing(null);
      return;
    }
    setViewing(name);
    if (viewData[name]) return;
    try {
      const data = await fetchProjectByName(name);
      setViewData((prev) => ({ ...prev, [name]: data }));
    } catch (err) {
      setViewData((prev) => ({ ...prev, [name]: { _error: err.message || "Failed to load." } }));
    }
  }

  async function onDelete(projectName) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await deleteProject(projectName);
      setMessage(`Project "${projectName}" deleted.`);
      setConfirmDelete(null);
      if (viewing === projectName) setViewing(null);
      const data = await fetchProjects();
      setProjects(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Delete failed.");
      setConfirmDelete(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <LiquidShell
      title="Project Management"
      subtitle="View and manage all analyzed projects stored on the backend."
    >
      <div className="page-stack">
        <GlassCard title="Analyzed Projects" hint="Projects available for use in resumes and portfolios.">
          {error ? <p className="error">{error}</p> : null}
          {message ? <p className="success">{message}</p> : null}
          {loading ? (
            <p className="muted">Loading...</p>
          ) : projects.length === 0 ? (
            <p className="muted">No analyzed projects found. Upload and analyze a project first.</p>
          ) : (
            <div className="settings-list compact">
              {projects.map((name) => (
                <div key={name}>
                  <div className="settings-row">
                    <span className="settings-label" style={{ fontSize: "1rem", fontWeight: 500 }}>{name}</span>
                    <div className="button-row">
                      <button
                        type="button"
                        className="liquid-btn"
                        onClick={() => onToggleView(name)}
                      >
                        {viewing === name ? "Hide" : "View"}
                      </button>
                      {confirmDelete === name ? (
                        <>
                          <button
                            type="button"
                            className="liquid-btn solid"
                            disabled={busy}
                            onClick={() => onDelete(name)}
                          >
                            Confirm Delete
                          </button>
                          <button
                            type="button"
                            className="liquid-btn"
                            disabled={busy}
                            onClick={() => setConfirmDelete(null)}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          className="liquid-btn"
                          disabled={busy}
                          onClick={() => setConfirmDelete(name)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                  {viewing === name ? (
                    viewData[name]?._error ? (
                      <p className="error" style={{ marginLeft: "1rem" }}>{viewData[name]._error}</p>
                    ) : viewData[name] ? (
                      <ProjectDetail data={viewData[name]} />
                    ) : (
                      <p className="muted" style={{ marginLeft: "1rem" }}>Loading...</p>
                    )
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </LiquidShell>
  );
}
