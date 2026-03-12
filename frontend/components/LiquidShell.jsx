"use client";

/**
 * Shared shell components used by all primary app routes.
 *
 * Exports:
 * - `LiquidShell`: floating nav + title chrome + content wrapper.
 * - `GlassCard`: reusable card container with consistent spacing/styling.
 */
import { usePathname, useRouter } from "next/navigation";
import { LiquidPillNav, LiquidSegmentedControl } from "./LiquidPillControl";
import { useEffect, useMemo, useState } from "react";

/**
 * Route definitions for top-level navigation.
 * Visibility of routes is filtered by the selected audience mode.
 * @type {{href: string, label: string, modes: Array<"public" | "private">}[]}
 */
const links = [
  { href: "/", label: "Home", modes: ["public", "private"] },
  { href: "/dashboard", label: "Dashboard", modes: ["public", "private"] },
  { href: "/upload", label: "Upload", modes: ["private"] },
  { href: "/workspace", label: "Resume + Portfolio", modes: ["public", "private"] },
  { href: "/config", label: "User Config", modes: ["private"] }
];

/**
 * Shared page shell with floating navigation, theme handling, and
 * consistent header/content composition.
 *
 * @param {{
 *   title: string,
 *   subtitle: string,
 *   children: import("react").ReactNode,
 *   rightSlot?: import("react").ReactNode
 * }} props
 * @returns {JSX.Element}
 */
export function LiquidShell({ title, subtitle, children, rightSlot }) {
  const pathname = usePathname();
  const router = useRouter();
  /**
   * Audience mode drives route visibility in the top navigation.
   * Persisted in localStorage as `viewMode`.
   */
  const [viewMode, setViewMode] = useState("private");
  /**
   * UI theme token used by document-level CSS variables.
   * Persisted in localStorage as `uiTheme`.
   */
  const [theme, setTheme] = useState(() => {
    if (typeof document !== "undefined") {
      const current = document.documentElement.dataset.theme;
      if (current === "dark" || current === "light") return current;
    }
    return "light";
  });

  useEffect(() => {
    /**
     * One-time hydration of persisted mode + theme preferences.
     */
    const storedViewMode = window.localStorage.getItem("viewMode");
    if (storedViewMode === "public" || storedViewMode === "private") {
      setViewMode(storedViewMode);
    }

    const current = document.documentElement.dataset.theme;
    if (current === "dark" || current === "light") {
      setTheme(current);
      return;
    }
    const stored = window.localStorage.getItem("uiTheme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(stored === "dark" || stored === "light" ? stored : (systemPrefersDark ? "dark" : "light"));
  }, []);

  useEffect(() => {
    /**
     * Broadcasts visibility mode changes so nested pages can react without
     * prop drilling from route to route.
     */
    window.localStorage.setItem("viewMode", viewMode);
    window.dispatchEvent(new CustomEvent("viewModeChange", { detail: viewMode }));
  }, [viewMode]);

  useEffect(() => {
    /**
     * Applies theme directly on `<html>` so all CSS variable branches update
     * consistently across current and future mounted subtrees.
     */
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    window.localStorage.setItem("uiTheme", theme);
  }, [theme]);

  const filteredLinks = useMemo(
    () => links.filter((link) => link.modes.includes(viewMode)),
    [viewMode]
  );

  useEffect(() => {
    /**
     * Safety redirect: if current pathname is hidden under the selected mode,
     * push user to the first visible route.
     */
    if (!filteredLinks.length) return;
    const isVisible = filteredLinks.some((link) => link.href === pathname);
    if (!isVisible) {
      router.replace(filteredLinks[0].href);
    }
  }, [filteredLinks, pathname, router]);

  return (
    <div className="liquid-scene">
      <div className="liquid-orb orb-amber" aria-hidden="true" />
      <div className="liquid-orb orb-cyan" aria-hidden="true" />
      <div className="liquid-orb orb-rose" aria-hidden="true" />

      <div className="frost-noise" aria-hidden="true" />
      <div className="floating-nav-layer">
        <LiquidPillNav
          items={filteredLinks}
          activeHref={pathname}
          className="top-chrome"
          trailingContent={
            <div className="top-right-slot top-actions">
              <div className="nav-mode-toggle" role="group" aria-label="Navigation visibility mode">
                <LiquidSegmentedControl
                  options={[
                    { value: "private", label: "Private" },
                    { value: "public", label: "Public" }
                  ]}
                  value={viewMode}
                  onChange={setViewMode}
                />
              </div>
              {rightSlot ? <div>{rightSlot}</div> : null}
              <button
                type="button"
                className="theme-toggle liquid-btn"
                aria-label="Toggle color theme"
                onClick={() => setTheme((prev) => (prev === "dark" ? "light" : "dark"))}
              >
                <span className="theme-icon" aria-hidden="true" suppressHydrationWarning>
                  {theme === "dark" ? "☀" : "☾"}
                </span>
              </button>
            </div>
          }
        />
      </div>

      <div className="app-shell glass-panel">
        <header className="chrome-row">
          <div className="title-block">
            <p className="eyebrow">Project Console</p>
            <h1>{title}</h1>
            <p className="subtitle">{subtitle}</p>
          </div>
        </header>

        <section className="content-wrap">{children}</section>
      </div>
    </div>
  );
}

/**
 * Reusable glass card wrapper used across pages for consistent
 * spacing, heading style, and panel treatment.
 *
 * @param {{
 *   title?: string,
 *   hint?: string,
 *   children: import("react").ReactNode,
 *   className?: string
 * }} props
 * @returns {JSX.Element}
 */
export function GlassCard({ title, hint, children, className = "" }) {
  return (
    <article className={`glass-card ${className}`.trim()}>
      {title ? <h2>{title}</h2> : null}
      {hint ? <p className="hint">{hint}</p> : null}
      {children}
    </article>
  );
}
