import { test, expect } from "@playwright/test";

/**
 * Authenticated page tests.
 *
 * We inject a fake session cookie to bypass the proxy auth check.
 * The proxy checks for `authjs.session-token` or `__Secure-authjs.session-token`.
 * With the cookie present, pages render without redirecting to /login.
 *
 * Note: API calls from pages will fail (no real backend), but the pages
 * should still render their shell/skeleton without 500 errors.
 */

const DASHBOARD_ROUTES = [
  { path: "/", heading: "Dashboard" },
  { path: "/watchlist", heading: "Watchlists" },
  { path: "/groups", heading: "Groups" },
  { path: "/explore", heading: "Explore" },
  { path: "/settings", heading: "Settings" },
  { path: "/ai-settings", heading: "AI Settings" },
  { path: "/webhooks", heading: "Webhooks" },
  { path: "/usage", heading: "Usage" },
];

const NAV_ITEMS = [
  "Dashboard",
  "Watchlists",
  "Groups",
  "Explore",
  "Settings",
  "AI Settings",
  "Webhooks",
  "Usage",
];

test.describe("Authenticated pages", () => {
  test.beforeEach(async ({ context }) => {
    // Inject fake session cookie so proxy allows access
    await context.addCookies([
      {
        name: "authjs.session-token",
        value: "fake-test-session-token",
        domain: "localhost",
        path: "/",
      },
    ]);
  });

  for (const route of DASHBOARD_ROUTES) {
    test(`${route.path} renders without error`, async ({ page }) => {
      const response = await page.goto(route.path);
      // Should not redirect to login
      expect(page.url()).not.toContain("/login");
      // Should not be a server error
      expect(response?.status()).toBeLessThan(500);
    });

    test(`${route.path} has "${route.heading}" heading`, async ({ page }) => {
      await page.goto(route.path);
      await expect(
        page.getByRole("heading", { name: route.heading }).first(),
      ).toBeVisible({ timeout: 10_000 });
    });
  }

  test("sidebar renders with expected nav items", async ({ page }) => {
    await page.goto("/");
    // Sidebar nav links are rendered on desktop
    for (const item of NAV_ITEMS) {
      await expect(
        page.getByRole("link", { name: item }).first(),
      ).toBeAttached();
    }
  });

  test("theme toggle is visible and clickable", async ({ page }) => {
    await page.goto("/");
    const toggle = page.getByRole("button", { name: /toggle theme/i });
    await expect(toggle).toBeVisible();
    // Click should not cause errors
    await toggle.click();
    // Still visible after click
    await expect(toggle).toBeVisible();
  });

  test("sidebar collapse toggle works", async ({ page }) => {
    await page.goto("/");
    // Find the sidebar collapse button (PanelLeftClose icon)
    const collapseBtn = page
      .locator("aside")
      .getByRole("button")
      .first();
    await expect(collapseBtn).toBeVisible();
    await collapseBtn.click();
    // Sidebar should still be present but narrower
    const aside = page.locator("aside");
    await expect(aside).toBeVisible();
  });
});
