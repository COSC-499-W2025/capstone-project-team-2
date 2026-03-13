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

test("fetchResume calls GET /resume/:id with encoding", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { id: "r 1" } });
  };

  await fetchResume("r 1");

  assert.equal(calls[0], "http://localhost:8000/resume/r%201");
});

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

test("fetchPortfolio calls GET /portfolio/:id with encoding", async () => {
  const calls = [];
  global.fetch = async (url) => {
    calls.push(url);
    return makeResponse({ json: { id: "p 1" } });
  };

  await fetchPortfolio("p 1");

  assert.equal(calls[0], "http://localhost:8000/portfolio/p%201");
});

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