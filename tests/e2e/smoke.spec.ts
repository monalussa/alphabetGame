import { expect, test } from '@playwright/test';

test('start screen loads with no console errors and no external requests', async ({
  page,
  baseURL,
}) => {
  const consoleErrors: string[] = [];
  const externalRequests: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('request', (request) => {
    if (!request.url().startsWith(baseURL ?? '')) externalRequests.push(request.url());
  });

  await page.goto('/');

  await expect(page.getByRole('button', { name: 'Jouer' })).toBeVisible();
  expect(consoleErrors).toEqual([]);
  expect(externalRequests).toEqual([]);
});

test('production build ships a Content-Security-Policy', async ({ page }) => {
  await page.goto('/');

  const csp = page.locator('meta[http-equiv="Content-Security-Policy"]');

  await expect(csp).toHaveAttribute('content', /default-src 'self'/);
});

test('pressing play opens the first game without CSP violations', async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto('/');

  await page.getByRole('button', { name: 'Jouer' }).click();

  await expect(page.getByRole('button', { name: 'Jouer' })).toBeHidden();
  expect(consoleErrors).toEqual([]);
});
