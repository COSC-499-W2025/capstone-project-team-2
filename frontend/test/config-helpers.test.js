import test from "node:test";
import assert from "node:assert/strict";

import {
  applyNameToConfig,
  formatExternalConsentLabel,
  formatLocalConsentLabel,
  resolveExternalConsentState,
  resolveLocalConsentState,
  validateExternalConsentSelection
} from "../app/config/helpers.js";

test("resolveExternalConsentState maps true to allow, anything else to deny", () => {
  assert.equal(resolveExternalConsentState({ consented: { external: true } }), "allow");
  assert.equal(resolveExternalConsentState({ consented: { external: false } }), "deny");
  assert.equal(resolveExternalConsentState({ consented: {} }), "deny");
  assert.equal(resolveExternalConsentState({}), "deny");
  assert.equal(resolveExternalConsentState(null), "deny");
});

test("formatExternalConsentLabel renders user-facing consent labels", () => {
  assert.equal(formatExternalConsentLabel("allow"), "Allow");
  assert.equal(formatExternalConsentLabel("deny"), "Do not allow");
});

test("validateExternalConsentSelection always returns no error", () => {
  assert.equal(validateExternalConsentSelection("allow"), "");
  assert.equal(validateExternalConsentSelection("deny"), "");
});

test("resolveLocalConsentState maps true to allow, anything else to deny", () => {
  assert.equal(resolveLocalConsentState({ consented: { "Data consent": true } }), "allow");
  assert.equal(resolveLocalConsentState({ consented: { "Data consent": false } }), "deny");
  assert.equal(resolveLocalConsentState({ consented: {} }), "deny");
  assert.equal(resolveLocalConsentState({}), "deny");
  assert.equal(resolveLocalConsentState(null), "deny");
});

test("formatLocalConsentLabel renders user-facing consent labels", () => {
  assert.equal(formatLocalConsentLabel("allow"), "Allow");
  assert.equal(formatLocalConsentLabel("deny"), "Do not allow");
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
