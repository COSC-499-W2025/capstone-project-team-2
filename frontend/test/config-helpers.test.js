import test from "node:test";
import assert from "node:assert/strict";

import {
  applyNameToConfig,
  formatExternalConsentLabel,
  resolveExternalConsentState,
  validateExternalConsentSelection
} from "../app/config/helpers.js";

test("resolveExternalConsentState maps true, false, and missing values explicitly", () => {
  assert.equal(resolveExternalConsentState({ consented: { external: true } }), "allow");
  assert.equal(resolveExternalConsentState({ consented: { external: false } }), "deny");
  assert.equal(resolveExternalConsentState({ consented: {} }), "unset");
  assert.equal(resolveExternalConsentState({}), "unset");
});

test("formatExternalConsentLabel renders user-facing consent labels", () => {
  assert.equal(formatExternalConsentLabel("allow"), "Allow");
  assert.equal(formatExternalConsentLabel("deny"), "Do not allow");
  assert.equal(formatExternalConsentLabel("unset"), "Not set");
});

test("validateExternalConsentSelection requires an explicit consent choice", () => {
  assert.equal(
    validateExternalConsentSelection("unset"),
    "Select an external tools consent option before saving."
  );
  assert.equal(validateExternalConsentSelection("allow"), "");
  assert.equal(validateExternalConsentSelection("deny"), "");
});

test("applyNameToConfig splits a full name into first and last name fields", () => {
  const nextConfig = applyNameToConfig({}, "Jane Mary Doe");

  assert.equal(nextConfig["First Name"], "Jane");
  assert.equal(nextConfig["Last Name"], "Mary Doe");
});

test("applyNameToConfig clears persisted name fields when input is blank", () => {
  const nextConfig = applyNameToConfig({
    "First Name": "Jane",
    "Last Name": "Doe"
  }, "   ");

  assert.equal(nextConfig["First Name"], "");
  assert.equal(nextConfig["Last Name"], "");
});
