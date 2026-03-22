"use client";

/**
 * Home route module.
 *
 * This page provides a concise overview of the project workflow and
 * highlights the operational scope of the interface.
 */
import { LiquidShell, GlassCard } from "../components/LiquidShell";
import Link from "next/link";

/**
 * Home route that introduces the project workflow and core capabilities.
 *
 * @returns {JSX.Element} Home dashboard shell.
 */
export default function HomePage() {
  return (
    <LiquidShell
      title="Project Workspace"
      subtitle="Analyze repositories, review insights, and build resume/portfolio artifacts from one interface."
    >
      <div className="page-stack">
        <div className="grid two-col">
          <GlassCard title="Start Here" hint="Follow this order to keep the workflow consistent.">
            <ol className="clean-list">
              <li>Set consent and profile preferences.</li>
              <li>Upload a project archive or folder.</li>
              <li>Review and manage analyzed projects.</li>
              <li>Use dashboard insights to prioritize content.</li>
              <li>Build resume and portfolio documents in Workspace.</li>
            </ol>
            <div className="button-row">
              <Link href="/config" className="liquid-btn solid">Go to Settings</Link>
              <Link href="/upload" className="liquid-btn">Go to Upload</Link>
              <Link href="/workspace" className="liquid-btn">Go to Workspace</Link>
            </div>
          </GlassCard>

          <GlassCard title="Workflow Coverage" hint="Complete end-to-end project and document operations.">
            <ul className="clean-list">
              <li>Upload ZIP or folder and run analysis.</li>
              <li>Inspect dashboard skill and activity signals.</li>
              <li>Create, edit, and download resume and portfolio docs.</li>
              <li>Manage user consent and profile preferences.</li>
            </ul>
          </GlassCard>
        </div>
      </div>
    </LiquidShell>
  );
}
