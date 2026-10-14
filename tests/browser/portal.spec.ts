import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

test('desktop homepage, theme, navigation and search survive transitions', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('জানুন আজ');
  await expect(page.locator('#logo-intro')).toBeHidden({ timeout: 5000 });
  await page.locator('#theme-toggle').click();
  await expect(page.locator('html')).toHaveClass(/dark/);
  await page.locator('header nav').first().getByRole('link', { name: 'সব লেখা', exact: true }).click();
  await expect(page.locator('#cards > div:visible')).toHaveCount(8);
  await page.locator('#search').fill('অমিল-অনুসন্ধান-123');
  await expect(page.locator('#empty')).toBeVisible();
  await page.locator('#search').fill('');
  await page.locator('#category').selectOption('সরকারি চাকরি');
  await expect(page.locator('#cards > div:visible')).toHaveCount(1);
  await page.locator('#cards > div:visible a').click();
  await expect(page.locator('h1')).toContainText('সরকারি নিয়োগ');
  await expect(page.locator('html')).toHaveClass(/dark/);
  await page.goBack();
  await expect(page.locator('#category')).toHaveValue('সরকারি চাকরি');
  await page.locator('header a[aria-label]').first().click();
  await expect(page.locator('#logo-intro')).toBeHidden();
  await page.locator('#ticker-toggle').click();
  await expect(page.locator('.ticker-track')).toHaveClass(/paused/);
  expect(errors).toEqual([]);
});

test('mobile navigation, keyboard and reduced motion', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  await expect(page.locator('#logo-intro')).toBeHidden();
  expect(await page.locator('.ticker-track').evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.locator('summary').click();
  await expect(page.getByRole('navigation', {name:'মোবাইল নেভিগেশন'})).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('header details')).not.toHaveAttribute('open', '');
  await page.locator('summary').click();
  await page.getByRole('navigation', {name:'মোবাইল নেভিগেশন'}).getByRole('link',{name:'বিভাগ',exact:true}).click();
  await expect(page.locator('h1')).toHaveText('বিভাগসমূহ');
});

test('content works without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: {width:375,height:812} });
  const page = await context.newPage(); await page.goto('/');
  await expect(page.locator('h1')).toBeVisible(); await expect(page.locator('#logo-intro')).toBeHidden();
  await page.locator('summary').click();
  await expect(page.getByRole('navigation',{name:'মোবাইল নেভিগেশন'})).toBeVisible();
  await context.close();
});

test('save desktop, mobile and dark previews', async ({ page }) => {
  await mkdir('preview', {recursive:true});
  await page.emulateMedia({ reducedMotion:'reduce', colorScheme:'light' });
  await page.setViewportSize({width:1440,height:1000}); await page.goto('/');
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({path:'preview/home-desktop.png',fullPage:true});
  await page.locator('#theme-toggle').click();
  await page.screenshot({path:'preview/home-dark.png',fullPage:true});
  await page.locator('#theme-toggle').click();
  await page.setViewportSize({width:375,height:812});
  await page.screenshot({path:'preview/home-mobile.png',fullPage:true});
});
