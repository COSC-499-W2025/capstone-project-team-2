import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_REPRESENTATION_PREFERENCES,
  buildChronologyPayload,
  formatChronologyInputs,
  mergeProjectOrder,
  normalizeRepresentationPreferences,
  parseListInput,
  toDateTimeLocalValue,
  toIsoDateTimeValue
} from "../app/representation/helpers.js";

test("normalizeRepresentationPreferences fills missing defaults", () => {
  const normalized = normalizeRepresentationPreferences({
    highlight_skills: ["React"],
    showcase_projects: ["Project A"]
  });

  assert.deepEqual(normalized, {
    ...DEFAULT_REPRESENTATION_PREFERENCES,
    highlight_skills: ["React"],
    showcase_projects: ["Project A"]
  });
});

test("mergeProjectOrder preserves preferred order and appends new projects once", () => {
  const merged = mergeProjectOrder(
    ["Project B", "Project A", "Project B"],
    [
      { project_name: "Project A" },
      { project_name: "Project C" },
      { project_name: "Project B" }
    ]
  );

  assert.deepEqual(merged, ["Project B", "Project A", "Project C"]);
});

test("parseListInput trims values and removes empty entries", () => {
  const parsed = parseListInput(" React,  Next.js ,, FastAPI ");

  assert.deepEqual(parsed, ["React", "Next.js", "FastAPI"]);
});

test("formatChronologyInputs flattens analyzed_at values for form state", () => {
  const formatted = formatChronologyInputs({
    "Project A": { analyzed_at: "2025-03-14T12:00:00Z" },
    "Project B": { other: "ignored" }
  });

  assert.equal(formatted["Project A"], toDateTimeLocalValue("2025-03-14T12:00:00Z"));
  assert.equal(formatted["Project B"], undefined);
});

test("buildChronologyPayload omits blank values and converts valid inputs to ISO", () => {
  const payload = buildChronologyPayload({
    "Project A": "2025-03-14T12:00:00",
    "Project B": "",
    "Project C": "   "
  });

  assert.deepEqual(payload, {
    "Project A": { analyzed_at: toIsoDateTimeValue("2025-03-14T12:00:00") }
  });
});

test("buildChronologyPayload rejects invalid date values", () => {
  assert.throws(
    () => buildChronologyPayload({ "Project A": "testing" }),
    /Enter a valid date and time for Project A\./
  );
});
