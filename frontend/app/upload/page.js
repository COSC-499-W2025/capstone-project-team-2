"use client";

/**
 * Upload route module.
 *
 * This route supports two ingestion flows:
 * - direct ZIP upload,
 * - folder selection with client-side ZIP creation.
 * Both converge into a shared backend analysis pipeline.
 */
import { useState } from "react";
import JSZip from "jszip";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { LiquidSegmentedControl } from "../../components/LiquidPillControl";
import { analyzeUploadedProject, fetchProjectInsights, uploadProjectZip } from "../../lib/api";

function AnalysisProgress() {
  return (
    <div className="analysis-progress" aria-live="polite">
      <div className="analysis-progress-track" aria-hidden="true">
        <div className="analysis-progress-fill" />
      </div>
      <p className="muted analysis-progress-label">Analyzing project. This can take a moment.</p>
    </div>
  );
}

/**
 * Renders the analysis summary widgets once a project insight object
 * is available from the backend pipeline.
 *
 * @param {{ insight: Record<string, any> }} props
 * @returns {JSX.Element | null}
 */
function InsightPreview({ insight }) {
  if (!insight) return null;
  const stats = insight.stats || {};
  const fileAnalysis = insight.file_analysis || {};
  const contributors = insight.contributors || {};

  return (
    <div className="grid two-col">
      <GlassCard title="Analysis Summary">
        <p><strong>Project:</strong> {insight.project_name || "Unknown"}</p>
        <p><strong>Type:</strong> {String(insight.project_type || "unknown")}</p>
        <p><strong>Duration Estimate:</strong> {insight.duration_estimate || "—"}</p>
        <p><strong>Skills Detected:</strong> {stats.skill_count || 0}</p>
      </GlassCard>

      <GlassCard title="Signals">
        <p><strong>Languages:</strong> {(insight.languages || []).join(", ") || "None"}</p>
        <p><strong>Frameworks:</strong> {(insight.frameworks || []).join(", ") || "None"}</p>
        <p><strong>Skills:</strong> {(insight.skills || []).join(", ") || "None"}</p>
      </GlassCard>

      <GlassCard title="File Analysis">
        <p>Total files: {fileAnalysis.file_count ?? "—"}</p>
        <p>Total size: {fileAnalysis.total_size_bytes ?? 0} bytes</p>
        <p>Avg size: {fileAnalysis.average_size_bytes ?? 0} bytes</p>
      </GlassCard>

      <GlassCard title="Contributors">
        {Object.keys(contributors).length ? (
          <ul className="clean-list">
            {Object.entries(contributors).map(([name, count]) => (
              <li key={name}>{name}: {count} file(s)</li>
            ))}
          </ul>
        ) : (
          <p className="muted">No contributors listed.</p>
        )}
      </GlassCard>
    </div>
  );
}

/**
 * Upload route that supports two ingestion modes:
 * 1) direct ZIP upload
 * 2) local folder compression followed by upload
 *
 * After upload, the page triggers analysis and renders the newest
 * matching insight payload.
 *
 * @returns {JSX.Element}
 */
export default function UploadPage() {
  /**
   * View state for upload mode, file selection, async lifecycle, and
   * latest resulting insight payload.
   */
  const [tab, setTab] = useState("zip");
  const [zipFile, setZipFile] = useState(null);
  const [folderFiles, setFolderFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [insight, setInsight] = useState(null);
  const pipelineStateClass = loading || success ? "status-ok" : "status-missing";

  /**
   * Triggers backend analysis and stores the latest matching
   * project insight payload in local state.
   *
   * @param {string} projectName
   * @returns {Promise<void>}
   */
  async function finalizeAnalysis(projectName) {
    await analyzeUploadedProject(projectName);
    const insights = await fetchProjectInsights();
    const matches = Array.isArray(insights)
      ? insights.filter((item) => item?.project_name === projectName)
      : [];
    setInsight(matches.length ? matches[matches.length - 1] : null);
  }

  /**
   * Handles the ZIP upload analysis flow.
   *
   * @returns {Promise<void>}
   */
  async function onAnalyzeZip() {
    if (!zipFile) {
      setError("Choose a .zip file first.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");
    setInsight(null);

    try {
      const upload = await uploadProjectZip(zipFile);
      const projectName = upload?.project_name || zipFile.name.replace(/\.zip$/i, "");
      await finalizeAnalysis(projectName);
      setSuccess(`Analysis complete for ${projectName}.`);
    } catch (err) {
      setError(err.message || "Upload/analyze failed.");
    } finally {
      setLoading(false);
    }
  }

  /**
   * Handles folder selection flow by zipping files client-side
   * and sending the generated archive to the upload endpoint.
   *
   * @returns {Promise<void>}
   */
  async function onAnalyzeFolder() {
    if (!folderFiles.length) {
      setError("Select a folder first.");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");
    setInsight(null);

    try {
      const zip = new JSZip();
      for (const file of folderFiles) {
        const rel = file.webkitRelativePath || file.name;
        const data = await file.arrayBuffer();
        zip.file(rel, data);
      }
      const blob = await zip.generateAsync({ type: "blob", compression: "DEFLATE" });

      const firstRel = folderFiles[0]?.webkitRelativePath || "project";
      const root = firstRel.split("/")[0] || "project";
      const zipName = `${root}.zip`;
      const zipAsFile = new File([blob], zipName, { type: "application/zip" });

      const upload = await uploadProjectZip(zipAsFile, zipName);
      const projectName = upload?.project_name || root;
      await finalizeAnalysis(projectName);
      setSuccess(`Folder compressed and analyzed as ${projectName}.`);
    } catch (err) {
      setError(err.message || "Folder analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <LiquidShell
      title="Project Upload"
      subtitle="Upload ZIP or choose a local folder, run analysis, and review generated project insights."
    >
      <div className="page-stack upload-page">
        <LiquidSegmentedControl
          value={tab}
          onChange={setTab}
          options={[
            { value: "zip", label: "ZIP Upload" },
            { value: "folder", label: "Folder Upload" }
          ]}
        />

        <div className="grid two-col">
          {tab === "zip" ? (
            <GlassCard title="ZIP Upload" hint="Upload a compressed repository archive for analysis.">
              <label className="drop-zone">
                <input
                  type="file"
                  accept=".zip,application/zip"
                  onChange={(event) => setZipFile(event.target.files?.[0] || null)}
                />
                <span>{zipFile ? zipFile.name : "Drop .zip or click to browse"}</span>
              </label>
              <div className="button-row">
                <button type="button" className="liquid-btn solid" onClick={onAnalyzeZip} disabled={loading}>
                  {loading ? "Working..." : "Analyze ZIP"}
                </button>
              </div>
            </GlassCard>
          ) : (
            <GlassCard title="Folder Upload" hint="Upload a local folder through the browser and analyze it as one project.">
              <label className="drop-zone">
                <input
                  type="file"
                  webkitdirectory="true"
                  directory="true"
                  multiple
                  onChange={(event) => setFolderFiles(Array.from(event.target.files || []))}
                />
                <span>{folderFiles.length ? `${folderFiles.length} file(s) selected` : "Choose a folder"}</span>
              </label>
              <div className="button-row">
                <button type="button" className="liquid-btn solid" onClick={onAnalyzeFolder} disabled={loading}>
                  {loading ? "Compressing + analyzing..." : "Analyze Folder"}
                </button>
              </div>
            </GlassCard>
          )}

          <GlassCard title="Status" hint="Latest pipeline result.">
            <div className="settings-list compact">
              <div className={`settings-row ${pipelineStateClass}`.trim()}>
                <span className="settings-label">Pipeline</span>
                <strong className="settings-value">
                  {loading ? "Running analysis pipeline..." : (success ? "Completed" : "Idle")}
                </strong>
              </div>
            </div>
            {loading ? <AnalysisProgress /> : null}
            {error ? <p className="error">{error}</p> : null}
            {success ? <p className="success">{success}</p> : (!loading ? <p className="muted">No analysis run yet.</p> : null)}
          </GlassCard>
        </div>

        {insight ? <InsightPreview insight={insight} /> : null}
      </div>
    </LiquidShell>
  );
}
