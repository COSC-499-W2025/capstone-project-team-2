"use client";

/**
 * Shared shell components used by all primary app routes.
 *
 * Exports:
 * - `LiquidShell`: floating nav + title chrome + content wrapper.
 * - `GlassCard`: reusable card container with consistent spacing/styling.
 */
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { LiquidPillNav, LiquidSegmentedControl } from "./LiquidPillControl";
import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { fetchConfig, fetchProjects } from "../lib/api";

/**
 * Route definitions for top-level navigation.
 * Visibility of routes is filtered by the selected audience mode.
 * @type {{href: string, label: string, modes: Array<"public" | "private">, requires?: "none" | "consent" | "projects"}[]}
 */
const links = [
  { href: "/", label: "Home", modes: ["public", "private"], requires: "none" },
  { href: "/config", label: "Settings", modes: ["public", "private"], requires: "none" },
  { href: "/upload", label: "Upload", modes: ["public", "private"], requires: "consent" },
  { href: "/projects", label: "Projects", modes: ["public", "private"], requires: "consent" },
  { href: "/dashboard", label: "Dashboard", modes: ["public", "private"], requires: "projects" },
  { href: "/workspace", label: "Builder", modes: ["public", "private"], requires: "consent" },
  { href: "/representation", label: "Project Settings", modes: ["public", "private"], requires: "projects" }
];

const DEFAULT_A11Y = {
  textScale: 0,
  reduceMotion: false,
  dyslexiaFont: false
};
const A11Y_STORAGE_KEY = "a11yPrefs";
const MIN_TEXT_SCALE = -2;
const MAX_TEXT_SCALE = 4;

const flowSteps = [
  { href: "/", label: "Start", requires: "none" },
  { href: "/config", label: "Settings", requires: "none" },
  { href: "/upload", label: "Upload", requires: "consent" },
  { href: "/projects", label: "Projects", requires: "consent" },
  { href: "/dashboard", label: "Dashboard", requires: "projects" },
  { href: "/workspace", label: "Builder", requires: "consent" },
  { href: "/representation", label: "Project Settings", requires: "projects" }
];

const flowPhases = [
  { label: "Setup", start: 0, end: 1 },
  { label: "Analyze", start: 2, end: 3 },
  { label: "Build", start: 4, end: 5 },
  { label: "Refine", start: 6, end: 6 }
];

function hasConfiguredConsent(config) {
  const external = config?.consented?.external;
  const dataConsent = config?.consented?.["Data consent"] ?? config?.consented?.data_consent;
  return (external === true || external === false) && dataConsent === true;
}

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
  const hasOpenedA11yRef = useRef(false);

  function clampTextScale(value) {
    if (!Number.isFinite(value)) return 0;
    return Math.max(MIN_TEXT_SCALE, Math.min(MAX_TEXT_SCALE, value));
  }
  const [flowLoading, setFlowLoading] = useState(true);
  const [flowError, setFlowError] = useState("");
  const [consentReady, setConsentReady] = useState(false);
  const [projectsReady, setProjectsReady] = useState(false);

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
      if (hasOpenedA11yRef.current && a11yTriggerRef.current) a11yTriggerRef.current.focus();
      return undefined;
    }
    hasOpenedA11yRef.current = true;
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

  useEffect(() => {
    let ignore = false;
    async function loadFlowReadiness() {
      setFlowLoading(true);
      setFlowError("");
      try {
        const [config, projects] = await Promise.allSettled([fetchConfig(), fetchProjects()]);
        if (ignore) return;

        const configValue = config.status === "fulfilled" ? config.value : {};
        const projectsValue = projects.status === "fulfilled" && Array.isArray(projects.value) ? projects.value : [];

        setConsentReady(hasConfiguredConsent(configValue));
        setProjectsReady(projectsValue.length > 0);

        if (config.status === "rejected" || projects.status === "rejected") {
          setFlowError("Some prerequisite checks could not be loaded. Backend may be offline.");
        }
      } finally {
        if (!ignore) setFlowLoading(false);
      }
    }

    loadFlowReadiness();
    return () => {
      ignore = true;
    };
  }, []);

  function isRouteUnlocked(route) {
    if (!route) return false;
    if (route.requires === "none" || !route.requires) return true;
    if (route.requires === "consent") return consentReady;
    if (route.requires === "projects") return consentReady && projectsReady;
    return true;
  }

  useEffect(() => {
    if (flowLoading || flowError) return;
    const currentRoute = [...links, ...flowSteps].find((route) => route.href === pathname);
    if (currentRoute && !isRouteUnlocked(currentRoute)) {
      if (!consentReady) {
        router.replace("/config");
        return;
      }
      if (!projectsReady) {
        router.replace("/upload");
      }
    }
  }, [pathname, flowLoading, flowError, consentReady, projectsReady, router]);

  const filteredLinks = useMemo(
    () => links
      .filter((link) => link.modes.includes(viewMode))
      .map((link) => ({ ...link, disabled: flowLoading ? false : !isRouteUnlocked(link) })),
    [viewMode, flowLoading, consentReady, projectsReady]
  );

  const currentStepIndex = flowSteps.findIndex((step) => step.href === pathname);
  const currentStep = currentStepIndex >= 0 ? flowSteps[currentStepIndex] : null;
  const nextStep = useMemo(() => {
    if (currentStepIndex < 0) return null;
    for (let index = currentStepIndex + 1; index < flowSteps.length; index += 1) {
      if (isRouteUnlocked(flowSteps[index])) return flowSteps[index];
    }
    return null;
  }, [currentStepIndex, consentReady, projectsReady]);
  const progressPercent = currentStepIndex >= 0
    ? ((currentStepIndex + 1) / flowSteps.length) * 100
    : 0;
  const flowBlocked = currentStepIndex >= 0 && currentStepIndex < flowSteps.length - 1 && !nextStep;
  const blockedReason = !consentReady
    ? "Complete Settings first."
    : "Upload and analyze at least one project first.";
  const activePhaseIndex = flowPhases.findIndex((phase) => currentStepIndex >= phase.start && currentStepIndex <= phase.end);

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
              <div className="nav-mode-toggle" role="group" aria-label="View mode">
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

          <aside className="header-side-panel" aria-label="Workflow summary">
            {currentStep ? (
              <div className="flow-banner">
                <span className="mode-pill flow-step-pill">
                  Step {currentStepIndex + 1} of {flowSteps.length}
                </span>
                {nextStep ? (
                  <Link href={nextStep.href} className="liquid-btn solid flow-next-btn">
                    Continue to {nextStep.label}
                  </Link>
                ) : flowBlocked ? (
                  <span className="liquid-btn flow-next-btn flow-next-blocked" aria-disabled="true">
                    Continue unavailable
                  </span>
                ) : (
                  <span className="mode-pill">Workflow complete</span>
                )}
              </div>
            ) : null}
            {flowBlocked ? <p className="flow-next-hint">{blockedReason}</p> : null}
            {flowError ? <p className="muted">{flowError}</p> : null}
          </aside>
        </header>

        <section className="content-wrap">
          <div className="flow-phase-strip" role="presentation">
            {flowPhases.map((phase, index) => {
              const complete = currentStepIndex > phase.end;
              const active = index === activePhaseIndex;
              const phaseStartUnlocked = isRouteUnlocked(flowSteps[phase.start]);
              const locked = !complete && !active && !phaseStartUnlocked;
              const marker = complete ? "✓" : (active ? "●" : String(index + 1));

              return (
                <span
                  key={phase.label}
                  className={`flow-phase-chip ${active ? "active" : ""} ${complete ? "complete" : ""} ${locked ? "locked" : ""}`.trim()}
                >
                  <span className="flow-phase-marker">{marker}</span>
                  <span>{phase.label}</span>
                </span>
              );
            })}
          </div>
          <div className="flow-progress-rail" aria-hidden="true">
            <span className="flow-progress-fill" style={{ width: `${progressPercent}%` }} />
          </div>
          {children}
        </section>
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
