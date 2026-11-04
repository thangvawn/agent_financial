import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import process from 'node:process'

const runner = fileURLToPath(new URL('../../../scripts/test-runner.mjs', import.meta.url))

function runFixture(args, source = "import test from 'node:test'; test('sample behavior', () => {})") {
  const directory = mkdtempSync(join(tmpdir(), 'northstar-test-runner-'))
  try {
    mkdirSync(join(directory, 'src/__tests__/feature'), { recursive: true })
    if (source !== null) writeFileSync(join(directory, 'src/__tests__/feature/sample.test.mjs'), source)
    const env = { ...process.env }
    delete env.NODE_TEST_CONTEXT
    return spawnSync(process.execPath, [runner, ...args], {
      cwd: directory, encoding: 'utf8', timeout: 10000, env,
    })
  } finally {
    rmSync(directory, { recursive: true, force: true })
  }
}

test('test command rejects a filter that selects no tests', () => {
  const result = runFixture(['--testPathPattern=missing-feature'])
  assert.equal(result.status, 1, result.stdout + result.stderr)
  assert.match(result.stderr, /No test files found/)
})

test('test command fails for an empty test directory', () => {
  const result = runFixture([], null)
  assert.equal(result.status, 1)
})

test('test command rejects unknown or incomplete options', async (t) => {
  for (const args of [['--typo'], ['--testPathPattern'], ['--testPathPattern='], ['--testPathPattern', '--typo']]) {
    await t.test(args.join(' '), () => {
      const result = runFixture(args)
      assert.equal(result.status, 2, result.stdout + result.stderr)
    })
  }
})

test('test command accepts both filter spellings and runs the selected behavior', () => {
  for (const args of [['--testPathPattern=feature/'], ['--testPathPattern', 'sample.test']]) {
    const result = runFixture(args)
    assert.equal(result.status, 0, result.stdout + result.stderr)
    assert.match(result.stdout, /sample behavior/)
  }
})

test('test command propagates a failing assertion', () => {
  const result = runFixture([], "import test from 'node:test'; test('broken behavior', () => { throw new Error('expected failure') })")
  assert.equal(result.status, 1, result.stdout + result.stderr)
  assert.match(result.stdout, /expected failure/)
})
