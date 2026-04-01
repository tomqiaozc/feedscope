import { test, expect } from "@playwright/test";

test.describe("Unauthenticated navigation", () => {
  test("/ redirects to /login", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/login/);
  });

  test("/watchlist redirects to /login", async ({ page }) => {
    await page.goto("/watchlist");
    await expect(page).toHaveURL(/\/login/);
  });

  test("/settings redirects to /login", async ({ page }) => {
    await page.goto("/settings");
    await expect(page).toHaveURL(/\/login/);
  });

  test("/groups redirects to /login", async ({ page }) => {
    await page.goto("/groups");
    await expect(page).toHaveURL(/\/login/);
  });

  test("/explore redirects to /login", async ({ page }) => {
    await page.goto("/explore");
    await expect(page).toHaveURL(/\/login/);
  });

  test("/webhooks redirects to /login", async ({ page }) => {
    await page.goto("/webhooks");
    await expect(page).toHaveURL(/\/login/);
  });

  test("/usage redirects to /login", async ({ page }) => {
    await page.goto("/usage");
    await expect(page).toHaveURL(/\/login/);
  });

  test("redirect preserves callbackUrl", async ({ page }) => {
    await page.goto("/watchlist");
    const url = new URL(page.url());
    expect(url.searchParams.get("callbackUrl")).toBe("/watchlist");
  });

  test("login page renders with Google sign-in button", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Feedscope" })).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in with google/i })).toBeVisible();
  });

  test("login page has correct branding text", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText("Social media analytics platform")).toBeVisible();
  });
});
