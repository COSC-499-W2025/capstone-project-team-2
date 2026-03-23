export const DEFAULT_A11Y = {
  textScale: 0,
  reduceMotion: false,
  dyslexiaFont: false,
  darkMode: false
};

export const A11Y_STORAGE_KEY = "a11yPrefs";
export const MIN_TEXT_SCALE = -2;
export const MAX_TEXT_SCALE = 4;

export const flowSteps = [
  { href: "/", label: "Start", cue: "Review workflow and key capabilities", requires: "none" },
  { href: "/config", label: "Settings", cue: "Set consent and profile preferences", requires: "none" },
  { href: "/upload", label: "Upload", cue: "Upload repositories and run analysis", requires: "consent" },
  { href: "/projects", label: "Projects", cue: "Review, update, and manage project records", requires: "consent" },
  { href: "/dashboard", label: "Dashboard", cue: "Inspect skill, activity, and trend insights", requires: "projects" },
  { href: "/workspace", label: "Builder", cue: "Create, edit, and export resume/portfolio drafts", requires: "consent" },
  { href: "/representation", label: "Project Settings", cue: "Finalize ordering, highlights, and chronology details", requires: "projects" }
];

export function clampTextScale(value) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(MIN_TEXT_SCALE, Math.min(MAX_TEXT_SCALE, value));
}

export function hydrateA11yPrefs(rawPrefs) {
  if (!rawPrefs) return DEFAULT_A11Y;

  try {
    const parsed = JSON.parse(rawPrefs);
    const parsedTextScale = typeof parsed?.textScale === "number" ? parsed.textScale : 0;
    return {
      textScale: clampTextScale(parsedTextScale),
      reduceMotion: Boolean(parsed?.reduceMotion),
      dyslexiaFont: Boolean(parsed?.dyslexiaFont),
      darkMode: Boolean(parsed?.darkMode)
    };
  } catch {
    return DEFAULT_A11Y;
  }
}

export function hasConfiguredConsent(config) {
  const external = config?.consented?.external;
  const dataConsent = config?.consented?.["Data consent"] ?? config?.consented?.data_consent;
  return (external === true || external === false) && dataConsent === true;
}

export function isRouteUnlocked(route, consentReady, projectsReady) {
  if (!route) return false;
  if (route.requires === "none" || !route.requires) return true;
  if (route.requires === "consent") return consentReady;
  if (route.requires === "projects") return consentReady && projectsReady;
  return true;
}

export function findNextUnlockedStep(currentStepIndex, consentReady, projectsReady, steps = flowSteps) {
  if (currentStepIndex < 0) return null;
  for (let index = currentStepIndex + 1; index < steps.length; index += 1) {
    if (isRouteUnlocked(steps[index], consentReady, projectsReady)) return steps[index];
  }
  return null;
}

export function findPreviousUnlockedStep(currentStepIndex, consentReady, projectsReady, steps = flowSteps) {
  if (currentStepIndex <= 0) return null;
  for (let index = currentStepIndex - 1; index >= 0; index -= 1) {
    if (isRouteUnlocked(steps[index], consentReady, projectsReady)) return steps[index];
  }
  return null;
}

export function getFlowSegmentState(index, currentStepIndex, unlocked, atLastStep) {
  const complete = currentStepIndex > index;
  const active = index === currentStepIndex;
  const locked = !complete && !active && !unlocked;

  if (atLastStep) return "complete";
  if (complete) return "complete";
  if (active) return "active";
  if (locked) return "locked";
  return "pending";
}
