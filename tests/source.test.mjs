import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
test('all original page routes are present', () => {
  for (const file of ['index.astro','404.astro','articles/index.astro','articles/[slug].astro','categories/index.astro','about/index.astro','contact/index.astro','privacy/index.astro','editorial/index.astro','disclaimer/index.astro']) assert.ok(existsSync(`src/pages/${file}`), file);
});
