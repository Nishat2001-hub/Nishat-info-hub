import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
const originals=JSON.parse(readFileSync(new URL('../tests/original-content.json',import.meta.url)));
test('all eight V1.2 articles are preserved byte for byte', () => {
  assert.equal(Object.keys(originals).length, 8);
  for (const [file, hash] of Object.entries(originals)) assert.equal(createHash('sha256').update(readFileSync(file)).digest('hex'), hash, file);
});
