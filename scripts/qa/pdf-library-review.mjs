import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir,readFile,writeFile} from 'node:fs/promises'
import {createHash} from 'node:crypto'
const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/pdf-library'
await mkdir(out,{recursive:true})
const sources=JSON.parse(await readFile('frontend/public/learning-assets/books/openstax-pdf-sources.json','utf8'))
const browser=await chromium.launch({headless:true,channel:'chromium'})
const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true})
const page=await context.newPage();page.setDefaultTimeout(15000)
const result={passes:[],failures:[],pageErrors:[],downloads:[]}
page.on('pageerror',error=>result.pageErrors.push(error.message))
await context.route('**/api/v1/public/learning/catalog?**',route=>route.fulfill({json:{items:[]}}))
await context.route('**/api/v1/public/learning/reader/check?**',route=>route.fulfill({json:{status:'restricted',message:'QA: nguồn bên ngoài cần quyền truy cập.'}}))
await context.route('**/fonts.googleapis.com/**',route=>route.fulfill({contentType:'text/css',body:''}))
const registered=await context.request.post(origin+'/api/v1/public/auth/register',{data:{name:'PDF library QA',email:`pdf-library.${Date.now()}@northstar.test`,password:'Local-QA-only-2026'}})
assert.equal(registered.status(),200)
const account=await registered.json()
await context.addInitScript(account=>{if(window!==window.top)return;localStorage.setItem('public-beta.session_id',account.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))},account)
async function step(name,fn){
 try{await fn();result.passes.push(name);console.log('PASS',name)}
 catch(error){result.failures.push({name,error:error.message});await page.screenshot({path:`${out}/failed-${name}.png`,fullPage:true});throw error}
}
async function close(){await page.getByRole('button',{name:'Xong',exact:true}).click();await page.getByLabel('Loại bản đọc').waitFor()}
try{
 await page.goto(origin+'/dashboard-static/learn')
 await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click()
 await step('default-is-full-pdf-without-notes-or-sample',async()=>{
  await page.locator('[data-book-id="openstax-principles-finance-2e"]').waitFor()
  assert.equal(await page.getByLabel('Loại bản đọc').inputValue(),'pdf')
  assert.equal(await page.locator('.lh-book-card').count(),4)
  assert.equal(await page.locator('[data-book-id="b-local-sample"],[data-book-id="b-common-sense-investing"],[data-book-id="b-psychology-of-money"]').count(),0)
  await page.locator('[data-book-id="openstax-principles-finance-2e"]').getByRole('button',{name:'Đọc PDF',exact:true}).waitFor()
  await page.screenshot({path:`${out}/library-pdf-desktop.png`,fullPage:true})
 })
 await step('download-is-exact-full-publisher-pdf',async()=>{
  const card=page.locator('[data-book-id="openstax-principles-finance-2e"]')
  const [download]=await Promise.all([page.waitForEvent('download'),card.getByRole('link',{name:'Tải PDF',exact:true}).click()])
  const path=await download.path(),bytes=await readFile(path)
  const expected=sources.find(source=>source.filename===download.suggestedFilename())
  assert.ok(expected);assert.equal(bytes.length,expected.size)
  assert.equal(createHash('sha256').update(bytes).digest('hex'),expected.sha256)
  result.downloads.push({filename:download.suggestedFilename(),bytes:bytes.length,sha256:expected.sha256})
 })
 for(const source of sources)await step('read-'+source.filename,async()=>{
  const card=page.locator(`[data-book-id="${source.filename.replace('.pdf','')}"]`)
  await card.getByRole('button',{name:'Đọc PDF',exact:true}).click()
  await page.getByRole('button',{name:'PDF toàn văn',exact:true}).waitFor()
  const frame=page.locator('iframe.br-doc__frame[src^="blob:"]');await frame.waitFor({timeout:30000})
  const digest=await frame.evaluate(async element=>{
   const bytes=await (await fetch(element.src)).arrayBuffer()
   return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(n=>n.toString(16).padStart(2,'0')).join('')
  })
  assert.equal(digest,source.sha256)
  assert.equal(await page.locator('.br-study').count(),0)
  if(source.filename.includes('finance-2e')){
   await page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first().fill('Ghi chú của tôi bên cạnh PDF toàn văn')
   await page.getByRole('button',{name:'Lưu',exact:true}).click()
   await page.waitForTimeout(3000)
   await page.screenshot({path:`${out}/full-pdf-reader-desktop.png`,fullPage:true})
  }
  await close()
 })
 await step('notes-only-appear-in-separate-filter',async()=>{
  await page.getByLabel('Loại bản đọc').selectOption('notes')
  await page.locator('[data-book-id="b-common-sense-investing"]').waitFor()
  assert.equal(await page.locator('.lh-book-card').count(),3)
  assert.equal(await page.locator('[data-book-id^="openstax-"]').count(),0)
  await page.getByLabel('Loại bản đọc').selectOption('all')
  assert.equal(await page.locator('.lh-book-card').count(),11)
  await page.getByLabel('Loại bản đọc').selectOption('pdf')
 })
 await step('reader-notes-persist-with-original-pdf',async()=>{
  await page.locator('[data-book-id="openstax-principles-finance-2e"]').getByRole('button',{name:'Đọc PDF',exact:true}).click()
  assert.equal(await page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first().inputValue(),'Ghi chú của tôi bên cạnh PDF toàn văn')
  await close()
 })
 await step('mobile-pdf-library-has-no-overflow',async()=>{
  await page.setViewportSize({width:390,height:844})
  assert.equal(await page.getByLabel('Loại bản đọc').inputValue(),'pdf')
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
  await page.screenshot({path:`${out}/library-pdf-mobile.png`,fullPage:true})
 })
 assert.deepEqual(result.pageErrors,[])
}finally{
 await writeFile(`${out}/browser-evidence.json`,JSON.stringify(result,null,2));await browser.close()
}
console.log(JSON.stringify(result,null,2));process.exitCode=result.failures.length?1:0
