import { chromium } from 'playwright'
import assert from 'node:assert/strict'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out=`output/playwright/review-2026-10-31/${process.env.REVIEW_BLOCK_FONTS?'font-offline':process.env.REVIEW_STEPS?'focused':'functional'}`
await mkdir(out,{recursive:true})
const snapshot=JSON.parse(await readFile('data/vn_market/snapshot.json','utf8'))
const browser=await chromium.launch({headless:true})
const context=await browser.newContext({viewport:{width:1440,height:1000}})
const page=await context.newPage()
page.setDefaultTimeout(10000)
const evidence={passes:[],findings:[],pageErrors:[],requests:[],abortedRequests:[]}
page.on('pageerror',e=>evidence.pageErrors.push(e.message))
page.on('requestfailed',r=>{if(r.url().startsWith(origin))evidence.abortedRequests.push({request:new URL(r.url()).pathname,error:r.failure()?.errorText})})
let modelOffline=false
await context.route('**/*',async route=>{
  const u=new URL(route.request().url())
  if(u.hostname==='fonts.googleapis.com') return process.env.REVIEW_BLOCK_FONTS?route.abort():route.fulfill({contentType:'text/css',body:''})
  if(u.origin!==origin) return route.abort()
  if(u.pathname.includes('/instruments/')&&u.pathname.endsWith('/history')) {
    const hourly=u.searchParams.get('interval')==='1h'
    const points=Array.from({length:180},(_,i)=>{
      const close=10000+Math.sin(i/9)*2000
      return {date:new Date(Date.UTC(2025,0,1)+(hourly?3600000:86400000)*i).toISOString(),open:close,close,high:close+100,low:close-100,volume:200000}
    })
    return route.fulfill({json:{points,source:'fixture'}})
  }
  if(u.pathname.includes('/data-hub/')||u.pathname.includes('/market-data/')) {
    if(u.pathname.endsWith('/snapshot')&&u.pathname.includes('vn-market')) return route.fulfill({json:snapshot})
    return route.fulfill({json:{items:[],indices:[],groups:[],data:[],source:'fixture'}})
  }
  if(u.pathname.startsWith('/financials/')) {
    if(u.pathname.endsWith('/model')) return modelOffline?route.fulfill({status:503,json:{detail:'QA offline'}}):route.continue()
    if(u.pathname.endsWith('/company-workspace')) return route.fulfill({json:{company:{name:'FPT',latest_period:'2025'},statements:{income:{periods:['2025'],rows:[]},balance:{periods:['2025'],rows:[]},cash_flow:{periods:['2025'],rows:[]}},ratio_groups:[],trend:{periods:[],series:[]}}})
    return route.fulfill({json:{}})
  }
  return route.continue()
})
page.on('response',r=>{const u=new URL(r.url()); if(u.pathname.startsWith('/api')||u.pathname.startsWith('/financials'))evidence.requests.push({path:u.pathname,method:r.request().method(),status:r.status()})})
async function step(name,fn){if(process.env.REVIEW_STEPS&&!process.env.REVIEW_STEPS.split(',').includes(name))return;try{await fn();evidence.passes.push(name);console.log('PASS',name)}catch(e){evidence.findings.push({step:name,error:e.message});console.log('OBSERVED',name,e.message);await page.screenshot({path:`${out}/${name.replaceAll(/[^a-z0-9]/gi,'-')}.png`,fullPage:true})}}
async function register(suffix){
 await page.goto(`${origin}/dashboard-static/register`)
 await page.locator('#auth-name').fill(`QA ${suffix}`)
 await page.locator('#auth-email').fill(`usage.${Date.now()}.${suffix}@northstar.test`)
 await page.locator('#auth-password').fill('Only-Local-QA-2026')
 await page.locator('#auth-confirm-password').fill('Only-Local-QA-2026')
 await page.locator('#auth-terms').check()
 await page.getByRole('button',{name:'Tạo tài khoản',exact:true}).click()
 await page.getByRole('tab',{name:'Cổ phiếu',exact:true}).waitFor()
}
try {
 await step('registration-real-backend',async()=>{await register('A')})
 await step('watchlist-add-remove-real-backend',async()=>{
   await page.getByRole('tab',{name:'Watchlist',exact:true}).click()
   await page.getByLabel('Thêm mã cổ phiếu').fill('FPT')
   await page.getByRole('button',{name:'+ Thêm mã',exact:true}).click()
   await page.getByRole('button',{name:'Bỏ theo dõi'}).first().waitFor()
   await page.getByRole('button',{name:'Bỏ theo dõi'}).first().click()
   await page.getByText('Watchlist đang trống',{exact:true}).waitFor()
 })
 await step('paper-trade-and-portfolio-real-backend',async()=>{
   await page.getByRole('tab',{name:'Lệnh giấy',exact:true}).click()
   await page.getByRole('button',{name:'Đặt lệnh giấy',exact:true}).click()
   await page.getByRole('status').filter({hasText:'FILLED'}).waitFor()
   await page.getByRole('tab',{name:'Danh mục',exact:true}).click()
   await page.getByRole('cell',{name:'FPT',exact:true}).waitFor()
   const row=page.getByRole('row').filter({has:page.getByRole('cell',{name:'FPT',exact:true})})
   assert.ok((await row.innerText()).includes('100'))
 })
 await step('workbook-server-save-reload',async()=>{
   await page.goto(`${origin}/dashboard-static/bctc`)
   await page.getByRole('tab',{name:'Notes',exact:true}).click()
   await page.getByRole('button',{name:'Lưu',exact:true}).waitFor()
   await page.getByLabel('Ghi chú BCTC',{exact:true}).fill('server version A')
   await page.getByRole('button',{name:'Lưu',exact:true}).click()
   await page.getByRole('status').filter({hasText:'Mô hình đã lưu'}).waitFor()
   await page.reload()
   await page.getByLabel('Ghi chú BCTC',{exact:true}).waitFor()
   assert.equal(await page.getByLabel('Ghi chú BCTC',{exact:true}).inputValue(),'server version A')
 })
 await step('workbook-offline-draft-online-recovery',async()=>{
   modelOffline=true
   await page.getByLabel('Ghi chú BCTC',{exact:true}).fill('offline newer version B')
   await page.getByRole('button',{name:'Lưu',exact:true}).click()
   await page.getByRole('status').filter({hasText:'bản nháp'}).waitFor()
   modelOffline=false
   await page.reload()
   await page.getByLabel('Ghi chú BCTC',{exact:true}).waitFor()
   const actual=await page.getByLabel('Ghi chú BCTC',{exact:true}).inputValue()
   evidence.draftReloadActual=actual
   assert.equal(actual,'offline newer version B','Online reload must surface newer offline draft or a recovery choice')
 })
 await step('simulation-default',async()=>{
   await page.goto(`${origin}/dashboard-static/simulation-lab`)
   await page.locator('.tearsheet-grid').waitFor()
 })
 await step('simulation-ai-copilot-open',async()=>{
   await page.getByRole('button',{name:'AI Copilot',exact:false}).click()
   await page.getByRole('heading',{name:'AI Quant Copilot & Chiến Lược Cố Vấn'}).waitFor({timeout:2500})
 })
 await step('blueprint-save-owner-A',async()=>{
   await page.getByRole('button',{name:'Bản Lưu',exact:false}).click()
   await page.getByPlaceholder('Tên chiến lược cần lưu...').fill('QA private strategy A')
   await page.getByRole('button',{name:'Lưu Bản Hiện Tại',exact:true}).click()
   await page.getByText('QA private strategy A',{exact:true}).waitFor()
   await page.getByRole('button',{name:'✕',exact:true}).click()
 })
 await step('logout-and-register-owner-B',async()=>{
   await page.getByRole('button',{name:'Đăng xuất',exact:true}).click()
   await page.getByRole('button',{name:'Đăng nhập',exact:true}).first().waitFor()
   await register('B')
 })
 await step('blueprint-account-isolation',async()=>{
   await page.goto(`${origin}/dashboard-static/simulation-lab`)
   await page.locator('.tearsheet-grid').waitFor()
   await page.getByRole('button',{name:'Bản Lưu',exact:false}).click()
   await page.getByPlaceholder('Tên chiến lược cần lưu...').waitFor()
   assert.equal(await page.getByText('QA private strategy A',{exact:true}).count(),0,'Owner B must not see saved personal strategy of owner A')
 })
 await page.goto(`${origin}/dashboard-static/learn`)
 await page.locator('.lhc-grid').waitFor()
 evidence.learningSnapshot=(await page.locator('body').innerText()).slice(0,4500)
 await page.screenshot({path:`${out}/learning.png`,fullPage:true})
 // Revoke the actual test session through backend while keeping the browser open.
 await step('revoked-session-reroute',async()=>{
   const token=await page.evaluate(()=>localStorage.getItem('public-beta.session_id'))
   const r=await context.request.post(`${origin}/api/v1/public/auth/logout`,{headers:{Authorization:`Bearer ${token}`}})
   assert.equal(r.status(),200)
   await page.goto(`${origin}/dashboard-static/global-terminal`)
   await page.getByRole('tab',{name:'Lệnh giấy',exact:true}).click()
   await page.getByRole('alert').waitFor()
   evidence.revokedSessionMessage=await page.getByRole('alert').innerText()
   assert.ok(page.url().endsWith('/login'),'Revoked session remains in protected UI instead of login/re-auth')
 })
} finally {await writeFile(`${out}/browser-evidence.json`,JSON.stringify(evidence,null,2));await browser.close()}
console.log(JSON.stringify({passes:evidence.passes,findings:evidence.findings,pageErrors:evidence.pageErrors},null,2))

process.exitCode=evidence.findings.some(item=>item.step)?1:0
