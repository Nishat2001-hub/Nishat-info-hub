import { writeFileSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
const fixtures = [
  ['verification-draft', 'draft: true\npubDate: 2000-01-01'],
  ['verification-future', 'draft: false\npubDate: 2999-01-01'],
];
const build = () => execFileSync('npm', ['run', 'build'], {stdio:'inherit'});
const created = [];
try {
  for (const [id, metadata] of fixtures) {
    const path = `src/content/articles/${id}.md`;
    assert.ok(!existsSync(path), 'Test fixture must not overwrite content');
    created.push(path);
    writeFileSync(path, `---\ntitle: ${id}\ndescription: Publication regression fixture\ncategory: টিউটোরিয়াল\n${metadata}\n---\nTest fixture.\n`);
  }
  build();
  for (const [id] of fixtures) {
    assert.ok(!existsSync(`dist/articles/${id}`), `${id} must not have a public route`);
    for (const file of ['dist/index.html','dist/articles/index.html','dist/sitemap-0.xml']) assert.ok(!readFileSync(file,'utf8').includes(id), `${id} leaked into ${file}`);
  }
  console.log('Draft and future content excluded from homepage, archive, routes and sitemap.');
} finally {
  for (const path of created) rmSync(path, {force:true});
  build();
}
