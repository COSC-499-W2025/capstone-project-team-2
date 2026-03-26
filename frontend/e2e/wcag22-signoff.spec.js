import { expect, test } from "@playwright/test";

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

const routes = ["/", "/config", "/upload", "/projects", "/dashboard", "/workspace", "/representation"];

test.describe("WCAG 2.2 sign-off checks", () => {
  test("keyboard focus reaches actionable controls on every core route", async ({ page }) => {
    await installApiMocks(page);

    for (const route of routes) {
      await page.goto(route);

      // Move focus by keyboard only until the page content section is reached.
      let reachedContentSectionControl = false;
      for (let i = 0; i < 30; i += 1) {
        await page.keyboard.press("Tab");
        reachedContentSectionControl = await page.evaluate(() => {
          const active = document.activeElement;
          if (!active || active === document.body) return false;

          const contentSection = document.querySelector(".content-wrap");
          if (!contentSection || !contentSection.contains(active)) return false;

          const tag = active.tagName.toLowerCase();
          return ["a", "button", "input", "select", "textarea"].includes(tag) || active.hasAttribute("tabindex");
        });

        if (reachedContentSectionControl) break;
      }

      expect(
        reachedContentSectionControl,
        `No keyboard-focusable control reached inside the page content section on ${route}`
      ).toBeTruthy();
    }
  });

  test("accessibility dialog traps focus and closes with Escape while restoring focus", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/workspace");

    const a11yTriggerButton = page.getByRole("button", { name: "Open accessibility menu" });
    await a11yTriggerButton.click();

    const dialog = page.getByRole("dialog", { name: /Accessibility settings/i });
    await expect(dialog).toBeVisible();

    const focusedInsideDialogOnOpen = await page.evaluate(() => {
      const dialogEl = document.getElementById("a11y-panel");
      return Boolean(dialogEl && dialogEl.contains(document.activeElement));
    });
    expect(focusedInsideDialogOnOpen).toBeTruthy();

    // Focus should stay inside dialog while tabbing.
    await page.keyboard.press("Tab");
    const stillInsideDialog = await page.evaluate(() => {
      const dialogEl = document.getElementById("a11y-panel");
      return Boolean(dialogEl && dialogEl.contains(document.activeElement));
    });
    expect(stillInsideDialog).toBeTruthy();

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(a11yTriggerButton).toBeFocused();
  });

  test("mobile reflow and text-spacing override do not create horizontal scroll on core routes", async ({ page }) => {
    await installApiMocks(page);
    await page.setViewportSize({ width: 320, height: 900 });

    for (const route of routes) {
      await page.goto(route);
      await page.addStyleTag({
        content: `
          * { line-height: 1.5 !important; letter-spacing: 0.12em !important; word-spacing: 0.16em !important; }
          p, li, h1, h2, h3, h4 { margin-bottom: 2em !important; }
          html { font-size: 200% !important; }
        `
      });

      const noHorizontalOverflow = await page.evaluate(() => {
        const el = document.scrollingElement || document.documentElement;
        return el.scrollWidth <= el.clientWidth + 1;
      });
      expect(noHorizontalOverflow, `Horizontal overflow detected on ${route} with spacing/zoom overrides`).toBeTruthy();
    }
  });
});
