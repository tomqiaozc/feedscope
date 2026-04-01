import { test, expect } from "@playwright/test";

test.describe("Smoke tests", () => {
  test("login page loads", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveTitle(/FeedScope/i);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("unauthenticated user redirected to login", async ({ page }) => {
    await page.goto("/");
    // Should redirect to login or show login page
    await expect(page).toHaveURL(/login/);
  });
});
