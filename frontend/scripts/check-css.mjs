import { readdir, readFile } from 'node:fs/promises'
import path from 'node:path'
import postcss from 'postcss'
async function files(dir) {return (await Promise.all((await readdir(dir,{withFileTypes:true})).map(e=>e.isDirectory()?files(path.join(dir,e.name)):path.join(dir,e.name)))).flat()}
const css=(await files('src')).filter(f=>f.endsWith('.css'))
let failed=0
for (const file of css) {
  try {postcss.parse(await readFile(file,'utf8'),{from:file})}
  catch(error) {failed++;console.error(error.message)}
}
console.log(`CSS syntax: ${css.length} files checked, ${failed} failed. No visual or accessibility certification.`)
process.exitCode=failed?1:0
