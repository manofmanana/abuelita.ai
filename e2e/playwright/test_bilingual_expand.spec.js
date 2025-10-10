const { test, expect } = require('@playwright/test');

// This Playwright test expects the dev server to be running at localhost:8000.
// It navigates to the Learn page, submits a topic, waits for the lesson, then
// clicks the first bilingual toggle and asserts the Spanish column is visible.

test('bilingual expand shows ES column', async ({ page }) => {
  await page.goto('http://localhost:8000/en/learn/');

  // Fill the topic and submit
  await page.fill('#input_text', 'lego');
  await page.click('button:has-text("Learn with Abuelita")');

  // Wait for lesson result to appear
  await page.waitForSelector('#learn-result-body .translation-result', { timeout: 5000 });

  // Click the first bilingual toggle
  const toggle = await page.$('#learn-result-body .bilingual-toggle');
  expect(toggle).not.toBeNull();
  await toggle.click();

  // After clicking, the expanded panel should have class is-open and contain ES text
  const expanded = await page.$('#learn-result-body .bilingual-expanded.is-open');
  expect(expanded).not.toBeNull();
  const text = await expanded.innerText();
  expect(text).toContain('ES:');
});
