"use client";

/**
 * Workspace route module.
 *
 * This file contains:
 * - shared editor/preview subcomponents for resume and portfolio documents,
 * - document lifecycle handlers (generate/load/delete/edit/render),
 * - and mode-aware rendering for private/public access behavior.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
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
  fetchResumes,
  fetchPortfolios,
  fetchProjectByName,
  addResumeProjectAI,
  addPortfolioProjectAI,
  generatePortfolio,
  generateResume,
  removePortfolioProject,
  removeResumeProject,
  removeResumeEducation,
  removeResumeExperience,
  renderPortfolio,
  renderResume,
  setPortfolioShowcaseRole,
  addResumeSkill,
  appendResumeSkill,
  removeResumeSkill,
  addPortfolioSkill,
  appendPortfolioSkill,
  removePortfolioSkill
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
const SELECT_PLACEHOLDER = "— select —";

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
          <input className="settings-control" value={form[field]} onChange={(e) => setForm((p) => ({ ...p, [field]: e.target.value }))} />
        </label>
      ))}
      <button type="submit" className="liquid-btn solid btn-success">Save Contact</button>
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
        <textarea className="settings-control" rows={6} value={summary} onChange={(e) => setSummary(e.target.value)} />
      </label>
      <button type="submit" className="liquid-btn solid btn-success">Update Summary</button>
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
        Current theme
        <input className="settings-control" type="text" readOnly value={doc?.theme || "—"} style={{ opacity: 0.6, cursor: "default" }} />
      </label>
      <label>
        New theme
        <select className="settings-control" value={theme} onChange={(e) => setTheme(e.target.value)}>
          {THEMES.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </label>
      <button type="button" className="liquid-btn solid btn-success" onClick={() => onApply([{ section: "theme", item_name: "", field: "", new_value: theme }])}>
        Change Theme
      </button>
    </div>
  );
}

const KNOWN_NETWORKS = [
  "LinkedIn", "GitHub", "GitLab", "Twitter", "Instagram",
  "YouTube", "Mastodon", "StackOverflow", "ResearchGate", "ORCID",
];

function Combobox({ value, onChange, placeholder }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const filtered = KNOWN_NETWORKS.filter((n) =>
    n.toLowerCase().includes(value.toLowerCase())
  );

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={ref} className="settings-combobox" style={{ position: "relative" }}>
      <input
        className="settings-control"
        value={value}
        placeholder={placeholder}
        onChange={(e) => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
      />
      {open && filtered.length > 0 && (
        <ul style={{
          position: "absolute", top: "100%", left: 0, right: 0, zIndex: 200,
          margin: 0, padding: "0.25rem 0", listStyle: "none",
          background: "var(--bg-1)", border: "1px solid var(--line)",
          borderRadius: "var(--surface-radius)",
          maxHeight: "180px", overflowY: "auto",
        }}>
          {filtered.map((n) => (
            <li
              key={n}
              onMouseDown={() => { onChange(n); setOpen(false); }}
              style={{
                padding: "0.45rem 0.85rem", cursor: "pointer",
                color: "var(--ink-0)", borderRadius: "var(--surface-radius)",
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "transparent"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              {n}
            </li>
          ))}
        </ul>
      )}
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

  useEffect(() => {
    if (action === "edit") {
      const current = connections.find((c) => c.network === network);
      setUsername(current?.username || "");
    } else {
      setUsername("");
    }
  }, [network, action]);

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
            <Combobox value={network} onChange={setNetwork} placeholder="e.g. LinkedIn" />
          </label>
          <label>
            Username
            <input className="settings-control" value={username} onChange={(e) => setUsername(e.target.value)} />
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
            <select className="settings-control" value={network} onChange={(e) => setNetwork(e.target.value)}>
              {names.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <label>
            New username
            <input className="settings-control" value={username} onChange={(e) => setUsername(e.target.value)} />
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
            <select className="settings-control" value={network} onChange={(e) => setNetwork(e.target.value)}>
              {names.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <button type="button" className="liquid-btn solid btn-danger" onClick={() => onApply([{ section: "connections", item_name: network, field: "delete", new_value: "" }])}>
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
        if (err?.status === 404) {
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
function ProjectEditor({ projects, docProjects, onAddProject, onAddProjectAI, onEditProject, onRemoveProject, busy = false, allowRoleOverride = false }) {
  const [aiLoading, setAiLoading] = useState(false);
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

  useEffect(() => {
    if (!projectName) return;
    let cancelled = false;
    fetchProjectByName(projectName)
      .then((data) => {
        if (cancelled) return;
        const item = data?.analysis?.resume_item || {};
        setSummary(item.summary || "");
        setHighlights((item.highlights || []).join("\n"));
        setStartDate(toMonthValue(item.start_date || ""));
        setEndDate(toMonthValue(item.end_date || ""));
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [projectName]);

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
            <select className="settings-control" value={projectName} onChange={(e) => setProjectName(e.target.value)}>
              {projects.map((name) => <option key={name}>{name}</option>)}
            </select>
          </label>
          <label>
            Override summary
            <textarea className="settings-control" rows={3} value={summary} onChange={(e) => setSummary(e.target.value)} />
          </label>
          <label>
            Override highlights (one per line)
            <textarea className="settings-control" rows={4} value={highlights} onChange={(e) => setHighlights(e.target.value)} />
          </label>
          <label>
            Start date
            <input className="settings-control" type="month" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </label>
          <label>
            End date
            <input className="settings-control" type="month" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </label>
          <div className="button-row">
            <button type="button" className="liquid-btn solid btn-success" disabled={busy || aiLoading} onClick={() => onAddProject(projectName, payload)}>
              Add Project
            </button>
            <button type="button" className="liquid-btn solid btn-success" disabled={busy || aiLoading} onClick={async () => { setAiLoading(true); try { await onAddProjectAI(projectName); } finally { setAiLoading(false); } }} title="Use Gemini AI to generate a polished project entry">
              {aiLoading ? "⏳ Generating..." : "✦ Add with AI"}
            </button>
          </div>
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
              <select className="settings-control" value={selectedDocProject} onChange={(e) => setSelectedDocProject(e.target.value)}>
                {docProjects.map((item) => <option key={item.name}>{item.name}</option>)}
              </select>
            </label>
            <label>
              Field
              <select className="settings-control" value={field} onChange={(e) => { setField(e.target.value); setNewValue(""); }}>
                <option value="summary">summary</option>
                <option value="highlights">highlights</option>
                <option value="start_date">start_date</option>
                <option value="end_date">end_date</option>
                <option value="location">location</option>
                <option value="name">name</option>
              </select>
            </label>
            {(() => {
              const proj = docProjects.find((p) => p.name === selectedDocProject);
              const current = proj?.[field];
              const display = Array.isArray(current) ? current.join("\n") : (current ?? "—");
              const isSmall = ["name", "location", "start_date", "end_date"].includes(field);
              return (
                <label>
                  Current value
                  {isSmall
                    ? <input type="text" readOnly value={display} className="settings-control" style={{ opacity: 0.6, cursor: "default" }} />
                    : <textarea rows={field === "highlights" ? 4 : 2} readOnly value={display} className="settings-control" style={{ opacity: 0.6, cursor: "default" }} />
                  }
                </label>
              );
            })()}
            <label>
              New value {field === "highlights" ? "(one per line)" : ""}
              {(field === "start_date" || field === "end_date")
                ? <input className="settings-control" type="month" value={newValue} onChange={(e) => setNewValue(e.target.value)} />
                : (field === "name" || field === "location")
                  ? <input className="settings-control" type="text" value={newValue} onChange={(e) => setNewValue(e.target.value)} placeholder={field === "name" ? "e.g., My Awesome Project" : "e.g., Vancouver, BC"} />
                  : <textarea className="settings-control" rows={field === "highlights" ? 4 : 2} value={newValue} onChange={(e) => setNewValue(e.target.value)} placeholder={field === "highlights" ? "e.g., Built REST API with FastAPI\nWrote unit tests with pytest" : "e.g., A web app that generates resumes using AI."} />
              }
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
              <button type="button" className="liquid-btn btn-danger" onClick={() => onRemoveProject(selectedDocProject)}>Remove Project ({selectedDocProject})</button>
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

  const today = new Date().toISOString().slice(0, 7);

  // Education state
  const [eduAction, setEduAction] = useState("add");
  const [institution, setInstitution] = useState("");
  const [area, setArea] = useState("");
  const [degree, setDegree] = useState("");
  const [gpa, setGpa] = useState("");
  const [eduLocation, setEduLocation] = useState("");
  const [eduStart, setEduStart] = useState("");
  const [eduEnd, setEduEnd] = useState("");
  const [eduHighlights, setEduHighlights] = useState("");
  const [selectedEdu, setSelectedEdu] = useState(education[0]?.institution || "");
  const [eduField, setEduField] = useState("institution");
  const [eduFieldValue, setEduFieldValue] = useState("");

  // Experience state
  const [expAction, setExpAction] = useState("add");
  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [expLocation, setExpLocation] = useState("");
  const [expStart, setExpStart] = useState("");
  const [expEnd, setExpEnd] = useState("");
  const [expHighlights, setExpHighlights] = useState("");
  const [selectedExp, setSelectedExp] = useState(experience[0]?.company || "");
  const [expField, setExpField] = useState("company");
  const [expFieldValue, setExpFieldValue] = useState("");

  useEffect(() => { setSelectedEdu(education[0]?.institution || ""); }, [doc]);
  useEffect(() => { setSelectedExp(experience[0]?.company || ""); }, [doc]);

  const [careerSection, setCareerSection] = useState("education");

  const EDU_FIELDS = ["institution", "area", "degree", "gpa", "location", "start_date", "end_date", "highlights"];
  const EXP_FIELDS = ["company", "position", "location", "start_date", "end_date", "summary", "highlights"];
  const DATE_FIELDS = ["start_date", "end_date"];
  const SMALL_FIELDS = ["institution", "area", "degree", "gpa", "location", "company", "position", "summary"];

  function parseHighlights(val) {
    return val.split("\n").map((x) => x.trim()).filter(Boolean);
  }

  function formatDate(val, isEnd = false) {
    if (!val) return undefined;
    return isEnd && val === today ? "present" : val;
  }

  return (
    <div className="form-stack">
      <LiquidSegmentedControl
        value={careerSection}
        onChange={setCareerSection}
        options={[
          { value: "education", label: "Education" },
          { value: "experience", label: "Experience" },
        ]}
      />

      {careerSection === "education" && (
      <div className="form-stack">
        <LiquidSegmentedControl
          value={eduAction}
          onChange={setEduAction}
          options={[
            { value: "add", label: "Add" },
            { value: "modify", label: "Modify" },
            { value: "remove", label: "Remove" },
          ]}
        />

          {eduAction === "add" && (
            <>
              <label>Institution *<input value={institution} placeholder="e.g., University of British Columbia" onChange={(e) => setInstitution(e.target.value)} /></label>
              <label>Area of Study *<input value={area} placeholder="e.g., Computer Science" onChange={(e) => setArea(e.target.value)} /></label>
              <label>Degree<input value={degree} placeholder="e.g., BSc" onChange={(e) => setDegree(e.target.value)} /></label>
              <label>GPA<input value={gpa} placeholder="e.g., 3.8" onChange={(e) => setGpa(e.target.value)} /></label>
              <label>Location<input value={eduLocation} placeholder="e.g., Kelowna, BC" onChange={(e) => setEduLocation(e.target.value)} /></label>
              <label>Start date<input type="month" value={eduStart} onChange={(e) => setEduStart(e.target.value)} /></label>
              <label>End date <span style={{opacity:0.6, fontSize:"0.8em"}}>(select current month for "present")</span><input type="month" value={eduEnd} onChange={(e) => setEduEnd(e.target.value)} /></label>
              <label>Highlights (one per line)<textarea rows={3} value={eduHighlights} onChange={(e) => setEduHighlights(e.target.value)} /></label>
              <button type="button" className="liquid-btn solid btn-success" onClick={() => onAddEducation({
                institution, area,
                degree: degree || undefined,
                gpa: gpa || undefined,
                location: eduLocation || undefined,
                start_date: formatDate(eduStart),
                end_date: formatDate(eduEnd, true),
                highlights: parseHighlights(eduHighlights)
              })}>Add Education</button>
            </>
          )}

          {eduAction === "modify" && (
            <>
              {education.length ? (
                <>
                  <label>Education entry<select value={selectedEdu} onChange={(e) => setSelectedEdu(e.target.value)}>{education.map((e) => <option key={e.institution}>{e.institution}</option>)}</select></label>
                  <label>Field<select value={eduField} onChange={(e) => { setEduField(e.target.value); setEduFieldValue(""); }}>{EDU_FIELDS.map((f) => <option key={f}>{f}</option>)}</select></label>
                  <label>
                    Current value
                    <input type="text" readOnly style={{ opacity: 0.6, cursor: "default" }} value={(() => { const entry = education.find((e) => e.institution === selectedEdu); const v = entry?.[eduField]; return Array.isArray(v) ? v.join("\n") : (v ?? "—"); })()} />
                  </label>
                  <label>
                    New value
                    {DATE_FIELDS.includes(eduField)
                      ? <input type="month" value={eduFieldValue} onChange={(e) => setEduFieldValue(e.target.value)} />
                      : SMALL_FIELDS.includes(eduField)
                        ? <input type="text" value={eduFieldValue} onChange={(e) => setEduFieldValue(e.target.value)} />
                        : <textarea rows={3} value={eduFieldValue} onChange={(e) => setEduFieldValue(e.target.value)} />
                    }
                  </label>
                  <button type="button" className="liquid-btn solid" onClick={() => {
                    const value = eduField === "highlights" ? parseHighlights(eduFieldValue) : DATE_FIELDS.includes(eduField) ? formatDate(eduFieldValue, eduField === "end_date") : eduFieldValue;
                    onEdit([{ section: "education", item_name: selectedEdu, field: eduField, new_value: value }]);
                  }}>Save Change</button>
                </>
              ) : <p style={{opacity:0.6}}>No education entries to modify.</p>}
            </>
          )}

          {eduAction === "remove" && (
            <>
              {education.length ? (
                <>
                  <label>Education entry<select value={selectedEdu} onChange={(e) => setSelectedEdu(e.target.value)}>{education.map((e) => <option key={e.institution}>{e.institution}</option>)}</select></label>
                  <button type="button" className="liquid-btn btn-danger" onClick={() => onRemoveEducation(selectedEdu)}>Remove ({selectedEdu})</button>
                </>
              ) : <p style={{opacity:0.6}}>No education entries to remove.</p>}
            </>
          )}
      </div>
      )}

      {careerSection === "experience" && (
      <div className="form-stack">
        <LiquidSegmentedControl
          value={expAction}
          onChange={setExpAction}
          options={[
            { value: "add", label: "Add" },
            { value: "modify", label: "Modify" },
            { value: "remove", label: "Remove" },
          ]}
        />

          {expAction === "add" && (
            <>
              <label>Company *<input value={company} placeholder="e.g., Acme Corp" onChange={(e) => setCompany(e.target.value)} /></label>
              <label>Position<input value={position} placeholder="e.g., Software Engineer" onChange={(e) => setPosition(e.target.value)} /></label>
              <label>Location<input value={expLocation} placeholder="e.g., Vancouver, BC" onChange={(e) => setExpLocation(e.target.value)} /></label>
              <label>Start date<input type="month" value={expStart} onChange={(e) => setExpStart(e.target.value)} /></label>
              <label>End date <span style={{opacity:0.6, fontSize:"0.8em"}}>(select current month for "present")</span><input type="month" value={expEnd} onChange={(e) => setExpEnd(e.target.value)} /></label>
              <label>Highlights (one per line)<textarea rows={3} value={expHighlights} onChange={(e) => setExpHighlights(e.target.value)} /></label>
              <button type="button" className="liquid-btn solid btn-success" onClick={() => onAddExperience({
                company,
                position: position || undefined,
                location: expLocation || undefined,
                start_date: formatDate(expStart),
                end_date: formatDate(expEnd, true),
                highlights: parseHighlights(expHighlights)
              })}>Add Experience</button>
            </>
          )}

          {expAction === "modify" && (
            <>
              {experience.length ? (
                <>
                  <label>Experience entry<select value={selectedExp} onChange={(e) => setSelectedExp(e.target.value)}>{experience.map((e) => <option key={e.company}>{e.company}</option>)}</select></label>
                  <label>Field<select value={expField} onChange={(e) => { setExpField(e.target.value); setExpFieldValue(""); }}>{EXP_FIELDS.map((f) => <option key={f}>{f}</option>)}</select></label>
                  <label>
                    Current value
                    <input type="text" readOnly style={{ opacity: 0.6, cursor: "default" }} value={(() => { const entry = experience.find((e) => e.company === selectedExp); const v = entry?.[expField]; return Array.isArray(v) ? v.join("\n") : (v ?? "—"); })()} />
                  </label>
                  <label>
                    New value
                    {DATE_FIELDS.includes(expField)
                      ? <input type="month" value={expFieldValue} onChange={(e) => setExpFieldValue(e.target.value)} />
                      : SMALL_FIELDS.includes(expField)
                        ? <input type="text" value={expFieldValue} onChange={(e) => setExpFieldValue(e.target.value)} />
                        : <textarea rows={3} value={expFieldValue} onChange={(e) => setExpFieldValue(e.target.value)} />
                    }
                  </label>
                  <button type="button" className="liquid-btn solid" onClick={() => {
                    const value = expField === "highlights" ? parseHighlights(expFieldValue) : DATE_FIELDS.includes(expField) ? formatDate(expFieldValue, expField === "end_date") : expFieldValue;
                    onEdit([{ section: "experience", item_name: selectedExp, field: expField, new_value: value }]);
                  }}>Save Change</button>
                </>
              ) : <p style={{opacity:0.6}}>No experience entries to modify.</p>}
            </>
          )}

          {expAction === "remove" && (
            <>
              {experience.length ? (
                <>
                  <label>Experience entry<select value={selectedExp} onChange={(e) => setSelectedExp(e.target.value)}>{experience.map((e) => <option key={e.company}>{e.company}</option>)}</select></label>
                  <button type="button" className="liquid-btn btn-danger" onClick={() => onRemoveExperience(selectedExp)}>Remove ({selectedExp})</button>
                </>
              ) : <p style={{opacity:0.6}}>No experience entries to remove.</p>}
            </>
          )}
      </div>
      )}
    </div>
  );
}

/**
 * Skills CRUD panel for adding, appending to, and removing skill categories.
 *
 * @param {{
 *   doc: any,
 *   onAddSkill: (payload: { label: string, details: string }) => void,
 *   onAppendSkill: (label: string, details: string) => void,
 *   onRemoveSkill: (label: string) => void,
 *   onApply: (edits: any[]) => void
 * }} props
 * @returns {JSX.Element}
 */
function SkillsEditor({ doc, onAddSkill, onAppendSkill, onRemoveSkill, onApply }) {
  const skills = Array.isArray(doc?.skills) ? doc.skills : [];
  const labels = skills.map((s) => s.label).filter(Boolean);

  const [action, setAction] = useState("add");
  const [label, setLabel] = useState("");
  const [details, setDetails] = useState("");
  const [selectedLabel, setSelectedLabel] = useState(labels[0] || "");
  const [appendDetails, setAppendDetails] = useState("");
  const [modifyDetails, setModifyDetails] = useState("");

  useEffect(() => {
    setSelectedLabel(labels[0] || "");
  }, [doc]);

  useEffect(() => {
    if (action === "modify") {
      const current = skills.find((s) => s.label === selectedLabel);
      setModifyDetails(current?.details || "");
    }
  }, [selectedLabel, action]);

  return (
    <div className="form-stack">
      <LiquidSegmentedControl
        value={action}
        onChange={setAction}
        options={[
          { value: "add", label: "Add" },
          { value: "modify", label: "Modify" },
          { value: "append", label: "Append" },
          { value: "remove", label: "Remove" },
        ]}
      />

      {action === "add" && (
        <>
          <label>
            Category label
            <input value={label} placeholder="e.g., Languages" onChange={(e) => setLabel(e.target.value)} />
          </label>
          <label>
            Skills (comma-separated)
            <input value={details} placeholder="e.g., Python, Java, C++" onChange={(e) => setDetails(e.target.value)} />
          </label>
          <button
            type="button"
            className="liquid-btn solid"
            onClick={() => { onAddSkill({ label, details }); setLabel(""); setDetails(""); }}
          >
            Add Skill Category
          </button>
        </>
      )}

      {action === "modify" && (
        <>
          {labels.length ? (
            <>
              <label>
                Category to modify
                <select value={selectedLabel} onChange={(e) => setSelectedLabel(e.target.value)}>
                  {labels.map((l) => <option key={l}>{l}</option>)}
                </select>
              </label>
              <label>
                Skills (comma-separated)
                <input value={modifyDetails} placeholder="e.g., Python, Java, C++" onChange={(e) => setModifyDetails(e.target.value)} />
              </label>
              <button
                type="button"
                className="liquid-btn solid"
                onClick={() => onApply([{ section: "skills", item_name: selectedLabel, field: "", new_value: modifyDetails }])}
              >
                Save {selectedLabel}
              </button>
            </>
          ) : (
            <p className="muted">No skill categories in this document yet.</p>
          )}
        </>
      )}

      {action === "append" && (
        <>
          {labels.length ? (
            <>
              <label>
                Existing category
                <select value={selectedLabel} onChange={(e) => setSelectedLabel(e.target.value)}>
                  {labels.map((l) => <option key={l}>{l}</option>)}
                </select>
              </label>
              {selectedLabel && (
                <label>
                  Current skills
                  <input
                    type="text"
                    readOnly
                    style={{ opacity: 0.6, cursor: "default" }}
                    value={skills.find((s) => s.label === selectedLabel)?.details || ""}
                  />
                </label>
              )}
              <label>
                Skills to append (comma-separated)
                <input value={appendDetails} placeholder="e.g., Rust, TypeScript" onChange={(e) => setAppendDetails(e.target.value)} />
              </label>
              <button
                type="button"
                className="liquid-btn solid"
                onClick={() => { onAppendSkill(selectedLabel, appendDetails); setAppendDetails(""); }}
              >
                Append to {selectedLabel}
              </button>
            </>
          ) : (
            <p className="muted">No skill categories in this document yet.</p>
          )}
        </>
      )}

      {action === "remove" && (
        <>
          {labels.length ? (
            <>
              <label>
                Category to remove
                <select value={selectedLabel} onChange={(e) => setSelectedLabel(e.target.value)}>
                  {labels.map((l) => <option key={l}>{l}</option>)}
                </select>
              </label>
              {selectedLabel && (
                <label>
                  Current skills
                  <input
                    type="text"
                    readOnly
                    style={{ opacity: 0.6, cursor: "default" }}
                    value={skills.find((s) => s.label === selectedLabel)?.details || ""}
                  />
                </label>
              )}
              <button
                type="button"
                className="liquid-btn btn-danger"
                onClick={() => onRemoveSkill(selectedLabel)}
              >
                Remove {selectedLabel}
              </button>
            </>
          ) : (
            <p className="muted">No skill categories in this document yet.</p>
          )}
        </>
      )}
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
  const [theme, setTheme] = useState("");
  const [idInput, setIdInput] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [activeSection, setActiveSection] = useState("edit");
  const [editCategory, setEditCategory] = useState("contact");
  const [savedProjects, setSavedProjects] = useState([]);
  const [savedDocs, setSavedDocs] = useState([]);

  const [rendering, setRendering] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [themePreviewOpen, setThemePreviewOpen] = useState(false);
  const [downloadName, setDownloadName] = useState("");

  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => setMessage(""), 5000);
    return () => clearTimeout(t);
  }, [message]);

  useEffect(() => {
    let ignore = false;
    async function loadProjects() {
      try {
        const data = await fetchProjects();
        if (!ignore) setSavedProjects(Array.isArray(data) ? data : []);
      } catch {
        if (!ignore) setSavedProjects([]);
      }
    }
    async function loadDocs() {
      try {
        const data = isResume ? await fetchResumes() : await fetchPortfolios();
        if (!ignore) setSavedDocs(Array.isArray(data) ? data : []);
      } catch {
        if (!ignore) setSavedDocs([]);
      }
    }
    loadProjects();
    loadDocs();
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
  async function safeAction(fn, success = "Updated.", skipRefresh = false) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      await fn();
      setMessage(success);
      if (!skipRefresh && docId) await refresh(docId);
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
    if (!theme) {
      setError("Theme is required.");
      return;
    }

    await safeAction(async () => {
      const res = isResume ? await generateResume(name.trim(), theme) : await generatePortfolio(name.trim(), theme);
      const id = isResume ? res.resume_id : res.portfolio_id;
      setDocId(id);
      setIdInput(id);
      const data = isResume ? await fetchResume(id) : await fetchPortfolio(id);
      setDoc(data);
      const merged = [id, ...readRecentIds().filter((x) => x !== id)].slice(0, 10);
      saveRecentIds(merged);
      const listFn = isResume ? fetchResumes : fetchPortfolios;
      try {
        const docs = await listFn();
        setSavedDocs(Array.isArray(docs) ? docs : []);
      } catch {
        // non-critical — status card will show "—" if list fetch fails
      }
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
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const data = isResume ? await fetchResume(id.trim()) : await fetchPortfolio(id.trim());
      setDocId(id.trim());
      setDoc(data);
      setIdInput(id.trim());
      setMessage(`${isResume ? "Resume" : "Portfolio"} loaded.`);
    } catch (err) {
      const isNotFound = err.status === 404;
      const existing = readRecentIds();
      const wasRecent = existing.includes(id.trim());
      if (isNotFound && wasRecent) {
        saveRecentIds(existing.filter((x) => x !== id.trim()));
        setMessage("Removed stale document ID.");
        const listFn = isResume ? fetchResumes : fetchPortfolios;
        listFn().then((d) => setSavedDocs(Array.isArray(d) ? d : [])).catch(() => {});
      } else {
        setError(err.message || "Request failed.");
      }
    } finally {
      setBusy(false);
    }
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
      saveRecentIds(readRecentIds().filter((x) => x !== docId));
      setDocId("");
      setDoc(null);
      setIdInput("");
      const listFn = isResume ? fetchResumes : fetchPortfolios;
      listFn().then((d) => setSavedDocs(Array.isArray(d) ? d : [])).catch(() => {});
    }, `${isResume ? "Resume" : "Portfolio"} deleted.`, true);
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

  async function onAddProjectAI(projectName) {
    if (!docId || !projectName) return;
    await safeAction(async () => {
      if (isResume) await addResumeProjectAI(docId, projectName);
      else await addPortfolioProjectAI(docId, projectName);
    }, "Project added with AI.");
  }

  async function onAddSkill(payload) {
    if (!docId) return;
    await safeAction(async () => {
      if (isResume) await addResumeSkill(docId, payload);
      else await addPortfolioSkill(docId, payload);
    }, "Skill category added.");
  }

  async function onAppendSkill(label, details) {
    if (!docId) return;
    await safeAction(async () => {
      if (isResume) await appendResumeSkill(docId, label, details);
      else await appendPortfolioSkill(docId, label, details);
    }, "Skills appended.");
  }

  async function onRemoveSkill(label) {
    if (!docId) return;
    await safeAction(async () => {
      if (isResume) await removeResumeSkill(docId, label);
      else await removePortfolioSkill(docId, label);
    }, "Skill category removed.");
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
        await removeResumeProject(docId, projectName);
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
      const ext = format === "markdown" ? "md" : format;
      const base = downloadName.trim() || `${kind}_${docId}`;
      downloadBlob(blob, `${base}.${ext}`);
    } catch (err) {
      setError(err.message || "Render failed.");
    } finally {
      setRendering(false);
    }
  }

  async function onPreview() {
    if (!docId) return;
    setRendering(true);
    setError("");
    try {
      const blob = isResume ? await renderResume(docId, "pdf") : await renderPortfolio(docId, "pdf");
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError(err.message || "Preview failed.");
    } finally {
      setRendering(false);
    }
  }

  function closePreview() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
  }

  const [recentIds, setRecentIds] = useState([]);

  function readRecentIds() {
    if (typeof window === "undefined") return [];
    const key = isResume ? "recentResumeIds" : "recentPortfolioIds";
    try {
      const parsed = JSON.parse(window.localStorage.getItem(key) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function saveRecentIds(ids) {
    const key = isResume ? "recentResumeIds" : "recentPortfolioIds";
    window.localStorage.setItem(key, JSON.stringify(ids));
    setRecentIds(ids);
  }

  useEffect(() => {
    setRecentIds(readRecentIds());
  }, [isResume]);

  const activeDoc = savedDocs.find((d) => d.id === docId);
  const createdAtText = activeDoc?.created_at ? new Date(activeDoc.created_at).toLocaleString() : "—";
  const hasActiveId = Boolean(docId);
  const hasCreatedAt = Boolean(activeDoc?.created_at);

  if (mode === "public") {
    return (
      <div className="page-stack workspace-page">
        <div className="grid two-col">
          <GlassCard title={`${isResume ? "Resume" : "Portfolio"} ID`} hint="Public mode is view + download only.">
            <div className="form-stack">
              <div className="settings-list compact">
                <label className="settings-row settings-field-row">
                  <span className="settings-label">Name</span>
                  <select
                    className="settings-control"
                    value={idInput}
                    onChange={(e) => setIdInput(e.target.value)}
                  >
                    <option value="">{SELECT_PLACEHOLDER}</option>
                    {savedDocs.map((doc) => (
                      <option key={doc.id} value={doc.id}>{doc.name}{doc.created_at ? ` (${new Date(doc.created_at).toLocaleDateString()})` : ""}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="button-row">
                <button type="button" className="liquid-btn solid" disabled={busy} onClick={() => onLoad(idInput)}>
                  {busy ? "Loading..." : `Load ${isResume ? "Resume" : "Portfolio"}`}
                </button>
              </div>
              {recentIds.length ? (
                <div className="button-row">
                  {recentIds.map((id) => {
                    const found = savedDocs.find((d) => d.id === id);
                    const label = `${id}${found?.created_at ? ` (${new Date(found.created_at).toLocaleDateString()})` : ""}`;
                    return (
                      <button key={id} type="button" className="liquid-btn" onClick={() => { setIdInput(id); onLoad(id); }}>
                        {label}
                      </button>
                    );
                  })}
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
        <GlassCard
          className="resume-controls-card"
          title={`${isResume ? "Resume" : "Portfolio"} Controls`}
          hint={`Create or load a document. ${savedDocs.length} ${isResume ? "resume" : "portfolio"}${savedDocs.length !== 1 ? "s" : ""} saved.`}
        >
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
                  <option value="">{SELECT_PLACEHOLDER}</option>
                  {THEMES.map((item) => <option key={item}>{item}</option>)}
                </select>
              </label>
            </div>
            <div className="button-row">
              <button type="button" className="liquid-btn" disabled={!theme} onClick={() => setThemePreviewOpen(true)}>
                Preview
              </button>
              <button type="button" className="liquid-btn solid btn-success" disabled={busy || !theme} onClick={onGenerate}>
                Generate {isResume ? "Resume" : "Portfolio"}
              </button>
            </div>

            <div className="settings-list compact">
              <label className="settings-row settings-field-row">
                <span className="settings-label">Load by name</span>
                <select
                  className="settings-control"
                  value={idInput}
                  onChange={(e) => setIdInput(e.target.value)}
                  disabled={savedDocs.length === 0}
                >
                  <option value="">{SELECT_PLACEHOLDER}</option>
                  {savedDocs.map((doc) => (
                    <option key={doc.id} value={doc.id}>{doc.name}{doc.created_at ? ` (${new Date(doc.created_at).toLocaleDateString()})` : ""}</option>
                  ))}
                </select>
              </label>
              {savedDocs.length === 0 && (
                <p className="warning"><span aria-hidden="true">⚠ </span>No saved {isResume ? "resumes" : "portfolios"} found. Generate one above to get started.</p>
              )}
            </div>
            <div className="button-row">
              <button type="button" className="liquid-btn solid" disabled={busy} onClick={() => onLoad(idInput)}>
                Load
              </button>
            </div>
            {recentIds.length ? (
              <div className="button-row">
                {recentIds.slice(0, 3).map((id) => {
                  const found = savedDocs.find((d) => d.id === id);
                  const label = `${id}${found?.created_at ? ` (${new Date(found.created_at).toLocaleDateString()})` : ""}`;
                  return (
                    <button key={id} type="button" className="liquid-btn" onClick={() => { setIdInput(id); onLoad(id); }}>
                      {label}
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>
        </GlassCard>

        <GlassCard title="Status" hint="Current document and actions.">
          <div className="form-stack">
            <div className="settings-list compact">
              <div className={`settings-row ${hasActiveId ? "status-ok" : "status-missing"}`.trim()}>
                <span className="settings-label">Active ID</span>
                <strong className="settings-value">{docId || "None"}</strong>
              </div>
              <div className={`settings-row ${hasCreatedAt ? "status-ok" : "status-missing"}`.trim()}>
                <span className="settings-label">Created</span>
                <strong className="settings-value">{createdAtText}</strong>
              </div>
              <div className="settings-row status-ok">
                <span className="settings-label">Mode</span>
                <strong className="settings-value">{mode === "private" ? "Private" : "Public"}</strong>
              </div>
            </div>
            <div className="button-row">
              <button type="button" className="liquid-btn" onClick={() => { setDocId(""); setDoc(null); setIdInput(""); }}>
                Close
              </button>
              <button type="button" className="liquid-btn solid btn-danger" disabled={!docId || busy} onClick={onDelete}>
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
                  { value: "skills", label: "Skills" },
                  ...(isResume ? [{ value: "career", label: "Education + Experience" }] : [])
                ]}
              />

              {editCategory === "contact" ? <EditContact doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "summary" ? <EditSummary doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "theme" ? <EditTheme doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "connections" ? <ConnectionsEditor doc={doc} onApply={onApplyEdits} /> : null}
              {editCategory === "skills" ? (
                <SkillsEditor
                  doc={doc}
                  onAddSkill={onAddSkill}
                  onAppendSkill={onAppendSkill}
                  onRemoveSkill={onRemoveSkill}
                  onApply={onApplyEdits}
                />
              ) : null}
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
              onAddProjectAI={onAddProjectAI}
              onEditProject={(projectName, field, value) => onApplyEdits([{ section: "projects", item_name: projectName, field, new_value: value }])}
              onRemoveProject={onRemoveProject}
              allowRoleOverride={!isResume}
              busy={busy}
            />
          ) : null}

          {activeSection === "download" ? (
            <GlassCard title="Render + Download">
              <div className="form-stack">
                <div style={{ maxWidth: "600px" }}>
                  <label className="settings-row settings-field-row">
                    <span className="settings-label">File name</span>
                    <input
                      className="settings-control"
                      value={downloadName}
                      onChange={(e) => setDownloadName(e.target.value)}
                      placeholder={`${kind}_${docId} (default)`}
                      style={{ minWidth: "300px" }}
                    />
                  </label>
                </div>
                <div className="button-row">
                  <button type="button" className="liquid-btn solid btn-success" disabled={rendering} onClick={onPreview}>
                    {rendering ? "Rendering..." : "Preview PDF"}
                  </button>
                  {FORMATS.map((format) => (
                    <button key={format} type="button" className="liquid-btn solid btn-success" disabled={rendering} onClick={() => onRender(format)}>
                      {rendering ? "Rendering..." : `Download ${format.toUpperCase()}`}
                    </button>
                  ))}
                </div>
              </div>
            </GlassCard>
          ) : null}
        </>
      ) : null}

      {previewUrl && typeof document !== "undefined" ? createPortal(
        <div style={{ position: "fixed", inset: 0, zIndex: 9999, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem 1rem", background: "var(--bg-1)", flexShrink: 0, borderBottom: "1px solid var(--line)" }}>
            <strong style={{ color: "var(--ink-0)" }}>Preview — {isResume ? "Resume" : "Portfolio"}</strong>
            <button type="button" className="liquid-btn" onClick={closePreview}>✕ Close</button>
          </div>
          <iframe
            src={`${previewUrl}#toolbar=1&zoom=100`}
            style={{ flex: 1, border: "none", width: "100%", minHeight: 0 }}
            title="Document Preview"
          />
        </div>,
        document.body
      ) : null}
    {themePreviewOpen && (
      <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <div style={{ background: "var(--bg-0)", border: "1px solid var(--line)", borderRadius: "var(--control-radius)", padding: "16px", width: "min(90vw, 900px)", height: "80vh", display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 600 }}>Theme Preview — {theme}</span>
            <button type="button" className="liquid-btn" onClick={() => setThemePreviewOpen(false)}>Close</button>
          </div>
          <iframe key={theme} src={`/theme-previews/${theme}.pdf`} style={{ flex: 1, border: "none", borderRadius: "var(--control-radius)", width: "100%" }} title="Theme Preview" />
        </div>
      </div>
    )}
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
