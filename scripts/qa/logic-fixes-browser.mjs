import { chromium } from 'playwright'
import assert from 'node:assert/strict'
const origin=process.env.REVIEW_PREVIEW_URL || 'http://127.0.0.1:5185'
const browser=await chromium.launch({headless:true})
const context=await browser.newContext({viewport:{width:1440,height:1000}})
const page=await context.newPage()
const errors=[];page.on('pageerror',e=>errors.push(e.message))
let saved=null,logoutHeader=null,logoutFails=true,modelOffline=false
await context.addInitScript(()=>{
  if(!sessionStorage.getItem('fixture-started')) {
    localStorage.setItem('public-beta.session_id','review-session')
    localStorage.setItem('northstar:bctc:model:FPT',JSON.stringify({owner:'other-owner',notes:'must never appear'}))
    sessionStorage.setItem('fixture-started','1')
  }
})
const model={revision:2,active_tab:'notes',notes:'FPT saved notes',formula:'=NET_INCOME / REVENUE',assumptions:{revenueGrowthPct:5}}
await page.route('**/api/**',async route=>{
  const url=new URL(route.request().url())
  if(url.pathname.endsWith('/auth/logout')) {
    logoutHeader=route.request().headers().authorization
    return route.fulfill({status:logoutFails?503:200,json:{status:'ok'}})
  }
  if(url.pathname.includes('/instruments/')&&url.pathname.endsWith('/history')) {
    const hourly=url.searchParams.get('interval')==='1h'
    const count=url.pathname.includes('/HPG/')?20:180
    const points=Array.from({length:count},(_,i)=>{
      const close=10000+Math.sin(i/9)*2000
      return {date:new Date(Date.UTC(2025,0,1)+(hourly?3600000:86400000)*i).toISOString(),open:close,close,high:close+100,low:close-100,volume:200000}
    })
    return route.fulfill({json:{points,source:'fixture'}})
  }
  return route.fulfill({json:{items:[],articles:[]}})
})
await page.route('**/financials/**',async route=>{
  const url=new URL(route.request().url()),ticker=url.pathname.split('/')[2]
  if(url.pathname.endsWith('/model')) {
    if(route.request().method()==='POST') {saved=route.request().postDataJSON();return route.fulfill({json:{model:{...saved,revision:1}}})}
    if(modelOffline) return route.fulfill({status:503,json:{detail:'offline'}})
    if(ticker==='FPT') return route.fulfill({json:{model}})
    return route.fulfill({status:404,json:{detail:'not saved'}})
  }
  if(url.pathname.endsWith('/company-workspace')) return route.fulfill({json:{company:{name:ticker,latest_period:'2025'},statements:{income:{periods:['2025'],rows:[]},balance:{periods:['2025'],rows:[]},cash_flow:{periods:['2025'],rows:[]}},ratio_groups:[],trend:{periods:[],series:[]}}})
  return route.fulfill({json:{}})
})
try {
  await page.goto(`${origin}/dashboard-static/simulation-lab`)
  await page.getByText('180 nến thật',{exact:true}).waitFor()
  await page.locator('.tearsheet-grid').waitFor()
  assert.equal(await page.getByRole('alert').count(),0)
  const editor=page.getByPlaceholder('Viết mã Quanta DSL tại đây...')
  await editor.fill('strategy "invalid"\ndetect:\n  x = unsupported(market.close)\nact:\n  when x:\n    enter long with wnav 5pct\n  when position.is_long:\n    close long')
  await page.getByRole('alert').filter({hasText:'hỗ trợ'}).waitFor()
  await page.locator('.simlab-preset-select').selectOption('turtle-breakout')
  await page.locator('.tearsheet-grid').waitFor()
  await Promise.all([page.waitForResponse(r=>r.url().includes('interval=1h')),page.getByLabel('Khung nến').selectOption('1h')])
  await page.locator('.tearsheet-grid').waitFor()
  assert.equal(await page.getByRole('alert').count(),0)
  console.log('PASS simulation: executable presets, invalid DSL, hourly chart')
  await page.getByLabel('Mã CK').selectOption('HPG')
  await page.getByRole('alert').filter({hasText:'nến lịch sử'}).waitFor()
  assert.equal(await page.locator('.tearsheet-grid').count(),0)
  console.log('PASS short-history: error replaces results without synthetic fallback')
  await page.goto(`${origin}/dashboard-static/bctc`)
  await page.getByLabel('Ghi chú BCTC',{exact:true}).waitFor()
  assert.equal(await page.getByLabel('Ghi chú BCTC',{exact:true}).inputValue(),'FPT saved notes')
  await page.getByLabel('Mã doanh nghiệp',{exact:true}).fill('VCB')
  await page.getByRole('button',{name:'Tra cứu',exact:true}).click()
  await page.getByRole('tab',{name:'Notes',exact:true}).click()
  assert.equal(await page.getByLabel('Ghi chú BCTC',{exact:true}).inputValue(),'')
  await page.getByLabel('Ghi chú BCTC',{exact:true}).fill('VCB fresh notes')
  await page.getByRole('button',{name:'Lưu',exact:true}).click()
  await page.getByRole('status').filter({hasText:'Mô hình đã lưu'}).waitFor()
  assert.equal(saved.expected_revision,0)
  assert.equal(saved.notes,'VCB fresh notes')
  console.log('PASS workbook: ticker reset, revision zero, server save')
  modelOffline=true
  await page.evaluate(()=>localStorage.setItem('public-beta.session_id','review-session-b'))
  await page.goto(`${origin}/dashboard-static/bctc`)
  await page.getByRole('button',{name:'Lưu',exact:true}).waitFor()
  await page.getByRole('tab',{name:'Notes',exact:true}).click()
  assert.equal(await page.getByLabel('Ghi chú BCTC',{exact:true}).inputValue(),'')
  assert.ok(!(await page.locator('body').innerText()).includes('must never appear'))
  console.log('PASS workbook: second account cannot see old offline notes')
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click()
  await page.getByRole('alert').filter({hasText:'thu hồi'}).waitFor()
  assert.equal(await page.evaluate(()=>localStorage.getItem('public-beta.session_id')),'review-session-b')
  logoutFails=false
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click()
  await page.getByRole('button',{name:'Đăng nhập',exact:true}).first().waitFor()
  assert.equal(logoutHeader,'Bearer review-session-b')
  assert.equal(await page.evaluate(()=>localStorage.getItem('public-beta.session_id')),null)
  console.log('PASS logout: failed revocation can retry; successful revocation clears session')
  assert.deepEqual(errors,[])
  await page.screenshot({path:'/tmp/ns-fixes-browser.png',fullPage:true})
  console.log('PASS no uncaught browser errors')
} catch (error) { console.error('BROWSER ERRORS', errors); console.error((await page.locator('body').innerText()).slice(0,7000)); await page.screenshot({path:'/tmp/ns-fixes-browser-failure.png',fullPage:true}); throw error } finally {await browser.close()}
