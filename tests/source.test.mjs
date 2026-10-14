import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
const originals = JSON.parse(readFileSync(new URL('./original-content.json', import.meta.url)));
test('all eight V1.2 articles are preserved byte for byte', () => {
  assert.equal(Object.keys(originals).length, 8);
  for (const [file, hash] of Object.entries(originals)) assert.equal(createHash('sha256').update(readFileSync(file)).digest('hex'), hash, file);
});
test('all original page routes are present', () => {
  for (const file of ['index.astro','404.astro','articles/index.astro','articles/[slug].astro','categories/index.astro','about/index.astro','contact/index.astro','privacy/index.astro','editorial/index.astro','disclaimer/index.astro']) assert.ok(existsSync(`src/pages/${file}`), file);
});
