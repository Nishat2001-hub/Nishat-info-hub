import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
function walk(path) { return readdirSync(path).flatMap(name => { const file=join(path,name); return statSync(file).isDirectory() ? walk(file) : [file]; }); }
test('built pages have valid local links, assets, Bengali language and SEO', () => {
  assert.ok(existsSync('dist/index.html'),'Run npm run build before npm test');
  const files = walk('dist').filter(file => file.endsWith('.html'));
  assert.ok(files.length >= 17);
  for (const file of files) {
    const html = readFileSync(file,'utf8');
    assert.match(html, /lang="bn"/); assert.match(html, /rel="canonical"/); assert.match(html, /name="description"/);
    for (const [,href] of html.matchAll(/(?:href|src)="([^"#]+)"/g)) {
      if (/^(?:https?:|mailto:|data:|tel:)/.test(href)) continue;
      const clean=decodeURIComponent(href.split(/[?#]/)[0]);
      const target=clean.startsWith('/') ? join('dist',clean) : join(dirname(file),clean);
      assert.ok(existsSync(target) || existsSync(join(target,'index.html')), `${file}: broken link ${href}`);
    }
    for (const [,json] of html.matchAll(/<script[^>]+type="application\/ld\+json"[^>]*>(.*?)<\/script>/gs)) assert.doesNotThrow(() => JSON.parse(json));
  }
});
test('sitemap and robots share the configured site origin', () => {
  const site = process.env.SITE_URL || 'https://nishat-info-hub.pages.dev';
  assert.ok(readFileSync('dist/robots.txt','utf8').includes(`${site}/sitemap-index.xml`));
  assert.ok(readFileSync('dist/sitemap-0.xml','utf8').includes(`${site}/articles/job-circular-guide/`));
  assert.ok(!readFileSync('dist/sitemap-0.xml','utf8').includes('/404/'));
});
