import { transformWithOxc } from 'vite'
import fs from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

export async function load(url, context, nextLoad) {
  if (url.endsWith('.jsx')) {
    const filePath = fileURLToPath(url)
    const source = await fs.readFile(filePath, 'utf8')
    const result = await transformWithOxc(source, filePath)
    return {
      format: 'module',
      shortCircuit: true,
      source: result.code,
    }
  }
  return nextLoad(url, context)
}

