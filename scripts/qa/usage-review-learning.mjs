import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/review-2026-10-31/learning'
await mkdir(out,{recursive:true})
const browser=await chromium.launch({headless:true})
const context=await browser.newContext({viewport:{width:1440,height:1000}})
const page=await context.newPage();page.setDefaultTimeout(8000)
const result={passes:[],findings:[],pageErrors:[]}
page.on('pageerror',e=>result.pageErrors.push(e.message))
let newsFails=false
const article={article_id:'qa-news',headline:'QA: Tin kiểm thử giao diện',source:'QA fixture',published_at:'2026-10-31T01:00:00Z',summary:'Nội dung kiểm thử',category:'markets',region:'VN'}
await context.route('**/*',async route=>{
 const u=new URL(route.request().url())
 if(u.hostname==='fonts.googleapis.com')return route.fulfill({contentType:'text/css',body:''})
 if(u.origin!==origin)return route.abort()
 if(u.pathname.startsWith('/api/v1/public/news/')){
  if(newsFails)return route.fulfill({status:503,json:{detail:'QA unavailable'}})
  if(u.pathname.includes('/articles/'))return route.fulfill({json:{article,...article}})
  return route.fulfill({json:{articles:u.searchParams.get('q')?[]:[article],items:[],source:'fixture'}})
 }
 if(u.pathname.includes('/data-hub/'))return route.fulfill({json:{items:[],points:[]}})
 return route.continue()
})
async function register(name){const r=await context.request.post(`${origin}/api/v1/public/auth/register`,{data:{name,email:`qa.${Date.now()}.${name}@northstar.test`,password:'Only-Local-QA-2026'}});assert.equal(r.status(),200);return r.json()}
const a=await register('LearningA')
await context.addInitScript(({a})=>{if(!sessionStorage.getItem('qa-init')){localStorage.setItem('public-beta.session_id',a.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(a.profile));sessionStorage.setItem('qa-init','1')}},{a})
async function step(name,fn){try{await fn();result.passes.push(name);console.log('PASS',name)}catch(e){result.findings.push({step:name,error:e.message});console.log('OBSERVED',name,e.message);await page.screenshot({path:`${out}/${name}.png`,fullPage:true})}}
async function sample(){await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click();await page.getByRole('heading',{name:'Northstar Sample Reader',exact:true}).click();await page.getByRole('button',{name:'Xong',exact:true}).waitFor()}
try{
 await page.goto(`${origin}/dashboard-static/learn`)
 await step('course-filter-bookmark',async()=>{
  await page.locator('.lhc-grid').waitFor()
  await page.getByLabel('Tìm khóa học, chủ đề, giảng viên').fill('qa-no-such-course-2026')
  await page.getByText('Không tìm thấy khóa học nào phù hợp với bộ lọc hiện tại.',{exact:true}).waitFor()
  await page.getByRole('button',{name:'Xóa bộ lọc',exact:true}).click()
  await page.getByRole('button',{name:'Lưu khóa học',exact:true}).first().click()
  assert.equal(await page.getByRole('button',{name:'Bỏ lưu khóa học',exact:true}).count(),1)
 })
 await step('book-pdf-notes-save-reopen',async()=>{
  await sample()
  const pdf=await context.request.get(`${origin}/learning-assets/books/northstar-sample-reader.pdf`)
  assert.equal(pdf.status(),200);assert.ok(pdf.headers()['content-type'].includes('pdf'))
  await page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first().fill('QA personal reading note')
  await page.getByRole('button',{name:'Lưu',exact:true}).click()
  await page.getByRole('button',{name:'Xong',exact:true}).click()
  await page.getByRole('heading',{name:'Northstar Sample Reader',exact:true}).click()
  assert.equal(await page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first().inputValue(),'QA personal reading note')
  await page.getByRole('button',{name:'Xong',exact:true}).click()
 })
 await step('mock-exam-resume-same-account',async()=>{
  await page.goto(`${origin}/dashboard-static/learn`)
  await page.getByRole('tab',{name:'CFA Mock',exact:true}).click()
  await page.getByRole('button',{name:'Bắt đầu phòng thi',exact:false}).click()
  await page.getByRole('radio').first().click()
  await page.goto(`${origin}/dashboard-static/learn`)
  await page.getByRole('tab',{name:'CFA Mock',exact:true}).click()
  await page.getByRole('radio').first().waitFor()
  assert.equal(await page.getByRole('radio').first().getAttribute('aria-checked'),'true')
 })
 await page.getByRole('button',{name:'Đăng xuất',exact:true}).click()
 await page.getByRole('button',{name:'Đăng nhập',exact:true}).first().waitFor()
 const b=await register('LearningB')
 await page.evaluate(({b})=>{localStorage.setItem('public-beta.session_id',b.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(b.profile))},{b})
 await page.goto(`${origin}/dashboard-static/learn`)
 await step('learning-bookmark-account-isolation',async()=>{
  await page.locator('.lhc-grid').waitFor()
  assert.equal(await page.getByRole('button',{name:'Bỏ lưu khóa học',exact:true}).count(),0,'Account B inherits bookmark from account A')
 })
 await step('mock-exam-account-isolation',async()=>{
  await page.getByRole('tab',{name:'CFA Mock',exact:true}).click()
  await page.locator('.mock-room').waitFor()
  result.examBText=(await page.locator('body').innerText()).slice(0,1800)
  assert.equal(await page.getByRole('radio').count(),0,'Account B resumes account A unfinished exam and its selected answer')
 })
 await step('news-select-search-empty',async()=>{
  await page.goto(`${origin}/dashboard-static/news`)
  await page.locator('.news-feed__item').first().click()
  await page.locator('.news-reader').getByText(article.headline,{exact:true}).waitFor()
  await page.locator('.news-filters__search input').fill('qa-empty')
  await page.getByText('Không tìm thấy tin tức phù hợp với bộ lọc hiện tại.',{exact:true}).waitFor()
 })
 await step('news-provider-error',async()=>{
  newsFails=true
  await page.reload()
  await page.getByText('Không thể cập nhật tin tức. Vui lòng thử lại sau.',{exact:true}).waitFor()
 })
 await step('mobile-learning-smoke',async()=>{
  await page.setViewportSize({width:390,height:844})
  await page.goto(`${origin}/dashboard-static/learn`)
  await page.locator('.lhc-grid').waitFor()
  result.mobileWidth=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}))
  await page.screenshot({path:`${out}/mobile-learning.png`,fullPage:true})
  assert.ok(result.mobileWidth.document<=result.mobileWidth.viewport+1,'Learning view has horizontal overflow')
 })
}finally{await writeFile(`${out}/evidence.json`,JSON.stringify(result,null,2));await browser.close()}
console.log(JSON.stringify(result,null,2))

process.exitCode=result.findings.length?1:0
