"use client";

/**
 * Home route module.
 *
 * This page provides a concise overview of the project workflow and
 * highlights the operational scope of the interface.
 */
import { LiquidShell, GlassCard } from "../components/LiquidShell";

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
