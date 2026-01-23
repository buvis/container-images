import { test, expect } from '@playwright/test';

test.describe('Exchanger E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/health', async route => route.fulfill({ json: { status: 'ok' } }));
    await page.route('**/api/favorites', async route => route.fulfill({ json: ['EUR', 'USD'] }));
    await page.route('**/api/providers/status', async route => route.fulfill({ json: [
      { name: 'CNB', healthy: true, symbol_count: 10 },
      { name: 'FCS', healthy: false, symbol_count: 0 }
    ]}));
    await page.route('**/api/task_status', async route => route.fulfill({ json: {} }));
    await page.route('**/api/backups', async route => route.fulfill({ json: [] }));
    await page.route('**/api/rates*', async route => route.fulfill({ json: [] }));
    await page.route('**/api/rates/coverage*', async route => route.fulfill({ json: {} }));
    await page.route('**/api/rates/history*', async route => route.fulfill({ json: [] }));
  });

  test('Dashboard loads and health indicator is visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Exchanger Dashboard' })).toBeVisible();
    await expect(page.getByText('OK')).toBeVisible();
  });

  test('Rates page navigates and calendar picker exists', async ({ page }) => {
    await page.goto('/rates');
    await expect(page.getByRole('heading', { name: 'Rates Explorer' })).toBeVisible();
    // Verify calendar headers exist
    await expect(page.getByText('Su', { exact: true })).toBeVisible();
    await expect(page.getByText('Mo', { exact: true })).toBeVisible();
  });

  test('Admin page tabs work', async ({ page }) => {
    await page.goto('/admin');
    await expect(page.getByRole('heading', { name: 'Admin Panel' })).toBeVisible();
    
    // Default tab
    await expect(page.getByRole('heading', { name: 'Trigger Backfill' })).toBeVisible();
    
    // Switch to Symbols
    await page.getByRole('button', { name: 'Symbols' }).click();
    await expect(page.getByRole('heading', { name: 'Populate Symbols' })).toBeVisible();
    
    // Switch to Backups
    await page.getByRole('button', { name: 'Backups' }).click();
    await expect(page.getByRole('heading', { name: 'Manage Backups' })).toBeVisible();
  });

  test('Providers page renders provider cards', async ({ page }) => {
    await page.goto('/providers');
    await expect(page.getByRole('heading', { name: 'Providers' })).toBeVisible();
    
    // Check mock data
    await expect(page.getByText('CNB')).toBeVisible();
    await expect(page.getByText('FCS')).toBeVisible();
    // Check healthy indicator
    await expect(page.locator('.text-green-400[title="Healthy"]')).toBeVisible();
  });
});
