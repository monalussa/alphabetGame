import { expect, test, type Page } from '@playwright/test';

async function startGame(page: Page): Promise<string[]> {
  const consoleErrors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Jouer' }).click();
  await expect(page.getByTestId('smash-game')).toBeVisible();
  return consoleErrors;
}

test('pressing a letter shows its character, then its words with pictures', async ({ page }) => {
  const consoleErrors = await startGame(page);

  await page.keyboard.press('a');
  await expect(page.getByText('Madame A', { exact: true })).toBeVisible();

  await expect(async () => {
    await page.keyboard.press('a');
    await expect(page.getByText('nanas')).toBeVisible({ timeout: 500 });
  }).toPass({ timeout: 15_000 });
  await expect(page.locator('img[src$="/images/pineapple.svg"]')).toBeVisible();
  expect(consoleErrors).toEqual([]);
});

test('keys pressed while a letter is playing are ignored', async ({ page }) => {
  await startGame(page);

  await page.keyboard.press('b');
  await page.keyboard.press('c');
  await page.keyboard.press('d');

  await expect(page.getByText('Monsieur B', { exact: true })).toBeVisible();
  await expect(page.getByText('Monsieur C', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Monsieur D', { exact: true })).toHaveCount(0);
});

test('a digit plays a fun burst', async ({ page }) => {
  await startGame(page);

  await page.keyboard.press('1');

  await expect(page.getByTestId('fun-burst')).toBeVisible();
});

test('an accented key (AZERTY é) plays a fun burst', async ({ page }) => {
  await startGame(page);

  await page.evaluate(() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'é' })));

  await expect(page.getByTestId('fun-burst')).toBeVisible();
});

test('holding the parent button for three seconds returns to the start screen', async ({
  page,
}) => {
  await page.clock.install();
  await startGame(page);
  const gate = page.getByRole('button', { name: /Parents/ });
  const box = await gate.boundingBox();
  if (!box) throw new Error('parent gate not visible');

  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.clock.runFor(3100);
  await page.mouse.up();

  await expect(page.getByRole('button', { name: 'Jouer' })).toBeVisible();
});

test('a short tap on the parent button does nothing', async ({ page }) => {
  await page.clock.install();
  await startGame(page);

  await page.getByRole('button', { name: /Parents/ }).click();
  await page.clock.runFor(3100);

  await expect(page.getByTestId('smash-game')).toBeVisible();
});
