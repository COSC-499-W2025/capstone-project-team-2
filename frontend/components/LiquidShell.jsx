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
import { useEffect, useMemo, useRef, useState } from "react";

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
  { href: "/projects", label: "Project Management", modes: ["private"] },
  { href: "/config", label: "User Config", modes: ["private"] },
  { href: "/representation", label: "Representation", modes: ["private"] }
];

const DEFAULT_A11Y = {
  textScale: 0,
  reduceMotion: false,
  dyslexiaFont: false
};
const A11Y_STORAGE_KEY = "a11yPrefs";
const MIN_TEXT_SCALE = -2;
const MAX_TEXT_SCALE = 4;

/**
 * Shared page shell with floating navigation and
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
  const [isA11yMenuOpen, setIsA11yMenuOpen] = useState(false);
  const [a11yPrefs, setA11yPrefs] = useState(DEFAULT_A11Y);
  const [hasHydratedA11y, setHasHydratedA11y] = useState(false);
  const a11yMenuRef = useRef(null);
  const a11yTriggerRef = useRef(null);

  function clampTextScale(value) {
    if (!Number.isFinite(value)) return 0;
    return Math.max(MIN_TEXT_SCALE, Math.min(MAX_TEXT_SCALE, value));
  }

  useEffect(() => {
    /**
     * One-time hydration of persisted navigation mode preference.
     */
    const storedViewMode = window.localStorage.getItem("viewMode");
    if (storedViewMode === "public" || storedViewMode === "private") {
      setViewMode(storedViewMode);
    }
  }, []);

  useEffect(() => {
    const rawPrefs = window.localStorage.getItem(A11Y_STORAGE_KEY);
    if (!rawPrefs) {
      setHasHydratedA11y(true);
      return;
    }

    try {
      const parsed = JSON.parse(rawPrefs);
      const parsedTextScale = typeof parsed?.textScale === "number" ? parsed.textScale : 0;
      setA11yPrefs({
        textScale: clampTextScale(parsedTextScale),
        reduceMotion: Boolean(parsed?.reduceMotion),
        dyslexiaFont: Boolean(parsed?.dyslexiaFont)
      });
    } catch {
      setA11yPrefs(DEFAULT_A11Y);
    } finally {
      setHasHydratedA11y(true);
    }
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
    if (!hasHydratedA11y) return;
    const root = document.documentElement;
    root.classList.toggle("a11y-text-scaling", a11yPrefs.textScale !== 0);
    root.classList.toggle("a11y-reduced-motion", a11yPrefs.reduceMotion);
    root.classList.toggle("a11y-dyslexia-font", a11yPrefs.dyslexiaFont);
    root.style.setProperty("--a11y-text-scale", String(a11yPrefs.textScale));
    window.localStorage.setItem(A11Y_STORAGE_KEY, JSON.stringify(a11yPrefs));
  }, [a11yPrefs, hasHydratedA11y]);

  useEffect(() => {
    if (!isA11yMenuOpen) return undefined;

    function onPointerDown(event) {
      if (!a11yMenuRef.current) return;
      if (!a11yMenuRef.current.contains(event.target)) {
        setIsA11yMenuOpen(false);
      }
    }
    function onKeyDown(event) {
      if (event.key === "Escape") {
        setIsA11yMenuOpen(false);
      }
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [isA11yMenuOpen]);

  useEffect(() => {
    if (!isA11yMenuOpen) {
      if (a11yTriggerRef.current) a11yTriggerRef.current.focus();
      return undefined;
    }

    const panelEl = document.getElementById("a11y-panel");
    if (!panelEl) return undefined;

    const firstFocusable = panelEl.querySelector(
      "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
    );
    if (firstFocusable && typeof firstFocusable.focus === "function") {
      firstFocusable.focus();
    }

    function onTrapTab(event) {
      if (event.key !== "Tab") return;
      const focusables = panelEl.querySelectorAll(
        "button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])"
      );
      if (!focusables.length) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onTrapTab);
    return () => document.removeEventListener("keydown", onTrapTab);
  }, [isA11yMenuOpen]);

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

  useEffect(() => {
    setIsA11yMenuOpen(false);
  }, [pathname]);

  const textScaleSummary = a11yPrefs.textScale === 0
    ? "Current: Default"
    : `Current: ${a11yPrefs.textScale > 0 ? "+" : ""}${a11yPrefs.textScale * 5}%`;

  const binaryRows = [
    { key: "reduceMotion", label: "Reduced motion", hint: "Limit movement and transitions" },
    { key: "dyslexiaFont", label: "Readable font", hint: "Use dyslexia-friendly typeface" }
  ];

  return (
    <div className="liquid-scene">
      <div className="floating-nav-layer">
        <LiquidPillNav
          items={filteredLinks}
          activeHref={pathname}
          reducedMotion={a11yPrefs.reduceMotion}
          className="top-chrome"
          trailingContent={
            <div className="top-right-slot top-actions">
              <div className="nav-mode-toggle" role="group" aria-label="Navigation visibility mode">
                <LiquidSegmentedControl
                  reducedMotion={a11yPrefs.reduceMotion}
                  options={[
                    { value: "private", label: "Private" },
                    { value: "public", label: "Public" }
                  ]}
                  value={viewMode}
                  onChange={setViewMode}
                />
              </div>
              {rightSlot ? <div>{rightSlot}</div> : null}
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

      <div className="a11y-control floating-a11y-control" ref={a11yMenuRef}>
        <button
          type="button"
          className={`liquid-glass-toggle a11y-trigger ${isA11yMenuOpen ? "open" : ""}`.trim()}
          ref={a11yTriggerRef}
          aria-haspopup="dialog"
          aria-expanded={isA11yMenuOpen}
          aria-controls="a11y-panel"
          aria-label={isA11yMenuOpen ? "Close accessibility menu" : "Open accessibility menu"}
          onClick={() => setIsA11yMenuOpen((open) => !open)}
        >
          <span>{isA11yMenuOpen ? "Close Accessibility" : "Accessibility"}</span>
        </button>
        {isA11yMenuOpen ? (
          <div id="a11y-panel" className="a11y-panel glass-panel" role="dialog" aria-label="Accessibility settings" aria-modal="true">
            <div className="a11y-panel-header">
              <p className="a11y-panel-kicker">Display Preferences</p>
              <p className="a11y-panel-title">Accessibility</p>
            </div>
            <div className="a11y-options-list">
              <div className="a11y-option">
                <div className="a11y-option-meta">
                  <span className="a11y-option-label">Text size</span>
                  <span className="a11y-option-hint">{textScaleSummary}</span>
                </div>
                <LiquidSegmentedControl
                  className="a11y-option-toggle"
                  reducedMotion={a11yPrefs.reduceMotion}
                  ariaLabel="Text size control"
                  options={[
                    { value: "minus", label: "A-" },
                    { value: "default", label: "A" },
                    { value: "plus", label: "A+" }
                  ]}
                  value={a11yPrefs.textScale === 0 ? "default" : a11yPrefs.textScale > 0 ? "plus" : "minus"}
                  onChange={(value) => {
                    setA11yPrefs((current) => ({
                      ...current,
                      textScale: value === "default"
                        ? 0
                        : clampTextScale(current.textScale + (value === "plus" ? 1 : -1))
                    }));
                  }}
                />
              </div>
              {binaryRows.map((row) => (
                <div key={row.key} className="a11y-option">
                  <div className="a11y-option-meta">
                    <span className="a11y-option-label">{row.label}</span>
                    <span className="a11y-option-hint">{row.hint}</span>
                  </div>
                  <LiquidSegmentedControl
                    className="a11y-option-toggle"
                    reducedMotion={a11yPrefs.reduceMotion}
                    ariaLabel={`${row.label} toggle`}
                    options={[
                      { value: "off", label: "Off" },
                      { value: "on", label: "On" }
                    ]}
                    value={a11yPrefs[row.key] ? "on" : "off"}
                    onChange={(value) => {
                      setA11yPrefs((current) => ({ ...current, [row.key]: value === "on" }));
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        ) : null}
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
