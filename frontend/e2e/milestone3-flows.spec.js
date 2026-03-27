import { expect, test } from "@playwright/test";
import path from "node:path";

const ZIP_FIXTURE = path.resolve(process.cwd(), "../milestone_2_test_files/test-data-snapshot1.zip");

function makeInsight(projectName = "sample-project") {
  return {
    project_name: projectName,
    analyzed_at: "2026-03-21T19:30:00Z",
    project_type: "web",
    summary: "Sample analyzed project used for browser workflow tests.",
    skills: ["React", "Testing", "Next.js"],
    stats: {
      top_contribution_count: 3,
      top_contribution_percentage: 72,
      skill_count: 3
    },
    hierarchy: {
      name: projectName,
      type: "DIR",
      children: [
        { name: "src", type: "DIR", children: [{ name: "app.js", type: "FILE" }] },
        { name: "tests", type: "DIR", children: [{ name: "app.spec.js", type: "FILE" }] },
        { name: "README.md", type: "FILE" }
      ]
    }
  };
}

function makeResume(id) {
  return {
    contact: {
      name: "Jane Doe",
      email: "jane@example.com",
      phone: "555-0100",
      location: "Vancouver, BC",
      website: "https://example.com"
    },
    summary: "Resume test document.",
    skills: [
      { label: "Languages", details: "JavaScript, Python" }
    ],
    projects: [],
    education: [],
    experience: [],
    design: { theme: "sb2nov" },
    metadata: { id }
  };
}

function makePortfolio(id) {
  return {
    contact: {
      name: "Jane Doe",
      email: "jane@example.com",
      location: "Vancouver, BC",
      website: "https://example.com"
    },
    summary: "Portfolio test document.",
    skills: [
      { label: "Frontend", details: "React, Next.js" }
    ],
    projects: [],
    design: { theme: "sb2nov" },
    metadata: { id }
  };
}

async function installApiMocks(page, options = {}) {
  const state = {
    config: options.config ?? { consented: { external: false, "Data consent": true }, "First Name": "", "Last Name": "" },
    projects: options.projects ?? [],
    insights: options.insights ?? [],
    representation: options.representation ?? {
      project_order: (options.insights ?? []).map((item) => item.project_name).filter(Boolean),
      chronology_corrections: {},
      comparison_attributes: ["languages", "frameworks", "duration_estimate"],
      highlight_skills: [],
      showcase_projects: [],
      project_overrides: {}
    },
    resumes: options.resumes ?? [],
    portfolios: options.portfolios ?? [],
    resumeDocs: options.resumeDocs ?? {},
    portfolioDocs: options.portfolioDocs ?? {}
  };

  await page.route("http://localhost:8000/**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const { pathname, searchParams } = url;

    const json = async (status, body) => route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body)
    });

    if (pathname === "/config/get" && method === "GET") {
      await json(200, state.config);
      return;
    }

    if (pathname === "/privacy-consent" && method === "POST") {
      const body = request.postDataJSON();
      state.config = {
        ...state.config,
        consented: {
          external: Boolean(body.external_consent),
          "Data consent": Boolean(body.data_consent)
        }
      };
      await json(200, { ok: true });
      return;
    }

    if (pathname === "/config/update" && method === "POST") {
      state.config = request.postDataJSON();
      await json(200, state.config);
      return;
    }

    if (pathname === "/projects/" && method === "GET") {
      await json(200, state.projects);
      return;
    }

    if (pathname === "/projects/upload" && method === "POST") {
      const projectName = "sample-project";
      if (!state.projects.includes(projectName)) state.projects.push(projectName);
      const existing = state.insights.find((item) => item.project_name === projectName);
      if (!existing) state.insights.push(makeInsight(projectName));
      await json(200, { project_name: projectName });
      return;
    }

    if (pathname === "/analyze" && method === "GET") {
      const projectName = searchParams.get("project_name") || "sample-project";
      if (!state.projects.includes(projectName)) state.projects.push(projectName);
      const existing = state.insights.find((item) => item.project_name === projectName);
      if (!existing) state.insights.push(makeInsight(projectName));
      await json(200, { ok: true, project_name: projectName });
      return;
    }

    if (pathname === "/insights/projects" && method === "GET") {
      await json(200, state.insights);
      return;
    }

    if (pathname === "/representation/projects" && method === "GET") {
      const projectMap = new Map();
      for (const insight of state.insights) {
        if (insight?.project_name) projectMap.set(insight.project_name, insight);
      }
      const preferredOrder = Array.isArray(state.representation?.project_order) ? state.representation.project_order : [];
      const orderedNames = [];
      for (const name of preferredOrder) {
        if (projectMap.has(name) && !orderedNames.includes(name)) orderedNames.push(name);
      }
      for (const name of projectMap.keys()) {
        if (!orderedNames.includes(name)) orderedNames.push(name);
      }

      let orderedProjects = orderedNames.map((name) => {
        const source = projectMap.get(name);
        const overrides = state.representation?.project_overrides?.[name] || {};
        return {
          ...source,
          project_type: overrides.contribution_type || source.project_type,
          contribution_type: overrides.contribution_type || source.project_type,
          duration_estimate: overrides.duration_estimate || source.duration_estimate
        };
      });

      const showcaseSet = new Set(Array.isArray(state.representation?.showcase_projects) ? state.representation.showcase_projects : []);
      const onlyShowcase = searchParams.get("only_showcase") === "true";
      if (onlyShowcase && showcaseSet.size > 0) {
        orderedProjects = orderedProjects.filter((project) => showcaseSet.has(project.project_name));
      } else if (showcaseSet.size > 0) {
        const showcased = orderedProjects.filter((project) => showcaseSet.has(project.project_name));
        const others = orderedProjects.filter((project) => !showcaseSet.has(project.project_name));
        orderedProjects = [...showcased, ...others];
      }

      await json(200, {
        projects: orderedProjects,
        project_order: state.representation.project_order || [],
        chronology_corrections: state.representation.chronology_corrections || {},
        comparison_attributes: state.representation.comparison_attributes || ["languages", "frameworks", "duration_estimate"],
        highlight_skills: state.representation.highlight_skills || [],
        showcase_projects: state.representation.showcase_projects || [],
        project_overrides: state.representation.project_overrides || {}
      });
      return;
    }

    if (pathname === "/representation/preferences" && method === "GET") {
      await json(200, state.representation);
      return;
    }

    if (pathname === "/representation/preferences" && method === "POST") {
      const body = request.postDataJSON();
      state.representation = {
        ...state.representation,
        ...body
      };
      await json(200, state.representation);
      return;
    }

    if (pathname === "/resumes" && method === "GET") {
      await json(200, state.resumes);
      return;
    }

    if (pathname === "/portfolios" && method === "GET") {
      await json(200, state.portfolios);
      return;
    }

    if (pathname === "/resume/generate" && method === "POST") {
      const { name } = request.postDataJSON();
      const id = `${String(name || "resume").trim().replace(/\s+/g, "_")}_resume_001`;
      state.resumeDocs[id] = makeResume(id);
      state.resumes = [{ id, name: String(name || "Resume").trim(), created_at: "2026-03-21T19:30:00Z" }];
      await json(200, { resume_id: id });
      return;
    }

    if (pathname === "/portfolio/generate" && method === "POST") {
      const { name } = request.postDataJSON();
      const id = `${String(name || "portfolio").trim().replace(/\s+/g, "_")}_portfolio_001`;
      state.portfolioDocs[id] = makePortfolio(id);
      state.portfolios = [{ id, name: String(name || "Portfolio").trim(), created_at: "2026-03-21T19:30:00Z" }];
      await json(200, { portfolio_id: id });
      return;
    }

    if (pathname.startsWith("/resume/") && method === "GET") {
      const id = decodeURIComponent(pathname.slice("/resume/".length));
      await json(200, state.resumeDocs[id] ?? makeResume(id));
      return;
    }

    if (pathname.startsWith("/portfolio/") && method === "GET") {
      const id = decodeURIComponent(pathname.slice("/portfolio/".length));
      await json(200, state.portfolioDocs[id] ?? makePortfolio(id));
      return;
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: `Unhandled mock route: ${method} ${pathname}` })
    });
  });
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.clear();
  });
});

test("saves config consent and profile details", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/config");

  await expect(page.getByRole("heading", { name: "User Configuration" })).toBeVisible();
  // Scope to the external consent control (second .config-consent-control) to avoid
  // matching the local consent "Allow" button
  await page.locator(".config-consent-control").nth(1).locator("button").first().click();
  await page.getByLabel("Full name").fill("Jane Doe");
  await page.getByRole("button", { name: "Save Configuration" }).click();

  await expect(page.getByText("Configuration saved.")).toBeVisible();
  // nth(0) = full name input row (Update Settings), nth(1) = local, nth(2) = external, nth(3) = name
  await expect(page.locator(".config-grid .settings-row").nth(2)).toContainText("Allow");
  await expect(page.locator(".config-grid .settings-row").nth(3)).toContainText("Jane Doe");
});

test("uploads and analyzes a zip, then shows it on the dashboard", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/upload");

  await expect(page.getByRole("heading", { name: /Project Upload/ })).toBeVisible();
  await page.locator('input[type="file"]').first().setInputFiles(ZIP_FIXTURE);
  await page.getByRole("button", { name: /Analyze ZIP/ }).click();

  await expect(page.getByText("Analysis complete for sample-project.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Analysis Summary" })).toBeVisible();

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: /Dashboard/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Top 3 Projects/ })).toBeVisible();
  await expect(page.getByText("sample-project")).toBeVisible();
  await expect(page.getByText("3").first()).toBeVisible();
});

test("generates and loads a resume in the workspace", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/workspace");

  await expect(page.getByRole("heading", { name: /Resume \+ Portfolio Builder/ })).toBeVisible();
  await page.getByLabel("Full name").fill("Jane Doe");
  await page.getByLabel("Theme").selectOption("sb2nov");
  await page.getByRole("button", { name: "Generate Resume", exact: true }).click();

  await expect(page.getByText("Resume created.")).toBeVisible();
  await expect(page.locator(".workspace-page .settings-row").filter({ hasText: "Active ID" })).toContainText("Jane_Doe_resume_001");
});

test("generates and loads a portfolio in the workspace", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/workspace");
  await page.getByRole("radio", { name: "P o r t f o l i o", exact: true }).click();

  await page.getByLabel("Full name").fill("Jane Doe");
  await page.getByLabel("Theme").selectOption("sb2nov");
  await page.getByRole("button", { name: "Generate Portfolio", exact: true }).click();

  await expect(page.getByText("Portfolio created.")).toBeVisible();
  await expect(page.locator(".workspace-page .settings-row").filter({ hasText: "Active ID" })).toContainText("Jane_Doe_portfolio_001");
});

test("dashboard public mode persists and workspace remains authoring", async ({ page }) => {
  await installApiMocks(page, { insights: [makeInsight("sample-project")] });

  await page.goto("/dashboard");
  await expect(page.getByRole("heading", { name: /Dashboard/ })).toBeVisible();

  await page.getByRole("radio", { name: "P u b l i c", exact: true }).click();

  await expect(page.getByLabel("Search")).toBeVisible();
  await expect(page.getByLabel("Type")).toBeVisible();
  await expect(page.getByLabel("Skill")).toBeVisible();
  await expect(page.getByRole("button", { name: /Open Filters/i })).toHaveCount(0);
  expect(await page.evaluate(() => window.localStorage.getItem("dashboardMode"))).toBe("public");

  await page.goto("/workspace");
  await expect(page.getByRole("heading", { name: /Resume \+ Portfolio Builder/ })).toBeVisible();
  await expect(page.getByLabel("Full name")).toBeVisible();
});

test("first-time user with no consent is redirected to config and sees consent document expanded", async ({ page }) => {
  await installApiMocks(page, {
    config: { "First Name": "", "Last Name": "" }
  });

  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/config$/);
  await expect(page.getByRole("heading", { name: "Data Consent Agreement" })).toBeVisible();
  await expect(page.locator(".consent-document")).toBeVisible();
  await expect(page.getByRole("button", { name: /Collapse/ })).toBeVisible();
});

test("returning user with consent set sees consent document collapsed", async ({ page }) => {
  await installApiMocks(page, {
    config: { consented: { external: true, "Data consent": true }, "First Name": "Jane", "Last Name": "Doe" }
  });

  await page.goto("/config");

  await expect(page.getByRole("heading", { name: "Data Consent Agreement" })).toBeVisible();
  await expect(page.locator(".consent-document")).not.toBeVisible();
  await expect(page.getByRole("button", { name: /View agreement/ })).toBeVisible();
});

test("local consent deny warning appears when set to do not allow", async ({ page }) => {
  await installApiMocks(page, {
    config: { consented: { external: true, "Data consent": true }, "First Name": "", "Last Name": "" }
  });

  await page.goto("/config");

  // Switch local consent to "Do not allow" — first .config-consent-control, last button
  await page.locator(".config-consent-control").first().locator("button").last().click();

  await expect(page.locator(".consent-deny-warning").first()).toBeVisible();
  await expect(page.locator(".consent-deny-warning").first()).toContainText("Local consent must be allowed");
});

test("external consent deny warning appears when set to do not allow", async ({ page }) => {
  await installApiMocks(page, {
    config: { consented: { external: true, "Data consent": true }, "First Name": "", "Last Name": "" }
  });

  await page.goto("/config");

  // Switch external consent to "Do not allow" — second .config-consent-control, last button
  await page.locator(".config-consent-control").nth(1).locator("button").last().click();

  await expect(page.locator(".consent-deny-warning").last()).toBeVisible();
  await expect(page.locator(".consent-deny-warning").last()).toContainText("External tools are disabled");
});

test("generate with AI button is disabled when external consent is off", async ({ page }) => {
  await installApiMocks(page, {
    config: { consented: { external: false, "Data consent": true }, "First Name": "", "Last Name": "" }
  });

  await page.goto("/workspace");

  await expect(page.getByRole("button", { name: /Generate Resume with AI/ })).toBeDisabled();
});

test("generate with AI button is enabled when external consent is on", async ({ page }) => {
  await installApiMocks(page, {
    config: { consented: { external: true, "Data consent": true }, "First Name": "", "Last Name": "" }
  });

  await page.goto("/workspace");
  await expect(page.getByRole("heading", { name: /Resume \+ Portfolio Builder/ })).toBeVisible();
  // Wait for initial fetches (config, projects, docs) to complete so state is settled
  // before interacting with the controlled select — avoids a race where setExternalAllowed
  // re-render overwrites the DOM select value set by selectOption before onChange propagates
  await page.waitForLoadState("networkidle");
  await page.getByLabel("Theme").selectOption("sb2nov");

  await expect(page.getByRole("button", { name: /Generate Resume with AI/ })).toBeEnabled();
});
