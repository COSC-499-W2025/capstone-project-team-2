"use client";

/**
 * Project Management route.
 *
 * Lists all analyzed projects stored on the backend and provides
 * per-project view and delete controls.
 */
import { useEffect, useRef, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { deleteProject, deleteProjectThumbnail, fetchProjectByName, fetchProjects, projectThumbnailUrl, uploadProjectThumbnail } from "../../lib/api";

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
          <span key={x} className="data-chip">
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
            <div className="button-row">
              <span className="data-chip">{item.project_type}</span>
            </div>
          </div>
        ) : null}
        {data?.analysis?.duration_estimate ? (
          <div className="settings-row">
            <span className="settings-label">Duration</span>
            <div className="button-row">
              <span className="data-chip">{data.analysis.duration_estimate}</span>
            </div>
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
  const [openNames, setOpenNames] = useState([]);
  const [viewData, setViewData] = useState({});
  // thumbnail state: { [name]: "loading" | "loaded" | "none" }
  const [thumbState, setThumbState] = useState({});
  // bumped on each successful upload to force browser cache invalidation
  const [thumbVersion, setThumbVersion] = useState({});
  const fileInputRef = useRef(null);
  const thumbUploadTarget = useRef(null);

  async function loadProjects() {
    try {
      const data = await fetchProjects();
      const names = Array.isArray(data) ? data : [];
      setProjects(names);
      // Mark all thumbnails as loading so they attempt to render
      setThumbState(Object.fromEntries(names.map((n) => [n, "loading"])));
    } catch (err) {
      setError(err.message || "Failed to load projects.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  function onThumbClick(name) {
    thumbUploadTarget.current = name;
    fileInputRef.current?.click();
  }

  async function onThumbFileSelected(e) {
    const file = e.target.files?.[0];
    const name = thumbUploadTarget.current;
    e.target.value = "";
    if (!file || !name) return;
    setError("");
    setThumbState((prev) => ({ ...prev, [name]: "loading" }));
    try {
      await uploadProjectThumbnail(name, file);
      setThumbVersion((prev) => ({ ...prev, [name]: (prev[name] ?? 0) + 1 }));
      setThumbState((prev) => ({ ...prev, [name]: "loaded" }));
    } catch (err) {
      setError(err.message || "Thumbnail upload failed.");
      setThumbState((prev) => ({ ...prev, [name]: "none" }));
    }
  }

  async function onThumbDelete(name) {
    setError("");
    try {
      await deleteProjectThumbnail(name);
      setThumbState((prev) => ({ ...prev, [name]: "none" }));
    } catch (err) {
      setError(err.message || "Failed to remove thumbnail.");
    }
  }

  const MAX_OPEN = 3;

  async function onToggleView(name) {
    if (viewing === name) {
      setViewing(null);
      setOpenNames((prev) => prev.filter((n) => n !== name));
      return;
    }
    setViewing(name);
    if (openNames.length >= MAX_OPEN) setOpenNames((prev) => prev.slice(1));
    setOpenNames((prev) => prev.includes(name) ? prev : [...prev, name]);
    if (viewData[name] && !viewData[name]._error) return;
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
            <>
            {/* Hidden file input for thumbnail uploads */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={onThumbFileSelected}
            />
            <div className="settings-list compact">
              {projects.map((name) => (
                <div key={name}>
                  <div className="settings-row">
                    <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                      {/* Thumbnail slot */}
                      <div style={{ position: "relative", flexShrink: 0 }}>
                        <div
                          title="Click to upload thumbnail"
                          onClick={() => onThumbClick(name)}
                          style={{
                            width: 80, height: 80, borderRadius: 5, overflow: "hidden",
                            border: "1px solid var(--layer-border, #ccc)", cursor: "pointer",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            background: "var(--bg-2, #eef1f5)", flexShrink: 0,
                          }}
                        >
                          {thumbState[name] === "loading" || thumbState[name] === "loaded" ? (
                            <img
                              src={`${projectThumbnailUrl(name)}?v=${thumbVersion[name] ?? 0}`}
                              alt={name}
                              style={{ width: "100%", height: "100%", objectFit: "cover" }}
                              onLoad={() => setThumbState((prev) => ({ ...prev, [name]: "loaded" }))}
                              onError={() => setThumbState((prev) => ({ ...prev, [name]: "none" }))}
                            />
                          ) : (
                            <span style={{ fontSize: "0.8rem", color: "var(--ink-1, #515154)", textAlign: "center", lineHeight: 1.2, padding: "0 4px" }}>Click to Add thumbnail</span>
                          )}
                        </div>
                        {thumbState[name] === "loaded" ? (
                          <button
                            type="button"
                            title="Remove thumbnail"
                            onClick={() => onThumbDelete(name)}
                            style={{
                              position: "absolute", top: -6, right: -6,
                              width: 18, height: 18, minHeight: 18, borderRadius: "50%",
                              border: "none", background: "var(--danger, #c0392b)",
                              color: "#fff", fontSize: "0.65rem", cursor: "pointer",
                              display: "flex", alignItems: "center", justifyContent: "center",
                              lineHeight: 1, padding: 0,
                            }}
                          >✕</button>
                        ) : null}
                      </div>
                      <span className="settings-label" style={{ fontSize: "1rem", fontWeight: 500 }}>{name}</span>
                    </div>
                    <div className="button-row">
                      <button
                        type="button"
                        className="liquid-btn solid btn-success"
                        onClick={() => onToggleView(name)}
                      >
                        {openNames.includes(name) ? "Hide" : "View"}
                      </button>
                       {confirmDelete === name ? (
                          <>
                            <button
                              type="button"
                              className="liquid-btn btn-danger"
                              disabled={busy}
                              onClick={() => onDelete(name)}
                            >
                              Confirm delete
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
                          className="liquid-btn btn-danger"
                          disabled={busy}
                          onClick={() => setConfirmDelete(name)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                  {openNames.includes(name) ? (
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
            </>
          )}
        </GlassCard>
      </div>
    </LiquidShell>
  );
}
