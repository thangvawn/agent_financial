import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir,readFile,writeFile} from 'node:fs/promises'
const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/book-reader-audit'
await mkdir(out,{recursive:true})
const pdf=await readFile('frontend/public/learning-assets/books/northstar-sample-reader.pdf')
const browser=await chromium.launch({headless:true})
const context=await browser.newContext({viewport:{width:1440,height:1000}})
const page=await context.newPage();page.setDefaultTimeout(10000)
const result={passes:[],failures:[],pageErrors:[]};let repair=false,active=0,maxActive=0,checks=0
page.on('pageerror',e=>result.pageErrors.push(e.message))
const books=[
 ['missing','QA missing book'],['restricted','QA restricted book'],['late404','QA vanished during download'],['wrong','QA HTML pretending to be PDF'],
 ...Array.from({length:10},(_,i)=>[`valid${i}`,`QA available book ${i}`]),
].map(([id,title])=>({book_id:id,title,author:'QA source audit',url:`https://archive.org/details/${id}`,summary:'Kiểm thử trạng thái nguồn sách',language:'en',topics:['investing']}))
books.push({...books[0],book_id:'duplicate',download_url:'https://archive.org/download/missing/missing.pdf'})
await context.route('**/*',async route=>{
 const u=new URL(route.request().url())
 if(u.hostname==='fonts.googleapis.com')return route.fulfill({contentType:'text/css',body:''})
 if(u.origin!==origin)return route.abort()
 if(u.pathname==='/api/v1/public/learning/catalog')return route.fulfill({json:{items:u.searchParams.get('kind')==='book'?books:[]}})
 if(u.pathname.endsWith('/reader/check')){
  active++;maxActive=Math.max(maxActive,active);checks++
  const id=new URL(u.searchParams.get('url')).pathname.split('/')[2]
  await new Promise(r=>setTimeout(r,60));active--
  const status=id==='missing'&&!repair?'missing':id==='restricted'?'restricted':['late404','wrong'].includes(id)||id.startsWith('valid')||id==='missing'?'ready':'unavailable'
  return route.fulfill({json:{status,kind:'pdf',message:status==='missing'?'Tài liệu không còn tại nguồn.':status==='restricted'?'Nguồn yêu cầu mượn sách.':'Đã kiểm tra nguồn.',view_url:`/api/v1/public/learning/reader/stream?url=${encodeURIComponent('https://archive.org/download/'+id+'/actual.pdf')}`,checked_at:new Date().toISOString()}})
 }
 if(u.pathname.endsWith('/reader/stream')){
  const id=new URL(u.searchParams.get('url')).pathname.split('/')[2]
  if(id==='late404')return route.fulfill({status:404,json:{detail:'Missing'}})
  if(id==='wrong')return route.fulfill({status:200,contentType:'text/html',body:'<html>Missing book</html>'})
  return route.fulfill({contentType:'application/pdf',body:pdf})
 }
 if(u.pathname.includes('/data-hub/')||u.pathname.includes('/news/'))return route.fulfill({json:{items:[],points:[],articles:[]}})
 return route.continue()
})
const response=await context.request.post(`${origin}/api/v1/public/auth/register`,{data:{name:'Book QA',email:`books.${Date.now()}@northstar.test`,password:'Only-Local-QA-2026'}})
assert.equal(response.status(),200);const account=await response.json()
await context.addInitScript(({account})=>{if(window!==window.top)return;localStorage.setItem('public-beta.session_id',account.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))},{account})
const search=page.getByLabel('Tìm sách và tài liệu')
async function open(title){await search.fill(title);await page.getByRole('button',{name:title,exact:true}).click();await page.getByRole('button',{name:'Xong',exact:true}).waitFor()}
async function close(){await page.getByRole('button',{name:'Xong',exact:true}).click()}
async function step(name,fn){try{await fn();result.passes.push(name);console.log('PASS',name)}catch(error){result.failures.push({name,error:error.message});console.log('FAIL',name,error.message);await page.screenshot({path:`${out}/failure-${name}.png`,fullPage:true});throw error}}
try{
 await page.goto(`${origin}/dashboard-static/learn`)
 await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click()
 await step('automatic-check-deduplicate-paginate',async()=>{
  await page.getByRole('heading',{name:'QA missing book',exact:true}).waitFor()
  await page.locator('[data-book-id="missing"] .book-source-badge--missing').waitFor()
  assert.equal(await page.locator('[data-book-id="duplicate"]').count(),0)
  assert.equal(await page.locator('.lh-book-card').count(),12)
  assert.ok(maxActive<=3,`Concurrent checks: ${maxActive}`)
  await page.getByRole('button',{name:'Trang sau',exact:true}).click()
  await page.getByText('Trang 2/2',{exact:true}).waitFor()
  await page.getByRole('button',{name:'Trang trước',exact:true}).click()
 })
 await step('full-audit-and-source-filters',async()=>{
  await page.getByRole('button',{name:'Kiểm tra lại toàn bộ sách',exact:true}).click()
  await page.getByRole('button',{name:/Dừng kiểm tra/}).waitFor({state:'detached',timeout:15000})
  await page.getByLabel('Lọc trạng thái nguồn sách').selectOption('missing')
  assert.equal(await page.locator('.lh-book-card').count(),1)
  await page.getByRole('heading',{name:'QA missing book',exact:true}).waitFor()
  await page.getByLabel('Lọc trạng thái nguồn sách').selectOption('ready')
  await page.locator('.lh-book-card').first().waitFor()
  assert.equal(await page.locator('.lh-book-card .book-source-badge:not(.book-source-badge--ready)').count(),0)
  await page.getByLabel('Lọc trạng thái nguồn sách').selectOption('all')
  await page.screenshot({path:`${out}/library-desktop.png`,fullPage:true})
 })
 await step('missing-book-notes-persist-retry-recovers',async()=>{
  await open('QA missing book')
  await page.getByRole('heading',{name:'Không còn tại nguồn',exact:true}).waitFor()
  assert.equal(await page.locator('.br-doc__frame').count(),0)
  const note=page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first()
  await note.fill('Ghi chú vẫn được giữ khi nguồn đã mất')
  await page.getByRole('button',{name:'Lưu',exact:true}).click()
  await close();await open('QA missing book')
  assert.equal(await note.inputValue(),'Ghi chú vẫn được giữ khi nguồn đã mất')
  repair=true;await page.getByRole('button',{name:'Kiểm tra lại nguồn',exact:true}).click()
  await page.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()
  await close()
 })
 await step('restricted-book-has-honest-state',async()=>{
  await open('QA restricted book')
  await page.getByRole('heading',{name:'Hạn chế truy cập',exact:true}).waitFor()
  assert.equal(await page.locator('.br-doc__frame').count(),0)
  await page.getByRole('button',{name:'Xem tóm lược',exact:true}).click()
  await page.locator('.br-study').waitFor();await close()
 })
 for(const title of ['QA vanished during download','QA HTML pretending to be PDF'])await step(title.includes('vanished')?'download-404':'false-pdf-body',async()=>{
  await open(title);await page.getByRole('heading',{name:'Chưa mở được tài liệu',exact:true}).waitFor()
  assert.equal(await page.locator('.br-doc__frame').count(),0)
  assert.equal(await page.locator('.br-source-strip .book-source-badge--ready').count(),0,'Failed download must not retain a green readable badge')
  await page.getByRole('button',{name:'Xem tóm lược',exact:true}).click();await page.locator('.br-study').waitFor();await close()
 })
 await step('local-pdf-is-validated-before-iframe',async()=>{
  await open('Northstar Sample Reader')
  await page.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()
  const content=await page.locator('iframe.br-doc__frame').evaluate(async frame=>(await (await fetch(frame.src)).text()).slice(0,5))
  assert.equal(content,'%PDF-');await close()
 })
 await step('html-notes-are-sandboxed-and-labelled',async()=>{
  await search.fill('');await page.locator('[data-book-id="b-common-sense-investing"] h3 button').click()
  await page.getByRole('button',{name:'Bài đọc tóm lược',exact:true}).waitFor()
  const frame=page.locator('iframe.br-doc__frame--html');await frame.waitFor()
  assert.equal(await frame.getAttribute('sandbox'),'')
  await page.getByText('Bài ghi chú học tập, không phải toàn bộ cuốn sách.',{exact:true}).waitFor()
  await page.screenshot({path:`${out}/reader-html-desktop.png`,fullPage:true});await close()
 })
 await step('mobile-library-and-error-reader-fit',async()=>{
  await search.fill('');await page.setViewportSize({width:390,height:844})
  await page.screenshot({path:`${out}/library-mobile.png`,fullPage:true})
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
  await open('QA restricted book')
  await page.getByRole('heading',{name:'Hạn chế truy cập',exact:true}).waitFor()
  await page.screenshot({path:`${out}/reader-mobile.png`,fullPage:true})
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
 })
 assert.deepEqual(result.pageErrors,[])
}finally{
 result.requests={checks,maxActive};await writeFile(`${out}/browser-evidence.json`,JSON.stringify(result,null,2));await browser.close()
}
console.log(JSON.stringify(result,null,2));process.exitCode=result.failures.length?1:0
