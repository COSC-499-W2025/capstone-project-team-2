/**
 * Canonical filename guard script.
 *
 * Some editor workflows can accidentally create numbered duplicates like:
 * - `page 2.js`
 * - `globals 8.css`
 * - `LiquidShell 3.jsx`
 *
 * This script runs in npm pre-hooks and restores expected canonical names
 * before dev/build/start to keep routing and imports stable.
 */
import { readdirSync, renameSync, existsSync, rmSync } from "node:fs";
import { join } from "node:path";

/**
 * Finds the first filename in a directory that matches a regex.
 *
 * @param {string} dirPath
 * @param {RegExp} pattern
 * @returns {string | null}
 */
function firstMatchingFile(dirPath, pattern) {
  const files = readdirSync(dirPath);
  return files.find((name) => pattern.test(name)) ?? null;
}

/**
 * Restores a canonical filename when editor-generated numbered
 * duplicates are present (for example, "page 2.js").
 *
 * @param {{
 *   dirPath: string,
 *   canonicalName: string,
 *   fallbackPattern: RegExp
 * }} params
 * @returns {void}
 */
function restoreCanonical({ dirPath, canonicalName, fallbackPattern }) {
  const canonicalPath = join(dirPath, canonicalName);
  if (existsSync(canonicalPath)) {
    return;
  }

  const fallback = firstMatchingFile(dirPath, fallbackPattern);
  if (!fallback) {
    return;
  }

  const fallbackPath = join(dirPath, fallback);
  renameSync(fallbackPath, canonicalPath);
  console.log(`[fix] restored ${canonicalName} from ${fallback}`);
}

/**
 * Canonical file repair entrypoint executed by npm pre-scripts.
 * Keeps critical route/component/style filenames stable.
 */
const appDir = join(process.cwd(), "app");
const componentsDir = join(process.cwd(), "components");
const nextBuildDir = join(process.cwd(), ".next");

restoreCanonical({
  dirPath: join(appDir, "upload"),
  canonicalName: "page.js",
  fallbackPattern: /^page \d+\.js$/
});

restoreCanonical({
  dirPath: appDir,
  canonicalName: "globals.css",
  fallbackPattern: /^globals \d+\.css$/
});

restoreCanonical({
  dirPath: componentsDir,
  canonicalName: "LiquidShell.jsx",
  fallbackPattern: /^LiquidShell \d+\.jsx$/
});

// Clear stale build artifacts before dev/build/start to avoid intermittent
// route-file ENOENT issues in .next/server/app/* during hot reload.
if (existsSync(nextBuildDir)) {
  rmSync(nextBuildDir, { recursive: true, force: true });
  console.log("[fix] cleared stale .next build cache");
}
