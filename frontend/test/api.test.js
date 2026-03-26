import test from "node:test";
import assert from "node:assert/strict";

import {
  analyzeUploadedProject,
  fetchRepresentationPreferences,
  fetchRepresentationProjects,
  fetchProjects,
  fetchProjectByName,
  fetchProjectInsights,
  fetchTopProjectHistories,
  getPortfolioShowcaseRole,
  getApiBase,
  saveConsent,
  setPortfolioShowcaseRole,
  updateConfig,
  updateRepresentationPreferences,
  fetchConfig,
  uploadProjectZip
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

// ---------------------------------------------------------------------------
// Core / misc
// ---------------------------------------------------------------------------

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

test("fetchProjectByName calls /projects/:name with encoding", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { name: "My Project" } });
  };

  await fetchProjectByName("My Project");

  assert.equal(calls[0], "http://localhost:8000/projects/My%20Project");
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

test("fetchTopProjectHistories encodes top_n and contributor query params", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: [] });
  };

  await fetchTopProjectHistories({ topN: 3, contributor: "Jane Doe" });

  assert.equal(
    calls[0],
    "http://localhost:8000/insights/top-projects?top_n=3&contributor=Jane+Doe"
  );
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

test("analyzeUploadedProject with no name omits query string", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { ok: true } });
  };

  await analyzeUploadedProject();

  assert.equal(calls[0], "http://localhost:8000/analyze");
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

test("fetchRepresentationPreferences calls /representation/preferences", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { project_order: ["Project A"] } });
  };

  const payload = await fetchRepresentationPreferences();

  assert.deepEqual(payload, { project_order: ["Project A"] });
  assert.equal(calls[0], "http://localhost:8000/representation/preferences");
});

test("updateRepresentationPreferences sends payload to /representation/preferences", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { saved: true } });
  };

  const payload = {
    project_order: ["Project A"],
    chronology_corrections: { "Project A": { analyzed_at: "2025-03-14T12:00:00Z" } },
    highlight_skills: ["React"],
    showcase_projects: ["Project A"]
  };

  await updateRepresentationPreferences(payload);

  assert.equal(calls[0].url, "http://localhost:8000/representation/preferences");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body ?? "{}"), payload);
});

test("fetchRepresentationProjects encodes only_showcase and snapshot_label query params", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { projects: [] } });
  };

  await fetchRepresentationProjects({ onlyShowcase: true, snapshotLabel: "milestone 3" });

  assert.equal(
    calls[0],
    "http://localhost:8000/representation/projects?only_showcase=true&snapshot_label=milestone+3"
  );
});
test("fetchConfig calls /config/get", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { name: "Jane" } });
  };

  await fetchConfig();

  assert.equal(calls[0], "http://localhost:8000/config/get");
});

test("uploadProjectZip POSTs a multipart form to /projects/upload", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { uploaded: true } });
  };

  const fakeFile = new File(["data"], "project.zip", { type: "application/zip" });
  await uploadProjectZip(fakeFile);

  assert.equal(calls[0].url, "http://localhost:8000/projects/upload");
  assert.equal(calls[0].init?.method, "POST");
  assert.ok(calls[0].init?.body instanceof FormData);
});

// ---------------------------------------------------------------------------
// Error path tests
// ---------------------------------------------------------------------------

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

test("getPortfolioShowcaseRole calls encoded showcase role endpoint", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { project_name: "My Project", role: "Backend Developer" } });
  };

  const payload = await getPortfolioShowcaseRole("My Project");

  assert.deepEqual(payload, { project_name: "My Project", role: "Backend Developer" });
  assert.equal(calls[0], "http://localhost:8000/portfolio-showcase/My%20Project/role");
});

test("setPortfolioShowcaseRole posts expected JSON body", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({
      json: {
        project_name: "My Project",
        role: "Technical Lead",
        status: "Role override saved successfully"
      }
    });
  };

  const payload = await setPortfolioShowcaseRole("My Project", "Technical Lead");

  assert.deepEqual(payload, {
    project_name: "My Project",
    role: "Technical Lead",
    status: "Role override saved successfully"
  });
  assert.equal(calls[0].url, "http://localhost:8000/portfolio-showcase/My%20Project/role");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body ?? "{}"), { role: "Technical Lead" });
});

test("getPortfolioShowcaseRole surfaces backend 404 detail", async () => {
  global.fetch = async () => makeResponse({
    ok: false,
    status: 404,
    json: { detail: "No saved role for project 'UnknownProject'." }
  });

  await assert.rejects(
    () => getPortfolioShowcaseRole("UnknownProject"),
    /No saved role for project 'UnknownProject'\./
  );
});

test("backend non-2xx attaches response.status to thrown error", async () => {
  global.fetch = async () => makeResponse({
    ok: false,
    status: 404,
    json: { detail: "Resume 'abc' not found" }
  });

  const err = await fetchProjects().catch((e) => e);
  assert.equal(err.status, 404);
});
