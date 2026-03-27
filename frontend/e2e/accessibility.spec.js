import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function installApiMocks(page) {
  const state = {
    config: {
      consented: {
        external: true,
        "Data consent": true
      },
      "First Name": "Jane",
      "Last Name": "Doe"
    },
    projects: ["sample-project"],
    insights: [],
    representation: {
      ordered_projects: ["sample-project"],
      chronology: {},
      highlighted_skills: [],
      showcase_projects: ["sample-project"]
    }
  };

  await page.route("http://localhost:8000/**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const { pathname } = url;

    const json = async (status, body) => route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(body)
    });

    if (pathname === "/config/get" && method === "GET") return json(200, state.config);
    if (pathname === "/projects/" && method === "GET") return json(200, state.projects);
    if (pathname === "/insights/projects" && method === "GET") return json(200, state.insights);
    if (pathname === "/representation/preferences" && method === "GET") return json(200, state.representation);
    if (pathname === "/representation/preferences" && method === "POST") {
      const payload = request.postDataJSON();
      state.representation = { ...state.representation, ...payload };
      return json(200, state.representation);
    }
    if (pathname === "/representation/projects" && method === "GET") return json(200, state.projects);
    if (pathname.startsWith("/projects/") && method === "GET") return json(200, { analysis: {} });
    if (pathname === "/resumes" && method === "GET") return json(200, []);
    if (pathname === "/portfolios" && method === "GET") return json(200, []);
    return json(200, { ok: true });
  });
}

test.describe("WCAG 2.0/2.1/2.2 A/AA checks", () => {
  const routes = ["/", "/config", "/upload", "/projects", "/dashboard", "/workspace", "/representation"];

  for (const route of routes) {
    test(`has no detectable axe violations on ${route}`, async ({ page }) => {
      await installApiMocks(page);
      await page.goto(route);

      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"])
        .analyze();

      expect(results.violations, `${route} violations: ${results.violations.map((v) => v.id).join(", ")}`).toEqual([]);
    });
  }
});
