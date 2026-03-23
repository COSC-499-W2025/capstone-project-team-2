import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_A11Y,
  clampTextScale,
  findNextUnlockedStep,
  findPreviousUnlockedStep,
  flowSteps,
  getFlowSegmentState,
  hasConfiguredConsent,
  hydrateA11yPrefs,
  isRouteUnlocked
} from "../components/liquid-shell-helpers.js";

test("hydrateA11yPrefs parses persisted darkMode and clamps textScale", () => {
  const prefs = hydrateA11yPrefs(JSON.stringify({
    textScale: 99,
    reduceMotion: 1,
    dyslexiaFont: "yes",
    darkMode: true
  }));

  assert.deepEqual(prefs, {
    textScale: 4,
    reduceMotion: true,
    dyslexiaFont: true,
    darkMode: true
  });
});

test("hydrateA11yPrefs falls back to defaults on invalid JSON", () => {
  assert.deepEqual(hydrateA11yPrefs("{invalid"), DEFAULT_A11Y);
});

test("clampTextScale enforces min/max and non-number fallback", () => {
  assert.equal(clampTextScale(-999), -2);
  assert.equal(clampTextScale(999), 4);
  assert.equal(clampTextScale(Number.NaN), 0);
});

test("hasConfiguredConsent accepts explicit external consent + data consent", () => {
  assert.equal(hasConfiguredConsent({ consented: { external: true, "Data consent": true } }), true);
  assert.equal(hasConfiguredConsent({ consented: { external: false, data_consent: true } }), true);
  assert.equal(hasConfiguredConsent({ consented: { external: true, "Data consent": false } }), false);
});

test("isRouteUnlocked respects none, consent, and projects requirements", () => {
  assert.equal(isRouteUnlocked({ requires: "none" }, false, false), true);
  assert.equal(isRouteUnlocked({ requires: "consent" }, false, true), false);
  assert.equal(isRouteUnlocked({ requires: "consent" }, true, false), true);
  assert.equal(isRouteUnlocked({ requires: "projects" }, true, false), false);
  assert.equal(isRouteUnlocked({ requires: "projects" }, true, true), true);
});

test("findNextUnlockedStep skips locked routes and returns nearest unlocked step", () => {
  const fromSettingsIndex = flowSteps.findIndex((step) => step.href === "/config");
  const nextWithoutConsent = findNextUnlockedStep(fromSettingsIndex, false, false, flowSteps);
  const nextWithConsent = findNextUnlockedStep(fromSettingsIndex, true, false, flowSteps);

  assert.equal(nextWithoutConsent, null);
  assert.equal(nextWithConsent?.href, "/upload");
});

test("findPreviousUnlockedStep returns nearest previous unlocked step", () => {
  const fromDashboardIndex = flowSteps.findIndex((step) => step.href === "/dashboard");
  const previousWithoutConsent = findPreviousUnlockedStep(fromDashboardIndex, false, false, flowSteps);
  const previousWithConsent = findPreviousUnlockedStep(fromDashboardIndex, true, false, flowSteps);

  assert.equal(previousWithoutConsent?.href, "/config");
  assert.equal(previousWithConsent?.href, "/projects");
});

test("getFlowSegmentState maps active/pending/locked and marks all complete on last step", () => {
  assert.equal(getFlowSegmentState(2, 2, true, false), "active");
  assert.equal(getFlowSegmentState(4, 2, false, false), "locked");
  assert.equal(getFlowSegmentState(3, 2, true, false), "pending");
  assert.equal(getFlowSegmentState(0, 6, true, true), "complete");
  assert.equal(getFlowSegmentState(6, 6, true, true), "complete");
});
