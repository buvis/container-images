import { test, expect } from '@playwright/test';

test.describe('Exchanger E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses - register specific routes before wildcards
    await page.route('**/api/health', async route => route.fulfill({ json: { status: 'ok' } }));
    await page.route('**/api/favorites', async route => route.fulfill({ json: [
      { provider: 'cnb', provider_symbol: 'EUR' },
      { provider: 'cnb', provider_symbol: 'USD' }
    ]}));
    await page.route('**/api/providers/status', async route => route.fulfill({ json: [
      { name: 'CNB', healthy: true, symbol_count: 10, symbol_counts_by_type: {} },
      { name: 'FCS', healthy: false, symbol_count: 0, symbol_counts_by_type: {} }
    ]}));
    await page.route('**/api/task_status', async route => route.fulfill({ json: {} }));
    await page.route('**/api/backups', async route => route.fulfill({ json: [] }));
    await page.route('**/api/symbols/list*', async route => route.fulfill({ json: [] }));
    await page.route('**/api/rates/coverage*', async route => route.fulfill({ json: {} }));
    await page.route('**/api/rates/missing*', async route => route.fulfill({ json: {} }));
    await page.route('**/api/rates/history*', async route => route.fulfill({ json: [] }));
    await page.route('**/api/rates/list*', async route => route.fulfill({ json: [] }));
    await page.route('**/api/rates*', async route => route.fulfill({ json: [] }));
  });

  test('Dashboard loads and health indicator is visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'System Status' })).toBeVisible();
    await expect(page.getByText('ok', { exact: true })).toBeVisible();
  });

  test('Rates page navigates and calendar picker exists', async ({ page }) => {
    await page.goto('/rates');
    await expect(page.getByRole('heading', { name: 'Rates Explorer' })).toBeVisible();
    // Verify calendar headers exist
    await expect(page.getByText('Su', { exact: true })).toBeVisible();
    await expect(page.getByText('Mo', { exact: true })).toBeVisible();
  });

  test('Admin page shows backfill form', async ({ page }) => {
    await page.goto('/admin');
    // Default tab shows backfill form
    await expect(page.getByRole('heading', { name: 'Trigger Backfill' })).toBeVisible();
  });
});
