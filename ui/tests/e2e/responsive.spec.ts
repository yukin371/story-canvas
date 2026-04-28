import { test, expect } from "@playwright/test";

test("illustration mobile flow keeps advanced editor collapsed by default", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  await page.getByRole("button", { name: "插画工作区" }).click();

  await expect(page.getByText("高级模板编辑")).toBeVisible();
  await expect(page.locator("details.template-editor-shell")).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "生成" })).toBeVisible();
});
