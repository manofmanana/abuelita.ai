Playwright test for Abuelita.ai

Prerequisites:
- Node.js >= 16
- Playwright installed (npm i -D @playwright/test)

Run the single test (ensure your Django dev server is running on localhost:8000):

npx playwright test e2e/playwright/test_bilingual_expand.spec.js

Note: The test assumes the dev server is accessible at http://localhost:8000 and
that the Learn page is reachable at /en/learn/.
