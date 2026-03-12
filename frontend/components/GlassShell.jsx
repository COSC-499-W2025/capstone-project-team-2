import Link from "next/link";
import { navItems } from "./glass-data";

/**
 * Legacy shell module.
 *
 * Retained for compatibility with older pages and reference layouts.
 */

/**
 * Legacy shell component preserved for compatibility with earlier
 * page structures. Provides a decorative backdrop, header, dock nav,
 * and content wrapper.
 *
 * @param {{
 *   title: string,
 *   subtitle: string,
 *   children: import("react").ReactNode
 * }} props
 * @returns {JSX.Element}
 */
export function GlassShell({ title, subtitle, children }) {
  return (
    <div className="scene">
      <div className="backdrop-orb orb-a" aria-hidden="true" />
      <div className="backdrop-orb orb-b" aria-hidden="true" />
      <div className="backdrop-orb orb-c" aria-hidden="true" />
      <main className="glass-app">
        <header className="glass-header">
          <div>
            <p className="eyebrow">Project Frontend</p>
            <h1>{title}</h1>
            <p className="subtitle">{subtitle}</p>
          </div>
          <span className="status-pill">Unified UI</span>
        </header>
        <nav className="glass-dock" aria-label="Primary Navigation">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="dock-item">
              {item.label}
            </Link>
          ))}
        </nav>
        {children}
      </main>
    </div>
  );
}

/**
 * Basic card wrapper used by legacy shell pages.
 *
 * @param {{
 *   title?: string,
 *   body?: string,
 *   children?: import("react").ReactNode
 * }} props
 * @returns {JSX.Element}
 */
export function GlassCard({ title, body, children }) {
  return (
    <article className="glass-card">
      {title ? <h2>{title}</h2> : null}
      {body ? <p>{body}</p> : null}
      {children}
    </article>
  );
}
