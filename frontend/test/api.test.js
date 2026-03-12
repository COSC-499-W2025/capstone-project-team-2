import test from "node:test";
import assert from "node:assert/strict";

import {
  analyzeUploadedProject,
  fetchProjects,
  fetchProjectInsights,
  getApiBase,
  saveConsent,
  updateConfig
} from "../lib/api.js";

/**
 * Creates a minimal fetch Response-like object for API client tests.
 *
 * @param {{ ok?: boolean, status?: number, json?: any, text?: string }} options
 * @returns {{ ok: boolean, status: number, json: () => Promise<any>, text: () => Promise<string>, blob: () => Promise<Blob> }}
 */
function makeResponse(options = {}) {
  const {
    ok = true,
    status = 200,
    json = {},
    text = ""
  } = options;

  return {
    ok,
    status,
    async json() {
      return json;
    },
    async text() {
      return text;
    },
    async blob() {
      return new Blob([text]);
    }
  };
}

test("getApiBase defaults to localhost:8000", () => {
  assert.equal(getApiBase(), "http://localhost:8000");
});

test("fetchProjects calls /projects/", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: ["project-a", "project-b"] });
  };

  const payload = await fetchProjects();

  assert.deepEqual(payload, ["project-a", "project-b"]);
  assert.equal(calls.length, 1);
  assert.equal(calls[0], "http://localhost:8000/projects/");
});

test("fetchProjectInsights calls /insights/projects", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: [] });
  };

  await fetchProjectInsights();

  assert.equal(calls[0], "http://localhost:8000/insights/projects");
});

test("analyzeUploadedProject appends encoded project_name query", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { ok: true } });
  };

  await analyzeUploadedProject("My Project 1");

  assert.equal(calls[0], "http://localhost:8000/analyze?project_name=My%20Project%201");
});

test("saveConsent sends expected JSON body", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { success: true } });
  };

  await saveConsent(false);

  assert.equal(calls[0].url, "http://localhost:8000/privacy-consent");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body ?? "{}"), {
    data_consent: true,
    external_consent: false
  });
});

test("updateConfig sends payload to /config/update", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { saved: true } });
  };

  const configPayload = { name: "Jane Doe", theme: "dark" };
  await updateConfig(configPayload);

  assert.equal(calls[0].url, "http://localhost:8000/config/update");
  assert.deepEqual(JSON.parse(calls[0].init?.body ?? "{}"), configPayload);
});

test("network failure surfaces friendly API offline message", async () => {
  global.fetch = async () => {
    throw new Error("socket closed");
  };

  await assert.rejects(
    () => fetchProjects(),
    /Cannot reach API server\. Is FastAPI running on port 8000\?/
  );
});

test("backend non-2xx with detail string becomes thrown message", async () => {
  global.fetch = async () => makeResponse({
    ok: false,
    status: 400,
    json: { detail: "Invalid payload" }
  });

  await assert.rejects(() => fetchProjects(), /Invalid payload/);
});
