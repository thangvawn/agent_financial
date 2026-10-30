import test from 'node:test'
import process from 'node:process'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
test('R13 runner propagates failed assertions as nonzero exit status', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'northstar-runner-'))
  try {
    fs.mkdirSync(path.join(tmp, 'src/__tests__'), { recursive: true })
    fs.copyFileSync(new URL('../../../scripts/test-runner.mjs', import.meta.url), path.join(tmp, 'runner.mjs'))
    fs.writeFileSync(path.join(tmp, 'src/__tests__/probe.test.mjs'), "import test from 'node:test';import assert from 'node:assert/strict';test('probe',()=>assert.equal(1,2));")
    const env = { ...process.env }; delete env.NODE_TEST_CONTEXT
    const result = spawnSync(process.execPath, ['runner.mjs'], { cwd: tmp, encoding: 'utf8', env })
    assert.match(result.stdout, /fail 1/)
    assert.equal(result.status, 1)
  } finally { fs.rmSync(tmp, { recursive: true, force: true }) }
})
