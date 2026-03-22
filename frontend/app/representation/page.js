"use client";

/**
 * Representation preferences route module.
 *
 * Purpose:
 * - hydrate persisted representation preferences,
 * - expose project ordering/showcase controls,
 * - and persist updates through backend representation endpoints.
 */
import { useEffect, useMemo, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import {
  fetchRepresentationPreferences,
  fetchRepresentationProjects,
  updateRepresentationPreferences
} from "../../lib/api";
import {
  DEFAULT_REPRESENTATION_PREFERENCES,
  buildChronologyPayload,
  filterAvailableProjects,
  formatChronologyInputs,
  formatDateLabel,
  mergeProjectOrder,
  normalizeRepresentationPreferences,
  parseListInput
} from "./helpers";

/**
 * Representation preferences route for project ordering and emphasis controls.
 *
 * @returns {JSX.Element}
 */
export default function RepresentationPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [projectsWarning, setProjectsWarning] = useState("");
  const [message, setMessage] = useState("");
  const [currentRepresentation, setCurrentRepresentation] = useState(DEFAULT_REPRESENTATION_PREFERENCES);
  const [representationProjects, setRepresentationProjects] = useState([]);
  const [projectOrder, setProjectOrder] = useState([]);
  const [highlightSkillsInput, setHighlightSkillsInput] = useState("");
  const [showcaseProjects, setShowcaseProjects] = useState([]);
  const [chronologyInputs, setChronologyInputs] = useState({});

  useEffect(() => {
    let ignore = false;

    async function loadRepresentationData() {
      setLoading(true);
      setError("");
      setProjectsWarning("");
      try {
        const preferences = normalizeRepresentationPreferences(await fetchRepresentationPreferences());
        let projectPayload = { projects: [] };
        try {
          projectPayload = await fetchRepresentationProjects();
        } catch (err) {
          projectPayload = { projects: [] };
          if (!ignore) {
            setProjectsWarning(err?.message || "Failed to load representation project insights.");
          }
        }
        if (ignore) return;

        const projects = Array.isArray(projectPayload?.projects) ? projectPayload.projects : [];
        setRepresentationProjects(projects);
        const mergedProjectOrder = mergeProjectOrder(preferences.project_order, projects);
        const filteredShowcaseProjects = filterAvailableProjects(preferences.showcase_projects, projects);
        setCurrentRepresentation({
          ...preferences,
          project_order: mergedProjectOrder,
          showcase_projects: filteredShowcaseProjects
        });
        setProjectOrder(mergedProjectOrder);
        setHighlightSkillsInput((preferences.highlight_skills || []).join(", "));
        setShowcaseProjects(filteredShowcaseProjects);
        setChronologyInputs(formatChronologyInputs(preferences.chronology_corrections));
      } catch (err) {
        if (!ignore) setError(err.message || "Failed to load representation preferences.");
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    loadRepresentationData();

    return () => {
      ignore = true;
    };
  }, []);

  async function savePreferences(payload) {
    if (saving) return;
    setSaving(true);
    setProjectsWarning("");
    setError("");
    setMessage("");

    try {
      const updated = normalizeRepresentationPreferences(await updateRepresentationPreferences(payload));
      let projectPayload = { projects: [] };
      let warning = "";
      try {
        projectPayload = await fetchRepresentationProjects();
      } catch (err) {
        projectPayload = { projects: [] };
        warning = err?.message || "Preferences were saved, but project insights could not be refreshed.";
      }

      const projects = Array.isArray(projectPayload?.projects) ? projectPayload.projects : [];
      setRepresentationProjects(projects);
      const mergedProjectOrder = mergeProjectOrder(updated.project_order, projects);
      const filteredShowcaseProjects = filterAvailableProjects(updated.showcase_projects, projects);
      setCurrentRepresentation({
        ...updated,
        project_order: mergedProjectOrder,
        showcase_projects: filteredShowcaseProjects
      });
      setProjectOrder(mergedProjectOrder);
      setHighlightSkillsInput((updated.highlight_skills || []).join(", "));
      setShowcaseProjects(filteredShowcaseProjects);
      setChronologyInputs(formatChronologyInputs(updated.chronology_corrections));
      if (warning) {
        setProjectsWarning(warning);
        setMessage("Representation preferences saved with warnings.");
      } else {
        setMessage("Representation preferences saved.");
      }
    } catch (err) {
      setError(err.message || "Failed to save representation preferences.");
    } finally {
      setSaving(false);
    }
  }

  async function onSaveSkills(event) {
    event.preventDefault();
    const payload = {
      highlight_skills: parseListInput(highlightSkillsInput)
    };
    await savePreferences(payload);
  }

  async function onSaveProjects(event) {
    event.preventDefault();
    const payload = {
      project_order: projectOrder,
      chronology_corrections: buildChronologyPayload(chronologyInputs),
      showcase_projects: showcaseProjects
    };
    await savePreferences(payload);
  }

  function moveProject(projectName, direction) {
    setProjectOrder((current) => {
      const index = current.indexOf(projectName);
      if (index < 0) return current;
      const nextIndex = direction === "up" ? index - 1 : index + 1;
      if (nextIndex < 0 || nextIndex >= current.length) return current;
      const next = [...current];
      [next[index], next[nextIndex]] = [next[nextIndex], next[index]];
      return next;
    });
  }

  function toggleShowcaseProject(projectName) {
    setShowcaseProjects((current) => (
      current.includes(projectName)
        ? current.filter((name) => name !== projectName)
        : [...current, projectName]
    ));
  }

  function toggleHighlightedSkill(skill) {
    const current = parseListInput(highlightSkillsInput);
    const next = current.includes(skill)
      ? current.filter((item) => item !== skill)
      : [...current, skill];
    setHighlightSkillsInput(next.join(", "));
  }

  const projectMeta = useMemo(() => {
    const meta = new Map();
    for (const project of representationProjects) {
      if (project?.project_name) meta.set(project.project_name, project);
    }
    return meta;
  }, [representationProjects]);

  const availableSkills = useMemo(() => {
    const skills = new Set();
    for (const project of representationProjects) {
      for (const skill of Array.isArray(project?.skills) ? project.skills : []) {
        if (skill) skills.add(skill);
      }
    }
    return [...skills].sort((a, b) => a.localeCompare(b));
  }, [representationProjects]);

  const currentHighlightedSkills = currentRepresentation.highlight_skills || [];
  const currentShowcaseProjects = currentRepresentation.showcase_projects || [];
  const chronologyCount = Object.keys(currentRepresentation.chronology_corrections || {}).length;

  return (
    <LiquidShell
      title="Representation Preferences"
      subtitle="Control project order, chronology corrections, highlighted skills, and showcase selections."
    >
      <div className="page-stack representation-page">
        {loading ? <p className="muted">Loading representation preferences...</p> : null}
        {error ? <p className="error">{error}</p> : null}
        {projectsWarning ? <p className="muted">{projectsWarning}</p> : null}
        {message ? <p className="success">{message}</p> : null}

        <div className="grid two-col config-grid">
          <GlassCard title="Current Representation">
            {!loading ? (
              <>
                <p className="muted">These preferences control project ordering and showcase emphasis across insights.</p>
                <div className="settings-list">
                  <div className={`settings-row ${((currentRepresentation.project_order?.length || 0) > 0) ? "status-ok" : "status-missing"}`.trim()}>
                    <span className="settings-label">Ordered projects</span>
                    <strong className="settings-value">{currentRepresentation.project_order?.length || 0}</strong>
                  </div>
                  <div className="settings-row status-ok">
                    <span className="settings-label">Chronology corrections</span>
                    <strong className="settings-value">{chronologyCount}</strong>
                  </div>
                  <div className={`settings-row ${currentHighlightedSkills.length ? "status-ok" : "status-missing"}`.trim()}>
                    <span className="settings-label">Highlighted skills</span>
                    <strong className="settings-value">{currentHighlightedSkills.length ? currentHighlightedSkills.join(", ") : "Not set"}</strong>
                  </div>
                  <div className={`settings-row ${currentShowcaseProjects.length ? "status-ok" : "status-missing"}`.trim()}>
                    <span className="settings-label">Showcase projects</span>
                    <strong className="settings-value">{currentShowcaseProjects.length ? currentShowcaseProjects.join(", ") : "Not set"}</strong>
                  </div>
                </div>
              </>
            ) : null}
          </GlassCard>

          <GlassCard title="Highlighted Skills">
            <p className="muted">Choose the skills that should be emphasized across representation views.</p>
            <form onSubmit={onSaveSkills} className="form-stack">
              <label>
                Highlighted skills (comma-separated)
                <textarea
                  rows={3}
                  value={highlightSkillsInput}
                  placeholder="e.g., FastAPI, Next.js, React"
                  onChange={(e) => setHighlightSkillsInput(e.target.value)}
                />
              </label>

              {availableSkills.length ? (
                <div className="settings-list compact">
                  {availableSkills.map((skill) => {
                    const selected = parseListInput(highlightSkillsInput).includes(skill);
                    return (
                      <label key={skill} className="settings-row settings-field-row">
                        <span className="settings-label">{skill}</span>
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() => toggleHighlightedSkill(skill)}
                        />
                      </label>
                    );
                  })}
                </div>
              ) : (
                <p className="muted">Analyze at least one project to get skill suggestions from `/representation/projects`.</p>
              )}

              <div className="button-row">
                <button type="submit" className="liquid-btn solid" disabled={loading || saving}>
                  {saving ? "Saving..." : "Save Representation Preferences"}
                </button>
              </div>
            </form>
          </GlassCard>
        </div>

        <GlassCard title="Project Order + Showcase">
          <p className="muted">Reorder projects, mark showcase entries, and optionally override `analyzed_at` values for chronology fixes.</p>
          {projectOrder.length ? (
            <form onSubmit={onSaveProjects} className="settings-list">
              {projectOrder.map((projectName, index) => {
                const project = projectMeta.get(projectName);
                const skills = Array.isArray(project?.skills) ? project.skills.slice(0, 4).join(", ") : "";
                return (
                  <div
                    key={projectName}
                    className="settings-row representation-project-row"
                  >
                    <div className="representation-project-header">
                      <div className="representation-project-meta">
                        <strong className="settings-value">{projectName}</strong>
                        <p className="muted representation-project-subtext">
                          Analyzed: {formatDateLabel(project?.analyzed_at)}
                        </p>
                        <p className="muted representation-project-skills">
                          Skills: {skills || "No detected skills"}
                        </p>
                      </div>

                      <div className="representation-project-actions">
                        <button
                          type="button"
                          className="liquid-btn"
                          disabled={index === 0}
                          onClick={() => moveProject(projectName, "up")}
                        >
                          Move Up
                        </button>
                        <button
                          type="button"
                          className="liquid-btn"
                          disabled={index === projectOrder.length - 1}
                          onClick={() => moveProject(projectName, "down")}
                        >
                          Move Down
                        </button>
                        <label className="representation-showcase-toggle">
                          <input
                            type="checkbox"
                            checked={showcaseProjects.includes(projectName)}
                            onChange={() => toggleShowcaseProject(projectName)}
                          />
                          Showcase
                        </label>
                      </div>
                    </div>

                    <label className="representation-chronology-field">
                      Chronology correction (`analyzed_at`)
                      <p className="muted representation-chronology-hint">
                        Use the date/time picker. Leave blank to keep the detected analyzed date.
                      </p>
                      <input
                        type="datetime-local"
                        step="1"
                        className="representation-chronology-input"
                        value={chronologyInputs[projectName] || ""}
                        onChange={(e) => setChronologyInputs((current) => ({
                          ...current,
                          [projectName]: e.target.value
                        }))}
                      />
                    </label>
                  </div>
                );
              })}

              <div className="button-row">
                <button type="submit" className="liquid-btn solid" disabled={loading || saving}>
                  {saving ? "Saving..." : "Save Representation Preferences"}
                </button>
              </div>
            </form>
          ) : (
            <p className="muted">No analyzed projects are available yet. Run analysis first, then return here to configure ordering and showcase preferences.</p>
          )}
        </GlassCard>
      </div>
    </LiquidShell>
  );
}
