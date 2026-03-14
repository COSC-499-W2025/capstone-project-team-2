"use client";

/**
 * Workspace route module.
 *
 * This file contains:
 * - shared editor/preview subcomponents for resume and portfolio documents,
 * - document lifecycle handlers (generate/load/delete/edit/render),
 * - and mode-aware rendering for private/public access behavior.
 */
import { useEffect, useMemo, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { LiquidSegmentedControl } from "../../components/LiquidPillControl";
import {
  addPortfolioProject,
  addResumeEducation,
  addResumeExperience,
  addResumeProject,
  deletePortfolio,
  deleteResume,
  editPortfolio,
  editResume,
  fetchPortfolio,
  fetchProjects,
  getPortfolioShowcaseRole,
  fetchResume,
  generatePortfolio,
  generateResume,
  removePortfolioProject,
  removeResumeEducation,
  removeResumeExperience,
  renderPortfolio,
  renderResume,
  setPortfolioShowcaseRole
} from "../../lib/api";

/**
 * Theme identifiers supported by backend document rendering.
 * @type {string[]}
 */
const THEMES = ["sb2nov", "classic", "moderncv", "engineeringresumes", "engineeringclassic"];
/**
 * Export formats supported by backend render endpoints.
 * @type {string[]}
 */
const FORMATS = ["pdf", "html", "markdown"];

/**
 * Triggers a browser download for a generated Blob.
 *
 * @param {Blob} blob
 * @param {string} filename
 * @returns {void}
 */
function downloadBlob(blob, filename) {
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(href);
}

/**
 * Normalizes date-like values into YYYY-MM format for month inputs.
 *
 * @param {string} input
 * @returns {string}
 */
function toMonthValue(input) {
  if (!input) return "";
  return String(input).slice(0, 7);
}

/**
 * Public-mode preview section with read-only data and export actions.
 *
 * @param {{ doc: any, onRender: (format: string) => void, rendering: boolean }} props
 * @returns {JSX.Element}
 */
function PublicPreview({ doc, onRender, rendering }) {
  if (!doc) return <p className="muted">Load a document ID to preview.</p>;

  return (
    <div className="grid two-col">
      <GlassCard title="Contact">
        <pre className="json-box">{JSON.stringify(doc.contact || {}, null, 2)}</pre>
      </GlassCard>
      <GlassCard title="Summary">
        <p>{doc.summary || "No summary available."}</p>
      </GlassCard>
      <GlassCard title="Connections">
        <pre className="json-box">{JSON.stringify(doc.connections || [], null, 2)}</pre>
      </GlassCard>
      <GlassCard title="Sections">
        <pre className="json-box">{JSON.stringify({
          education: doc.education || [],
          experience: doc.experience || [],
          projects: doc.projects || [],
          skills: doc.skills || []
        }, null, 2)}</pre>
      </GlassCard>

      <GlassCard title="Download">
        <div className="button-row">
          {FORMATS.map((format) => (
            <button key={format} type="button" className="liquid-btn" disabled={rendering} onClick={() => onRender(format)}>
              {rendering ? "Rendering..." : `Download ${format.toUpperCase()}`}
            </button>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}

/**
 * Contact editor for fields in the document contact section.
 *
 * @param {{ doc: any, onApply: (edits: any[]) => void }} props
 * @returns {JSX.Element}
 */
function EditContact({ doc, onApply }) {
  const contact = doc?.contact || {};
  const [form, setForm] = useState({
    name: contact.name || "",
    email: contact.email || "",
    phone: contact.phone || "",
    location: contact.location || "",
    website: contact.website || ""
  });

  useEffect(() => {
    setForm({
      name: contact.name || "",
      email: contact.email || "",
      phone: contact.phone || "",
      location: contact.location || "",
      website: contact.website || ""
    });
  }, [doc]);

  return (
    <form
      className="form-grid"
      onSubmit={(e) => {
        e.preventDefault();
        const edits = Object.entries(form)
          .filter(([, value]) => String(value).trim())
          .map(([field, value]) => ({ section: "contact", item_name: "", field, new_value: value }));
        onApply(edits);
      }}
    >
      {Object.keys(form).map((field) => (
        <label key={field}>
          {field}
          <input value={form[field]} onChange={(e) => setForm((p) => ({ ...p, [field]: e.target.value }))} />
        </label>
      ))}
      <button type="submit" className="liquid-btn solid">Save Contact</button>
    </form>
  );
}

/**
 * Summary editor section.
 *
 * @param {{ doc: any, onApply: (edits: any[]) => void }} props
 * @returns {JSX.Element}
 */
function EditSummary({ doc, onApply }) {
  const [summary, setSummary] = useState(doc?.summary || "");
  useEffect(() => setSummary(doc?.summary || ""), [doc]);

  return (
    <form
      className="form-stack"
      onSubmit={(e) => {
        e.preventDefault();
        onApply([{ section: "summary", item_name: "", field: "", new_value: summary }]);
      }}
    >
      <label>
        Summary
        <textarea rows={6} value={summary} onChange={(e) => setSummary(e.target.value)} />
      </label>
      <button type="submit" className="liquid-btn solid">Update Summary</button>
    </form>
  );
}

/**
 * Theme selector and updater.
 *
 * @param {{ doc: any, onApply: (edits: any[]) => void }} props
 * @returns {JSX.Element}
 */
function EditTheme({ doc, onApply }) {
  const [theme, setTheme] = useState(doc?.theme || THEMES[0]);
  useEffect(() => setTheme(doc?.theme || THEMES[0]), [doc]);

  return (
    <div className="form-stack">
      <label>
        Theme
        <select value={theme} onChange={(e) => setTheme(e.target.value)}>
          {THEMES.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </label>
      <button type="button" className="liquid-btn solid" onClick={() => onApply([{ section: "theme", item_name: "", field: "", new_value: theme }])}>
        Change Theme
      </button>
    </div>
  );
}

/**
 * Connections CRUD helper panel (add/edit/remove).
 *
 * @param {{ doc: any, onApply: (edits: any[]) => void }} props
 * @returns {JSX.Element}
 */
function ConnectionsEditor({ doc, onApply }) {
  const connections = Array.isArray(doc?.connections) ? doc.connections : [];
  const names = connections.map((c) => c.network).filter(Boolean);

  const [action, setAction] = useState("add");
  const [network, setNetwork] = useState("LinkedIn");
  const [username, setUsername] = useState("");

  return (
    <div className="form-stack">
      <LiquidSegmentedControl
        value={action}
        onChange={setAction}
        options={[
          { value: "add", label: "Add" },
          { value: "edit", label: "Edit" },
          { value: "remove", label: "Remove" }
        ]}
      />

      {action === "add" ? (
        <>
          <label>
            Network
            <input value={network} onChange={(e) => setNetwork(e.target.value)} />
          </label>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <button type="button" className="liquid-btn solid" onClick={() => onApply([{ section: "connections", item_name: network, field: "username", new_value: username }])}>
            Add Connection
          </button>
        </>
      ) : null}

      {action === "edit" ? (
        <>
          <label>
            Existing connection
            <select value={network} onChange={(e) => setNetwork(e.target.value)}>
              {names.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <label>
            New username
            <input value={username} onChange={(e) => setUsername(e.target.value)} />
          </label>
          <button type="button" className="liquid-btn solid" onClick={() => onApply([{ section: "connections", item_name: network, field: "username", new_value: username }])}>
            Update Connection
          </button>
        </>
      ) : null}

      {action === "remove" ? (
        <>
          <label>
            Remove connection
            <select value={network} onChange={(e) => setNetwork(e.target.value)}>
              {names.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <button type="button" className="liquid-btn solid" onClick={() => onApply([{ section: "connections", item_name: network, field: "delete", new_value: "" }])}>
            Remove Connection
          </button>
        </>
      ) : null}
    </div>
  );
}

/**
 * Portfolio showcase role override editor for one selected project name.
 *
 * The override is stored outside the portfolio document itself, so this panel
 * loads/saves directly against the project-level showcase endpoint.
 *
 * @param {{ title: string, projectName: string, hint?: string }} props
 * @returns {JSX.Element}
 */
function PortfolioRoleOverrideCard({ title, projectName, hint = "" }) {
  const [role, setRole] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadRole() {
      if (!projectName) {
        setRole("");
        setError("");
        setMessage("");
        return;
      }

      setLoading(true);
      setError("");
      setMessage("");

      try {
        const data = await getPortfolioShowcaseRole(projectName);
        if (!ignore) setRole(data?.role || "");
      } catch (err) {
        if (ignore) return;
        if ((err?.message || "").includes("No saved role for project")) {
          setRole("");
          return;
        }
        setError(err.message || "Failed to load role override.");
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    loadRole();
    return () => {
      ignore = true;
    };
  }, [projectName]);

  async function onSave() {
    if (!projectName) return;
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const data = await setPortfolioShowcaseRole(projectName, role);
      setRole(data?.role || role.trim());
      setMessage("Role override saved.");
    } catch (err) {
      setError(err.message || "Failed to save role override.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <GlassCard title={title} hint={hint}>
      <div className="form-stack">
        <label>
          Project
          <input value={projectName || ""} readOnly placeholder="Select a project first" />
        </label>
        <label>
          Showcase role
          <textarea
            rows={3}
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g., Backend Developer"
            disabled={!projectName || loading || saving}
          />
        </label>
        <div className="button-row">
          <button
            type="button"
            className="liquid-btn solid"
            disabled={!projectName || loading || saving}
            onClick={onSave}
          >
            {loading ? "Loading..." : saving ? "Saving..." : "Save Role Override"}
          </button>
        </div>
        {!projectName ? <p className="muted">Select a project to load or save its showcase role.</p> : null}
        {projectName && !loading && !error && !message && !role ? (
          <p className="muted">No saved role override for this project yet.</p>
        ) : null}
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="success">{message}</p> : null}
      </div>
    </GlassCard>
  );
}

/**
 * Project management panel for adding analyzed projects into a document
 * and modifying/removing existing project entries.
 *
 * @param {{
 *   projects: string[],
  *   docProjects: any[],
 *   onAddProject: (projectName: string, payload: Record<string, any>) => void,
 *   onEditProject: (projectName: string, field: string, value: any) => void,
 *   onRemoveProject: (projectName: string) => void,
 *   allowRoleOverride?: boolean
 * }} props
 * @returns {JSX.Element}
 */
function ProjectEditor({ projects, docProjects, onAddProject, onEditProject, onRemoveProject, allowRoleOverride = false }) {
  const [projectName, setProjectName] = useState(projects[0] || "");
  const [summary, setSummary] = useState("");
  const [highlights, setHighlights] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [selectedDocProject, setSelectedDocProject] = useState(docProjects?.[0]?.name || "");
  const [field, setField] = useState("summary");
  const [newValue, setNewValue] = useState("");

  useEffect(() => {
    setProjectName(projects[0] || "");
  }, [projects]);

  useEffect(() => {
    setSelectedDocProject(docProjects?.[0]?.name || "");
  }, [docProjects]);

  const payload = {
    summary: summary || undefined,
    highlights: highlights.split("\n").map((x) => x.trim()).filter(Boolean),
    start_date: toMonthValue(startDate) || undefined,
    end_date: toMonthValue(endDate) || undefined
  };

  return (
    <div className="grid two-col">
      <GlassCard title="Add Project from Analysis">
        <div className="form-stack">
          <label>
            Saved project
            <select value={projectName} onChange={(e) => setProjectName(e.target.value)}>
              {projects.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <label>
            Override summary
            <textarea rows={3} value={summary} onChange={(e) => setSummary(e.target.value)} />
          </label>
          <label>
            Override highlights (one per line)
            <textarea rows={4} value={highlights} onChange={(e) => setHighlights(e.target.value)} />
          </label>
          <label>
            Start date
            <input type="month" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </label>
          <label>
            End date
            <input type="month" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </label>
          <button type="button" className="liquid-btn solid" onClick={() => onAddProject(projectName, payload)}>
            Add Project
          </button>
        </div>
      </GlassCard>

      {allowRoleOverride ? (
        <PortfolioRoleOverrideCard
          title="Showcase Role Override"
          hint="Stored by analyzed project name for portfolio showcase customization."
          projectName={projectName}
        />
      ) : null}

      <GlassCard title="Modify Existing Project">
        {docProjects?.length ? (
          <div className="form-stack">
            <label>
              Project in document
              <select value={selectedDocProject} onChange={(e) => setSelectedDocProject(e.target.value)}>
                {docProjects.map((item) => <option key={item.name}>{item.name}</option>)}
              </select>
            </label>
            <label>
              Field
              <select value={field} onChange={(e) => setField(e.target.value)}>
                <option value="summary">summary</option>
                <option value="highlights">highlights</option>
                <option value="start_date">start_date</option>
                <option value="end_date">end_date</option>
                <option value="location">location</option>
                <option value="name">name</option>
              </select>
            </label>
            <label>
              New value {field === "highlights" ? "(one per line)" : ""}
              <textarea rows={4} value={newValue} onChange={(e) => setNewValue(e.target.value)} />
            </label>
            <div className="button-row">
              <button
                type="button"
                className="liquid-btn solid"
                onClick={() => {
                  const value = field === "highlights"
                    ? newValue.split("\n").map((x) => x.trim()).filter(Boolean)
                    : newValue;
                  onEditProject(selectedDocProject, field, value);
                }}
              >
                Save Change
              </button>
              <button type="button" className="liquid-btn" onClick={() => onRemoveProject(selectedDocProject)}>Remove Project</button>
            </div>
          </div>
        ) : (
          <p className="muted">No projects in this document yet.</p>
        )}
      </GlassCard>

      {allowRoleOverride ? (
        <PortfolioRoleOverrideCard
          title="Existing Project Role Override"
          hint="Useful when you want the saved showcase role to match the project already in this portfolio."
          projectName={selectedDocProject}
        />
      ) : null}
    </div>
  );
}

/**
 * Resume-only education and experience editor controls.
 *
 * @param {{
 *   doc: any,
 *   onAddEducation: (payload: any) => void,
 *   onRemoveEducation: (institution: string) => void,
 *   onAddExperience: (payload: any) => void,
 *   onRemoveExperience: (company: string) => void,
 *   onEdit: (edits: any[]) => void
 * }} props
 * @returns {JSX.Element}
 */
function ResumeEducationExperience({ doc, onAddEducation, onRemoveEducation, onAddExperience, onRemoveExperience, onEdit }) {
  const education = Array.isArray(doc?.education) ? doc.education : [];
  const experience = Array.isArray(doc?.experience) ? doc.experience : [];

  const [institution, setInstitution] = useState("");
  const [area, setArea] = useState("");
  const [degree, setDegree] = useState("");
  const [eduHighlights, setEduHighlights] = useState("");

  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [expHighlights, setExpHighlights] = useState("");

  return (
    <div className="grid two-col">
      <GlassCard title="Education">
        <div className="form-stack">
          <label>
            Institution *
            <input value={institution} onChange={(e) => setInstitution(e.target.value)} />
          </label>
          <label>
            Area *
            <input value={area} onChange={(e) => setArea(e.target.value)} />
          </label>
          <label>
            Degree
            <input value={degree} onChange={(e) => setDegree(e.target.value)} />
          </label>
          <label>
            Highlights
            <textarea rows={3} value={eduHighlights} onChange={(e) => setEduHighlights(e.target.value)} />
          </label>
          <div className="button-row">
            <button
              type="button"
              className="liquid-btn solid"
              onClick={() => onAddEducation({
                institution,
                area,
                degree: degree || undefined,
                highlights: eduHighlights.split("\n").map((x) => x.trim()).filter(Boolean)
              })}
            >
              Add Education
            </button>
            {education.length ? (
              <button type="button" className="liquid-btn" onClick={() => onRemoveEducation(education[0].institution)}>
                Remove First Education
              </button>
            ) : null}
          </div>
          {education.length ? (
            <button
              type="button"
              className="liquid-btn"
              onClick={() => onEdit([{ section: "education", item_name: education[0].institution, field: "area", new_value: area || education[0].area || "" }])}
            >
              Quick Modify First Education Area
            </button>
          ) : null}
        </div>
      </GlassCard>

      <GlassCard title="Experience">
        <div className="form-stack">
          <label>
            Company *
            <input value={company} onChange={(e) => setCompany(e.target.value)} />
          </label>
          <label>
            Position
            <input value={position} onChange={(e) => setPosition(e.target.value)} />
          </label>
          <label>
            Highlights
            <textarea rows={3} value={expHighlights} onChange={(e) => setExpHighlights(e.target.value)} />
          </label>
          <div className="button-row">
            <button
              type="button"
              className="liquid-btn solid"
              onClick={() => onAddExperience({
                company,
                position: position || undefined,
                highlights: expHighlights.split("\n").map((x) => x.trim()).filter(Boolean)
              })}
            >
              Add Experience
            </button>
            {experience.length ? (
              <button type="button" className="liquid-btn" onClick={() => onRemoveExperience(experience[0].company)}>
                Remove First Experience
              </button>
            ) : null}
          </div>
          {experience.length ? (
            <button
              type="button"
              className="liquid-btn"
              onClick={() => onEdit([{ section: "experience", item_name: experience[0].company, field: "position", new_value: position || experience[0].position || "" }])}
            >
              Quick Modify First Experience Position
            </button>
          ) : null}
        </div>
      </GlassCard>
    </div>
  );
}

/**
 * Core workspace studio for one document kind (resume or portfolio).
 * Handles lifecycle actions, edits, project operations, and rendering.
 *
 * @param {{ kind: "resume" | "portfolio", mode: "public" | "private" }} props
 * @returns {JSX.Element}
 */
function DocumentStudio({ kind, mode }) {
  const isResume = kind === "resume";

  /**
   * Document-specific state:
   * - identity/loading (`docId`, `idInput`, `busy`),
   * - loaded payload (`doc`),
   * - creation/edit controls (`name`, `theme`, section toggles),
   * - feedback (`message`, `error`),
   * - project support (`savedProjects`).
   */
  const [docId, setDocId] = useState("");
  const [doc, setDoc] = useState(null);
  const [name, setName] = useState("");
  const [theme, setTheme] = useState(THEMES[0]);
  const [idInput, setIdInput] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [activeSection, setActiveSection] = useState("edit");
  const [editCategory, setEditCategory] = useState("contact");
  const [savedProjects, setSavedProjects] = useState([]);

  const [rendering, setRendering] = useState(false);

  useEffect(() => {
    let ignore = false;
    /**
     * Loads known analyzed project names for project insertion workflows.
     *
     * @returns {Promise<void>}
     */
    async function loadProjects() {
      try {
        const data = await fetchProjects();
        if (!ignore) setSavedProjects(Array.isArray(data) ? data : []);
      } catch {
        if (!ignore) setSavedProjects([]);
      }
    }
    loadProjects();
    return () => {
      ignore = true;
    };
  }, []);

  /**
   * Refreshes document state from backend for the current document id.
   *
   * @param {string} [currentId=docId]
   * @returns {Promise<void>}
   */
  async function refresh(currentId = docId) {
    if (!currentId) return;
    const data = isResume ? await fetchResume(currentId) : await fetchPortfolio(currentId);
    setDoc(data);
  }

  /**
   * Executes an action with shared busy/error/success state handling,
   * then refreshes document data when applicable.
   *
   * @param {() => Promise<void>} fn
   * @param {string} [success="Updated."]
   * @returns {Promise<void>}
   */
  async function safeAction(fn, success = "Updated.") {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
      setMessage(success);
      if (docId) await refresh(docId);
    } catch (err) {
      setError(err.message || "Request failed.");
    } finally {
      setBusy(false);
    }
  }

  /**
   * Creates a new document (resume or portfolio) and loads it.
   *
   * @returns {Promise<void>}
   */
  async function onGenerate() {
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }

    await safeAction(async () => {
      const res = isResume ? await generateResume(name.trim(), theme) : await generatePortfolio(name.trim(), theme);
      const id = isResume ? res.resume_id : res.portfolio_id;
      setDocId(id);
      setIdInput(id);
      const data = isResume ? await fetchResume(id) : await fetchPortfolio(id);
      setDoc(data);
      const key = isResume ? "recentResumeIds" : "recentPortfolioIds";
      const existing = JSON.parse(window.localStorage.getItem(key) || "[]");
      const merged = [id, ...existing.filter((x) => x !== id)].slice(0, 10);
      window.localStorage.setItem(key, JSON.stringify(merged));
    }, `${isResume ? "Resume" : "Portfolio"} created.`);
  }

  /**
   * Loads an existing document by id.
   *
   * @param {string} [id=idInput]
   * @returns {Promise<void>}
   */
  async function onLoad(id = idInput) {
    if (!id.trim()) {
      setError("Enter a document ID first.");
      return;
    }
    await safeAction(async () => {
      const data = isResume ? await fetchResume(id.trim()) : await fetchPortfolio(id.trim());
      setDocId(id.trim());
      setDoc(data);
      setIdInput(id.trim());
    }, `${isResume ? "Resume" : "Portfolio"} loaded.`);
  }

  /**
   * Deletes the currently active document.
   *
   * @returns {Promise<void>}
   */
  async function onDelete() {
    if (!docId) {
      setError("Load a document first.");
      return;
    }
    await safeAction(async () => {
      if (isResume) await deleteResume(docId);
      else await deletePortfolio(docId);
      setDocId("");
      setDoc(null);
      setIdInput("");
    }, `${isResume ? "Resume" : "Portfolio"} deleted.`);
  }

  /**
   * Applies an edit set to the active document.
   *
   * @param {any[]} edits
   * @returns {Promise<void>}
   */
  async function onApplyEdits(edits) {
    if (!docId) return;
    await safeAction(async () => {
      if (isResume) await editResume(docId, edits);
      else await editPortfolio(docId, edits);
    }, "Changes saved.");
  }

  /**
   * Adds a project entry into the active document.
   *
   * @param {string} projectName
   * @param {Record<string, any>} payload
   * @returns {Promise<void>}
   */
  async function onAddProject(projectName, payload) {
    if (!docId || !projectName) return;
    await safeAction(async () => {
      if (isResume) await addResumeProject(docId, projectName, payload);
      else await addPortfolioProject(docId, projectName, payload);
    }, "Project added.");
  }

  /**
   * Removes a project entry from the active document.
   *
   * @param {string} projectName
   * @returns {Promise<void>}
   */
  async function onRemoveProject(projectName) {
    if (!docId || !projectName) return;
    await safeAction(async () => {
      if (isResume) {
        await editResume(docId, [{ section: "projects", item_name: projectName, field: "delete", new_value: "" }]);
      } else {
        await removePortfolioProject(docId, projectName);
      }
    }, "Project removed.");
  }

  /**
   * Requests rendered output in a selected format and downloads it.
   *
   * @param {string} format
   * @returns {Promise<void>}
   */
  async function onRender(format) {
    if (!docId) return;
    setRendering(true);
    setError("");
    try {
      const blob = isResume ? await renderResume(docId, format) : await renderPortfolio(docId, format);
      downloadBlob(blob, `${kind}_${docId}.${format === "markdown" ? "md" : format}`);
    } catch (err) {
      setError(err.message || "Render failed.");
    } finally {
      setRendering(false);
    }
  }

  const recentIds = useMemo(() => {
    if (typeof window === "undefined") return [];
    const key = isResume ? "recentResumeIds" : "recentPortfolioIds";
    try {
      const parsed = JSON.parse(window.localStorage.getItem(key) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }, [isResume, docId]);

  if (mode === "public") {
    return (
      <div className="page-stack workspace-page">
        <div className="grid two-col">
          <GlassCard title={`${isResume ? "Resume" : "Portfolio"} ID`} hint="Public mode is view + download only.">
            <div className="form-stack">
              <div className="settings-list compact">
                <label className="settings-row settings-field-row">
                  <span className="settings-label">Document ID</span>
                  <input
                    className="settings-control"
                    value={idInput}
                    onChange={(e) => setIdInput(e.target.value)}
                    placeholder="e.g., Jane_Doe_a1b2c3d4"
                  />
                </label>
              </div>
              <div className="button-row">
                <button type="button" className="liquid-btn solid" disabled={busy} onClick={() => onLoad(idInput)}>
                  {busy ? "Loading..." : `Load ${isResume ? "Resume" : "Portfolio"}`}
                </button>
              </div>
              {recentIds.length ? (
                <div className="button-row">
                  {recentIds.map((id) => (
                    <button key={id} type="button" className="liquid-btn" onClick={() => { setIdInput(id); onLoad(id); }}>
                      {id}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
            {error ? <p className="error">{error}</p> : null}
            {message ? <p className="success">{message}</p> : null}
          </GlassCard>

          <PublicPreview doc={doc} onRender={onRender} rendering={rendering} />
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack workspace-page">
      <div className="grid two-col workspace-control-grid">
        <GlassCard title={`${isResume ? "Resume" : "Portfolio"} Controls`} hint="Create or load a document.">
          <div className="form-stack">
            <div className="settings-list compact">
              <label className="settings-row settings-field-row">
                <span className="settings-label">Full name</span>
                <input
                  className="settings-control"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Jane Doe"
                />
              </label>
              <label className="settings-row settings-field-row">
                <span className="settings-label">Theme</span>
                <select className="settings-control" value={theme} onChange={(e) => setTheme(e.target.value)}>
                  {THEMES.map((item) => <option key={item}>{item}</option>)}
                </select>
              </label>
            </div>
            <div className="button-row">
              <button type="button" className="liquid-btn solid" disabled={busy} onClick={onGenerate}>
                Generate {isResume ? "Resume" : "Portfolio"}
              </button>
            </div>

            <div className="settings-list compact">
              <label className="settings-row settings-field-row">
                <span className="settings-label">Load by ID</span>
                <input
                  className="settings-control"
                  value={idInput}
                  onChange={(e) => setIdInput(e.target.value)}
                  placeholder="Paste an existing ID"
                />
              </label>
            </div>
            <div className="button-row">
              <button type="button" className="liquid-btn solid" disabled={busy} onClick={() => onLoad(idInput)}>
                Load
              </button>
            </div>
            {recentIds.length ? (
              <div className="button-row">
                {recentIds.slice(0, 3).map((id) => (
                  <button key={id} type="button" className="liquid-btn" onClick={() => { setIdInput(id); onLoad(id); }}>{id}</button>
                ))}
              </div>
            ) : null}
          </div>
        </GlassCard>

        <GlassCard title="Status" hint="Current document and actions.">
          <div className="form-stack">
            <div className="settings-list compact">
              <div className="settings-row">
                <span className="settings-label">Active ID</span>
                <strong className="settings-value">{docId || "None"}</strong>
              </div>
              <div className="settings-row">
                <span className="settings-label">Mode</span>
                <strong className="settings-value">{mode === "private" ? "Private" : "Public"}</strong>
              </div>
            </div>
            <div className="button-row">
              <button type="button" className="liquid-btn solid" onClick={() => { setDocId(""); setDoc(null); setIdInput(""); }}>
                Close
              </button>
              <button type="button" className="liquid-btn solid" disabled={!docId || busy} onClick={onDelete}>
                Delete Active
              </button>
            </div>
            {error ? <p className="error">{error}</p> : null}
            {message ? <p className="success">{message}</p> : null}
          </div>
        </GlassCard>
      </div>

      {docId && doc ? (
        <>
          <LiquidSegmentedControl
            value={activeSection}
            onChange={setActiveSection}
            options={[
              { value: "edit", label: "Edit" },
              { value: "projects", label: "Projects" },
              { value: "download", label: "Download" }
            ]}
          />

          {activeSection === "edit" ? (
            <GlassCard title="Edit Sections">
              <LiquidSegmentedControl
                value={editCategory}
                onChange={setEditCategory}
                options={[
                  { value: "contact", label: "Contact" },
                  { value: "summary", label: "Summary" },
                  { value: "theme", label: "Theme" },
                  { value: "connections", label: "Connections" },
                  ...(isResume ? [{ value: "career", label: "Education + Experience" }] : [])
                ]}
              />

              {editCategory === "contact" ? <EditContact doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "summary" ? <EditSummary doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "theme" ? <EditTheme doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "connections" ? <ConnectionsEditor doc={doc} onApply={onApplyEdits} /> : null}
              {isResume && editCategory === "career" ? (
                <ResumeEducationExperience
                  doc={doc}
                  onEdit={onApplyEdits}
                  onAddEducation={(payload) => safeAction(() => addResumeEducation(docId, payload), "Education entry added.")}
                  onRemoveEducation={(nameToRemove) => safeAction(() => removeResumeEducation(docId, nameToRemove), "Education removed.")}
                  onAddExperience={(payload) => safeAction(() => addResumeExperience(docId, payload), "Experience entry added.")}
                  onRemoveExperience={(nameToRemove) => safeAction(() => removeResumeExperience(docId, nameToRemove), "Experience removed.")}
                />
              ) : null}
            </GlassCard>
          ) : null}

          {activeSection === "projects" ? (
            <ProjectEditor
              projects={savedProjects}
              docProjects={Array.isArray(doc.projects) ? doc.projects : []}
              onAddProject={onAddProject}
              onEditProject={(projectName, field, value) => onApplyEdits([{ section: "projects", item_name: projectName, field, new_value: value }])}
              onRemoveProject={onRemoveProject}
              allowRoleOverride={!isResume}
            />
          ) : null}

          {activeSection === "download" ? (
            <GlassCard title="Render + Download">
              <div className="button-row">
                {FORMATS.map((format) => (
                  <button key={format} type="button" className="liquid-btn solid" disabled={rendering} onClick={() => onRender(format)}>
                    {rendering ? "Rendering..." : `Download ${format.toUpperCase()}`}
                  </button>
                ))}
              </div>
            </GlassCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

/**
 * Workspace route that switches between Resume and Portfolio studios.
 *
 * @returns {JSX.Element}
 */
export default function WorkspacePage() {
  const [tab, setTab] = useState("resume");
  const [mode, setMode] = useState("private");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get("tab");
    if (fromQuery === "portfolio" || fromQuery === "resume") {
      setTab(fromQuery);
    }

    const stored = window.localStorage.getItem("viewMode");
    if (stored === "public" || stored === "private") setMode(stored);

    /**
     * Syncs workspace mode when nav-level visibility mode changes.
     *
     * @param {CustomEvent<"public" | "private">} event
     * @returns {void}
     */
    const onViewModeChange = (event) => {
      const nextMode = event?.detail;
      if (nextMode === "public" || nextMode === "private") {
        setMode(nextMode);
      }
    };

    window.addEventListener("viewModeChange", onViewModeChange);
    return () => window.removeEventListener("viewModeChange", onViewModeChange);
  }, []);

  return (
    <LiquidShell
      title="Resume + Portfolio Workspace"
      subtitle="Create, edit, preview, and export resume or portfolio documents with public/private access modes."
    >
      <div className="page-stack workspace-page">
        <LiquidSegmentedControl
          value={tab}
          onChange={setTab}
          options={[
            { value: "resume", label: "Resume" },
            { value: "portfolio", label: "Portfolio" }
          ]}
        />

        {tab === "resume" ? <DocumentStudio kind="resume" mode={mode} /> : null}
        {tab === "portfolio" ? <DocumentStudio kind="portfolio" mode={mode} /> : null}
      </div>
    </LiquidShell>
  );
}
