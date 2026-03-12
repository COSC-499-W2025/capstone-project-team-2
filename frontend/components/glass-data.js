/**
 * Static legacy data module.
 *
 * These exports are intentionally static and are used by legacy shell
 * examples/components that remain in the repository for compatibility.
 */

/**
 * Legacy navigation items consumed by GlassShell dock navigation.
 * @type {{ href: string, label: string }[]}
 */
export const navItems = [
  { href: "/", label: "Home" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
  { href: "/resume", label: "Resume" },
  { href: "/portfolio", label: "Portfolio" }
];

/**
 * Static dashboard metric placeholders used by legacy UI examples.
 * @type {{ label: string, value: string }[]}
 */
export const dashboardStats = [
  { label: "Projects Tracked", value: "14" },
  { label: "Languages Detected", value: "9" },
  { label: "Resume Variants", value: "6" },
  { label: "Portfolio Themes", value: "4" }
];

/**
 * Sample activity feed entries used by legacy showcase cards.
 * @type {string[]}
 */
export const activity = [
  "Analyzed monorepo structure and inferred stack ownership.",
  "Generated role-focused bullet points for backend services.",
  "Refreshed portfolio cards with measured impact metrics."
];
