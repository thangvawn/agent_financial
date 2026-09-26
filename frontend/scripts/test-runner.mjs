import { glob } from 'node:fs/promises'
import { run } from 'node:test'
import { spec } from 'node:test/reporters'
import { resolve, relative } from 'node:path'

const args = process.argv.slice(2)
let pattern = null

for (let i = 0; i < args.length; i++) {
  if (args[i].startsWith('--testPathPattern=')) {
    pattern = args[i].split('=')[1]
  } else if (args[i] === '--testPathPattern' && args[i + 1]) {
    pattern = args[++i]
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
  console.log('No test files found.')
  process.exit(0)
}

const testStream = run({ files: testFiles })
testStream.compose(spec).pipe(process.stdout)

testStream.on('error', () => {
  process.exit(1)
})

testStream.on('end', () => {
  // If failed tests exist, exit with 1
})

