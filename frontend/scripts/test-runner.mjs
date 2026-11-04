import { glob } from 'node:fs/promises'
import { run } from 'node:test'
import { spec } from 'node:test/reporters'
import { resolve } from 'node:path'

const args = process.argv.slice(2)
let pattern = null

for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith('--testPathPattern=')) {
    pattern = args[i].slice('--testPathPattern='.length)
  } else if (args[i] === '--testPathPattern') {
    pattern = args[++i]
  } else {
    console.error(`Unknown option: ${args[i]}. Use --testPathPattern <path substring>.`)
    process.exit(2)
  }
  if (!pattern || pattern.startsWith('--')) {
    console.error('--testPathPattern requires a non-empty path substring.')
    process.exit(2)
  }
}

const testFiles = []
for await (const entry of glob('src/**/__tests__/**/*.test.{js,mjs,jsx}')) {
  if (!pattern || entry.includes(pattern)) {
    testFiles.push(resolve(entry))
  }
}

// Also check top-level src/__tests__
for await (const entry of glob('src/__tests__/*.test.{js,mjs,jsx}')) {
  const full = resolve(entry)
  if (!testFiles.includes(full) && (!pattern || entry.includes(pattern))) {
    testFiles.push(full)
  }
}

if (testFiles.length === 0) {
  console.error(`No test files found${pattern ? ` for ${JSON.stringify(pattern)}` : ''}.`)
  process.exit(1)
}

const testStream = run({ files: testFiles })
testStream.compose(spec).pipe(process.stdout)

testStream.on('error', () => {
  process.exit(1)
})

testStream.on('test:fail', () => { process.exitCode = 1 })
