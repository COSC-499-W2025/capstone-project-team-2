import test from "node:test";
import assert from "node:assert/strict";

import {
  fetchResumes,
  generateResume,
  fetchResume,
  deleteResume,
  editResume,
  addResumeProject,
  addResumeProjectAI,
  addResumeEducation,
  removeResumeEducation,
  addResumeExperience,
  removeResumeExperience,
  renderResume,
  exportResume,
  exportResumeCustom,
  addResumeProjectManual,
  addResumeSkill,
  appendResumeSkill,
  removeResumeSkill,
  removeResumeProject,
  addResumeAward,
  removeResumeAward,
  updateResumeSkillLevel,
  updatePortfolioSkillLevel,
  fetchPortfolios,
  generatePortfolio,
  fetchPortfolio,
  deletePortfolio,
  editPortfolio,
  addPortfolioProject,
  addPortfolioProjectAI,
  renderPortfolio,
  exportPortfolio,
  exportPortfolioCustom,
  addPortfolioProjectManual,
  addPortfolioSkill,
  appendPortfolioSkill,
  removePortfolioSkill,
  removePortfolioProject,
  setPortfolioShowcaseRole,
  getPortfolioShowcaseRole
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
// Resume endpoints
// ---------------------------------------------------------------------------

/**
 * Verifies that fetchResumes issues a GET request to /resumes
 * and returns the parsed JSON array.
 */
test("fetchResumes calls GET /resumes", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: [{ id: "r1", name: "Resume 1" }] });
  };

  const result = await fetchResumes();

  assert.equal(calls[0], "http://localhost:8000/resumes");
  assert.deepEqual(result, [{ id: "r1", name: "Resume 1" }]);
});

/**
 * Verifies that generateResume sends a POST to /resume/generate
 * with the name and theme in the request body.
 */
test("generateResume POSTs name and theme to /resume/generate", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { id: "r1" } });
  };

  await generateResume("Alice", "classic");

  assert.equal(calls[0].url, "http://localhost:8000/resume/generate");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { name: "Alice", theme: "classic" });
});

/**
 * Verifies that fetchResume issues a GET to /resume/:id
 * and percent-encodes spaces in the id.
 */
test("fetchResume calls GET /resume/:id with encoding", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { id: "r 1" } });
  };

  await fetchResume("r 1");

  assert.equal(calls[0], "http://localhost:8000/resume/r%201");
});

/**
 * Verifies that deleteResume sends a DELETE request to /resume/:id.
 */
test("deleteResume sends DELETE /resume/:id", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { deleted: true } });
  };

  await deleteResume("r1");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that editResume sends a POST to /resume/:id/edit
 * with the edits array serialised in the request body.
 */
test("editResume POSTs edits array to /resume/:id/edit", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const edits = [{ op: "replace", path: "/name", value: "Bob" }];
  await editResume("r1", edits);

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/edit");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { edits });
});

/**
 * Verifies that addResumeProject sends a POST to /resume/:id/add/project/:name
 * with the project name percent-encoded and the options payload in the body.
 */
test("addResumeProject POSTs to /resume/:id/add/project/:name", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await addResumeProject("r1", "My Project", { highlight: true });

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/add/project/My%20Project");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { highlight: true });
});

/**
 * Verifies that addResumeProjectAI sends a POST to /resume/:id/add/project/:name/ai
 * to trigger AI-assisted project content generation.
 */
test("addResumeProjectAI POSTs to /resume/:id/add/project/:name/ai", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await addResumeProjectAI("r1", "My Project");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/add/project/My%20Project/ai");
  assert.equal(calls[0].init?.method, "POST");
});

/**
 * Verifies that addResumeEducation sends a POST to /resume/:id/add/education
 * with the education object in the request body.
 */
test("addResumeEducation POSTs payload to /resume/:id/add/education", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const edu = { institution: "UBC", degree: "BSc" };
  await addResumeEducation("r1", edu);

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/add/education");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), edu);
});

/**
 * Verifies that removeResumeEducation sends a DELETE to
 * /resume/:id/education/:institution with the institution name percent-encoded.
 */
test("removeResumeEducation sends DELETE /resume/:id/education/:institution", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await removeResumeEducation("r1", "UBC Okanagan");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/education/UBC%20Okanagan");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that addResumeExperience sends a POST to /resume/:id/add/experience
 * with the experience object in the request body.
 */
test("addResumeExperience POSTs payload to /resume/:id/add/experience", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const exp = { company: "Acme", role: "Engineer" };
  await addResumeExperience("r1", exp);

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/add/experience");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), exp);
});

/**
 * Verifies that removeResumeExperience sends a DELETE to
 * /resume/:id/experience/:company with the company name percent-encoded.
 */
test("removeResumeExperience sends DELETE /resume/:id/experience/:company", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await removeResumeExperience("r1", "Acme Corp");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/experience/Acme%20Corp");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that renderResume sends a POST to /resume/:id/render/:format
 * and returns the response as a Blob.
 */
test("renderResume POSTs to /resume/:id/render/:format and returns blob", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ text: "%PDF-content" });
  };

  const blob = await renderResume("r1", "pdf");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/render/pdf");
  assert.equal(calls[0].init?.method, "POST");
  assert.ok(blob instanceof Blob);
});

/**
 * Verifies that exportResume sends a POST to /resume/:id/export/:format
 * to trigger a server-side export to the default output path.
 */
test("exportResume POSTs to /resume/:id/export/:format", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { path: "/out/resume.pdf" } });
  };

  await exportResume("r1", "pdf");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/export/pdf");
  assert.equal(calls[0].init?.method, "POST");
});

/**
 * Verifies that exportResumeCustom sends a POST to /resume/:id/export/:format/custom
 * with the custom output path in the request body.
 */
test("exportResumeCustom POSTs path to /resume/:id/export/:format/custom", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await exportResumeCustom("r1", "pdf", "/home/user/docs");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/export/pdf/custom");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { path: "/home/user/docs" });
});

/**
 * Verifies that addResumeProjectManual sends a POST to /resume/:id/add/project/manual
 * with a manually supplied project payload in the request body.
 */
test("addResumeProjectManual POSTs manual payload to /resume/:id/add/project/manual", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const proj = { title: "Side Project", description: "Cool app" };
  await addResumeProjectManual("r1", proj);

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/add/project/manual");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), proj);
});

/**
 * Verifies that addResumeSkill sends a POST to /resume/:id/add/skill
 * with the skill category object in the request body.
 */
test("addResumeSkill POSTs skill payload to /resume/:id/add/skill", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const skill = { label: "Languages", details: "Python, JS" };
  await addResumeSkill("r1", skill);

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/add/skill");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), skill);
});

/**
 * Verifies that appendResumeSkill sends a POST to /resume/:id/skill/:label/append
 * with the additional skill details in the request body.
 */
test("appendResumeSkill POSTs details to /resume/:id/skill/:label/append", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await appendResumeSkill("r1", "Languages", "Go, Rust");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/skill/Languages/append");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { details: "Go, Rust" });
});

/**
 * Verifies that removeResumeSkill sends a DELETE to /resume/:id/skill/:label.
 */
test("removeResumeSkill sends DELETE /resume/:id/skill/:label", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await removeResumeSkill("r1", "Languages");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/skill/Languages");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that removeResumeProject sends a DELETE to /resume/:id/project/:name
 * with the project name percent-encoded.
 */
test("removeResumeProject sends DELETE /resume/:id/project/:name", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await removeResumeProject("r1", "My Project");

  assert.equal(calls[0].url, "http://localhost:8000/resume/r1/project/My%20Project");
  assert.equal(calls[0].init?.method, "DELETE");
});

// ---------------------------------------------------------------------------
// Portfolio endpoints
// ---------------------------------------------------------------------------

/**
 * Verifies that fetchPortfolios issues a GET request to /portfolios
 * and returns the parsed JSON array.
 */
test("fetchPortfolios calls GET /portfolios", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: [{ id: "p1", name: "Portfolio 1" }] });
  };

  const result = await fetchPortfolios();

  assert.equal(calls[0], "http://localhost:8000/portfolios");
  assert.deepEqual(result, [{ id: "p1", name: "Portfolio 1" }]);
});

/**
 * Verifies that generatePortfolio sends a POST to /portfolio/generate
 * with the name and theme in the request body.
 */
test("generatePortfolio POSTs name and theme to /portfolio/generate", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { id: "p1" } });
  };

  await generatePortfolio("Alice", "modern");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/generate");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { name: "Alice", theme: "modern" });
});

/**
 * Verifies that fetchPortfolio issues a GET to /portfolio/:id
 * and percent-encodes spaces in the id.
 */
test("fetchPortfolio calls GET /portfolio/:id with encoding", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { id: "p 1" } });
  };

  await fetchPortfolio("p 1");

  assert.equal(calls[0], "http://localhost:8000/portfolio/p%201");
});

/**
 * Verifies that deletePortfolio sends a DELETE request to /portfolio/:id.
 */
test("deletePortfolio sends DELETE /portfolio/:id", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { deleted: true } });
  };

  await deletePortfolio("p1");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that editPortfolio sends a POST to /portfolio/:id/edit
 * with the edits array serialised in the request body.
 */
test("editPortfolio POSTs edits array to /portfolio/:id/edit", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const edits = [{ op: "replace", path: "/name", value: "New Name" }];
  await editPortfolio("p1", edits);

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/edit");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { edits });
});

/**
 * Verifies that addPortfolioProject sends a POST to /portfolio/:id/add/project/:name
 * with the project name percent-encoded and the options payload in the body.
 */
test("addPortfolioProject POSTs to /portfolio/:id/add/project/:name", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await addPortfolioProject("p1", "My Project", { featured: true });

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/add/project/My%20Project");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { featured: true });
});

/**
 * Verifies that addPortfolioProjectAI sends a POST to /portfolio/:id/add/project/:name/ai
 * to trigger AI-assisted project content generation.
 */
test("addPortfolioProjectAI POSTs to /portfolio/:id/add/project/:name/ai", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await addPortfolioProjectAI("p1", "My Project");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/add/project/My%20Project/ai");
  assert.equal(calls[0].init?.method, "POST");
});

/**
 * Verifies that renderPortfolio sends a POST to /portfolio/:id/render/:format
 * and returns the response as a Blob.
 */
test("renderPortfolio POSTs to /portfolio/:id/render/:format and returns blob", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ text: "<html>portfolio</html>" });
  };

  const blob = await renderPortfolio("p1", "html");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/render/html");
  assert.equal(calls[0].init?.method, "POST");
  assert.ok(blob instanceof Blob);
});

/**
 * Verifies that exportPortfolio sends a POST to /portfolio/:id/export/:format
 * to trigger a server-side export to the default output path.
 */
test("exportPortfolio POSTs to /portfolio/:id/export/:format", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { path: "/out/portfolio.html" } });
  };

  await exportPortfolio("p1", "html");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/export/html");
  assert.equal(calls[0].init?.method, "POST");
});

/**
 * Verifies that exportPortfolioCustom sends a POST to /portfolio/:id/export/:format/custom
 * with the custom output path in the request body.
 */
test("exportPortfolioCustom POSTs path to /portfolio/:id/export/:format/custom", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await exportPortfolioCustom("p1", "html", "/home/user/site");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/export/html/custom");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { path: "/home/user/site" });
});

/**
 * Verifies that addPortfolioProjectManual sends a POST to /portfolio/:id/add/project/manual
 * with a manually supplied project payload in the request body.
 */
test("addPortfolioProjectManual POSTs manual payload to /portfolio/:id/add/project/manual", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const proj = { title: "Side Project", description: "Cool app" };
  await addPortfolioProjectManual("p1", proj);

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/add/project/manual");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), proj);
});

/**
 * Verifies that addPortfolioSkill sends a POST to /portfolio/:id/add/skill
 * with the skill category object in the request body.
 */
test("addPortfolioSkill POSTs skill payload to /portfolio/:id/add/skill", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  const skill = { label: "Frameworks", details: "React, Vue" };
  await addPortfolioSkill("p1", skill);

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/add/skill");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), skill);
});

/**
 * Verifies that appendPortfolioSkill sends a POST to /portfolio/:id/skill/:label/append
 * with the additional skill details in the request body.
 */
test("appendPortfolioSkill POSTs details to /portfolio/:id/skill/:label/append", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await appendPortfolioSkill("p1", "Frameworks", "Svelte");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/skill/Frameworks/append");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { details: "Svelte" });
});

/**
 * Verifies that removePortfolioSkill sends a DELETE to /portfolio/:id/skill/:label.
 */
test("removePortfolioSkill sends DELETE /portfolio/:id/skill/:label", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await removePortfolioSkill("p1", "Frameworks");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/skill/Frameworks");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that removePortfolioProject sends a DELETE to /portfolio/:id/project/:name
 * with the project name percent-encoded.
 */
test("removePortfolioProject sends DELETE /portfolio/:id/project/:name", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await removePortfolioProject("p1", "My Project");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/p1/project/My%20Project");
  assert.equal(calls[0].init?.method, "DELETE");
});

/**
 * Verifies that setPortfolioShowcaseRole sends a POST to
 * /portfolio-showcase/:name/role with the role in the request body.
 */
test("setPortfolioShowcaseRole POSTs role to /portfolio-showcase/:name/role", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, init });
    return makeResponse({ json: { ok: true } });
  };

  await setPortfolioShowcaseRole("My Project", "Lead Developer");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio-showcase/My%20Project/role");
  assert.equal(calls[0].init?.method, "POST");
  assert.deepEqual(JSON.parse(calls[0].init?.body), { role: "Lead Developer" });
});

/**
 * Verifies that getPortfolioShowcaseRole issues a GET to
 * /portfolio-showcase/:name/role and returns the parsed role object.
 */
test("getPortfolioShowcaseRole calls GET /portfolio-showcase/:name/role", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { role: "Lead Developer" } });
  };

  const result = await getPortfolioShowcaseRole("My Project");

  assert.equal(calls[0], "http://localhost:8000/portfolio-showcase/My%20Project/role");
  assert.deepEqual(result, { role: "Lead Developer" });
});

// ---------------------------------------------------------------------------
// Resume award endpoints
// ---------------------------------------------------------------------------

test("addResumeAward calls POST /resume/:id/add/award with JSON body", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method, body: init?.body });
    return makeResponse({ json: { status: "Award added." } });
  };

  const result = await addResumeAward("test 123", {
    name: "Best Project",
    date: "2025-04",
    location: "UBC",
  });

  assert.equal(calls[0].url, "http://localhost:8000/resume/test%20123/add/award");
  assert.equal(calls[0].method, "POST");
  const body = JSON.parse(calls[0].body);
  assert.equal(body.name, "Best Project");
  assert.equal(body.date, "2025-04");
  assert.deepEqual(result, { status: "Award added." });
});

test("removeResumeAward calls DELETE /resume/:id/award/:name", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method });
    return makeResponse({ json: { status: "Award removed." } });
  };

  await removeResumeAward("test 123", "Best Project");

  assert.equal(calls[0].url, "http://localhost:8000/resume/test%20123/award/Best%20Project");
  assert.equal(calls[0].method, "DELETE");
});

// ---------------------------------------------------------------------------
// Skill level update endpoints
// ---------------------------------------------------------------------------

test("updateResumeSkillLevel calls POST /resume/:id/skill/:label/level", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method, body: init?.body });
    return makeResponse({ json: { status: "Updated", details: "Python (**Advanced**)" } });
  };

  const result = await updateResumeSkillLevel("test 123", "Languages", "Python", "Advanced");

  assert.equal(calls[0].url, "http://localhost:8000/resume/test%20123/skill/Languages/level");
  assert.equal(calls[0].method, "POST");
  const body = JSON.parse(calls[0].body);
  assert.equal(body.skill_name, "Python");
  assert.equal(body.level, "Advanced");
  assert.deepEqual(result, { status: "Updated", details: "Python (**Advanced**)" });
});

test("updatePortfolioSkillLevel calls POST /portfolio/:id/skill/:label/level", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method, body: init?.body });
    return makeResponse({ json: { status: "Updated", details: "Python (**Advanced**)" } });
  };

  const result = await updatePortfolioSkillLevel("test 123", "Languages", "Python", "Advanced");

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/test%20123/skill/Languages/level");
  assert.equal(calls[0].method, "POST");
  const body = JSON.parse(calls[0].body);
  assert.equal(body.skill_name, "Python");
  assert.equal(body.level, "Advanced");
});

// ---------------------------------------------------------------------------
// AI project with date overrides
// ---------------------------------------------------------------------------

test("addResumeProjectAI sends date overrides when provided", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method, body: init?.body });
    return makeResponse({ json: { status: "Project added with AI." } });
  };

  await addResumeProjectAI("test 123", "MyProject", {
    start_date: "2025-03",
    end_date: "2026-03",
  });

  assert.equal(calls[0].url, "http://localhost:8000/resume/test%20123/add/project/MyProject/ai");
  assert.equal(calls[0].method, "POST");
  const body = JSON.parse(calls[0].body);
  assert.equal(body.start_date, "2025-03");
  assert.equal(body.end_date, "2026-03");
});

test("addResumeProjectAI works without payload", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method, body: init?.body });
    return makeResponse({ json: { status: "Project added with AI." } });
  };

  await addResumeProjectAI("test 123", "MyProject");

  assert.equal(calls[0].method, "POST");
  assert.equal(calls[0].body, undefined);
});

test("addPortfolioProjectAI sends date overrides when provided", async () => {
  const calls = [];
  global.fetch = async (url, init) => {
    calls.push({ url, method: init?.method, body: init?.body });
    return makeResponse({ json: { status: "Project added with AI." } });
  };

  await addPortfolioProjectAI("test 123", "MyProject", {
    start_date: "2025-03",
    end_date: "2026-03",
  });

  assert.equal(calls[0].url, "http://localhost:8000/portfolio/test%20123/add/project/MyProject/ai");
  assert.equal(calls[0].method, "POST");
  const body = JSON.parse(calls[0].body);
  assert.equal(body.start_date, "2025-03");
  assert.equal(body.end_date, "2026-03");
});