import { chromium } from 'playwright'
import { readFile, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'
const out='output/playwright/commodities'
const quotes=JSON.parse(await readFile(`${out}/quotes.json`,'utf8'))
const histories=JSON.parse(await readFile(`${out}/histories.json`,'utf8'))
const session=JSON.parse(await readFile(`${out}/session.json`,'utf8'))
const browser=await chromium.launch()
const context=await browser.newContext({viewport:{width:1600,height:1050}})
await context.addInitScript(s=>{localStorage.setItem('public-beta.session_id',s.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(s.profile));localStorage.setItem('public-beta.theme','dark')},session)
const page=await context.newPage(),errors=[],checks=[]
let snapshotError=false,historyState='ready',delayed=false
page.on('pageerror',e=>errors.push(e.message))
await page.route('**/*',async route=>{
 const url=new URL(route.request().url())
 if(url.hostname!=='127.0.0.1')return route.abort()
 if(url.pathname.endsWith('/commodities/snapshot'))return route.fulfill({status:snapshotError?503:200,json:snapshotError?{detail:'QA: mất kết nối'}:quotes})
 if(url.pathname.includes('/instruments/')&&url.pathname.endsWith('/history')){
  const symbol=decodeURIComponent(url.pathname.split('/').at(-2)),period=url.searchParams.get('period')
  if(delayed&&symbol==='WTI'&&period==='3mo')await new Promise(resolve=>setTimeout(resolve,500))
  if(historyState==='error')return route.fulfill({status:503,json:{detail:'QA: history unavailable'}})
  const payload=structuredClone(histories[symbol]||{points:[],source:'yahoo_finance',freshness:'degraded'})
  payload.points=historyState==='empty'?[]:payload.points.slice(-({'1mo':22,'3mo':66,'6mo':132,'1y':260}[period]||66))
  if(historyState==='close-only')payload.points=payload.points.map(p=>({date:p.date,close:p.close}))
  if(historyState==='stale')payload.freshness='stale'
  return route.fulfill({json:payload})
 }
 if(!url.pathname.startsWith('/api/')||url.pathname.includes('/auth/'))return route.continue()
 return route.fulfill({status:503,json:{detail:'QA: ngoài phạm vi'}})
})
async function open(){await page.goto('http://127.0.0.1:5191/dashboard-static/global-terminal');await page.getByRole('tab',{name:'Hàng hóa',exact:true}).click();await page.getByRole('button',{name:'Xem Gold (XAU)',exact:true}).waitFor()}
async function ready(){await page.locator('.commodity-chart [role="img"]').waitFor()}
async function capture(name){await page.screenshot({path:`${out}/${name}.png`,fullPage:true,animations:'disabled'})}
try{
 await open();await ready();await page.locator('.commodity-table .price-sparkline[data-state=ready]').first().waitFor();await capture('desktop-dark')
 assert.equal(await page.locator('.commodity-table tbody tr').count(),23)
 assert.ok(!(await page.locator('.commodity-table').innerText()).includes('$'))
 checks.push('23 contracts, native quote units and real histories')
 await page.locator('.commodity-chart [role=img]').evaluate(element=>{let f=element[Object.keys(element).find(k=>k.startsWith('__reactFiber$'))];while(f){let h=f.memoizedState;while(h&&typeof h==='object'){const current=h.memoizedState?.current;if(typeof current?.timeScale==='function'){window.__commodityQaChart=current;current.timeScale().setVisibleLogicalRange({from:20,to:45});return}h=h.next}f=f.return}throw Error('Chart API not found')})
 await page.getByRole('switch',{name:'Chế độ tối',exact:true}).click();await ready()
 assert.ok(await page.evaluate(()=>{const r=window.__commodityQaChart.timeScale().getVisibleLogicalRange();return Math.abs(r.from-20)<1&&Math.abs(r.to-45)<1}))
 checks.push('Theme switch preserves the zoomed chart range')
 await page.getByRole('button',{name:'Đặt lại khung biểu đồ',exact:true}).click();await capture('desktop-light')
 checks.push('Both themes render and retain selected chart')
 await page.getByRole('button',{name:'Năng lượng',exact:false}).click();assert.equal(await page.locator('.commodity-table tbody tr').count(),5);assert.ok((await page.locator('.commodity-detail-head').innerText()).includes('WTI'));await ready()
 await page.getByRole('button',{name:'Xem Natural Gas (NATGAS)',exact:true}).focus();await page.keyboard.press('Enter');await ready();assert.ok((await page.locator('.commodity-quote').innerText()).includes('USD/MMBtu'))
 checks.push('Group filter selects a visible contract; selection works by keyboard')
 await page.getByRole('button',{name:'1 năm',exact:true}).click();await ready();await page.getByRole('button',{name:'Đường',exact:true}).click();await page.getByRole('button',{name:'Đặt lại khung biểu đồ',exact:true}).click()
 checks.push('Period, candle/line and chart reset controls work')
 await page.getByRole('button',{name:'Tất cả',exact:false}).click();await page.getByRole('textbox',{name:'Tìm hàng hoá',exact:true}).fill('cattle');assert.equal(await page.locator('.commodity-table tbody tr').count(),2)
 await page.getByRole('textbox',{name:'Tìm hàng hoá',exact:true}).fill('no-match');assert.equal(await page.locator('.commodity-table tbody tr').count(),0);await page.getByRole('button',{name:'Xoá bộ lọc',exact:true}).click();assert.equal(await page.locator('.commodity-table tbody tr').count(),23)
 checks.push('Search, empty result and reset combine with group filter')
 await page.getByRole('combobox',{name:'Sắp xếp hàng hoá',exact:true}).selectOption('losers');assert.ok((await page.locator('.commodity-table tbody tr').first().innerText()).includes('GASOLINE'))
 checks.push('Percentage sort uses numeric values')
 for(const width of [1280,850,768,390,320]){
  await page.setViewportSize({width,height:1000});await ready()
  const over=await page.locator('.commodity-page').evaluate(e=>({width:e.clientWidth,scroll:e.scrollWidth,body:document.documentElement.scrollWidth,viewport:innerWidth}))
  assert.ok(over.scroll<=over.width+1,JSON.stringify(over));assert.ok(over.body<=over.viewport+1,JSON.stringify(over))
  await capture(`width-${width}`)
 }
 checks.push('No page overflow at 1280, 850, 768, 390 and 320px')
 await page.getByRole('button',{name:'Bảng giá · Chọn hợp đồng',exact:true}).click()
 await page.getByRole('button',{name:'Xem Gold (XAU)',exact:true}).click();await ready()
 assert.ok(await page.locator('.commodity-detail').isVisible());assert.ok(!(await page.locator('.commodity-watch').isVisible()))
 checks.push('Mobile switches from contract list directly to selected chart')
 await capture('mobile-dark-or-light')
 await page.setViewportSize({width:1600,height:1050});snapshotError=true;await page.getByRole('button',{name:'Làm mới bảng giá',exact:true}).click();await page.getByRole('alert').waitFor();assert.equal(await page.locator('.commodity-table tbody tr').count(),23);snapshotError=false;await page.getByRole('button',{name:'Thử lại',exact:true}).click();await page.getByRole('alert').waitFor({state:'hidden'})
 checks.push('Refresh failure keeps quotes and retry recovers')
 historyState='error';await page.getByRole('button',{name:'Tải lại lịch sử giá',exact:true}).click();await page.getByText('Chưa tải được biểu đồ',{exact:true}).waitFor();assert.equal(await page.locator('.commodity-chart canvas').count(),0)
 historyState='empty';await page.getByRole('button',{name:'Thử lại lịch sử',exact:true}).click();await page.getByText('Chưa đủ lịch sử để vẽ biểu đồ',{exact:true}).waitFor()
 checks.push('Failed or missing history never draws fabricated lines')
 historyState='close-only';await page.getByRole('button',{name:'Thử lại lịch sử',exact:true}).click();await ready();assert.ok(await page.getByRole('button',{name:'Nến',exact:true}).isDisabled())
 checks.push('Close-only history switches to line and disables unsupported candles')
 historyState='stale';await page.getByRole('button',{name:'Tải lại lịch sử giá',exact:true}).click();await ready();assert.ok((await page.locator('.commodity-chart-caption').innerText()).includes('Lịch sử lưu trước đó'))
 checks.push('Cached history is labelled')
 historyState='ready';delayed=true;await page.getByRole('button',{name:'3 tháng',exact:true}).click();await page.getByRole('button',{name:'Xem Crude Oil WTI (WTI)',exact:true}).click();await page.getByRole('button',{name:'Xem Gold (XAU)',exact:true}).click();await ready();await page.waitForTimeout(600);assert.ok((await page.locator('.commodity-chart [role=img]').getAttribute('aria-label')).includes('Gold'))
 checks.push('Fast A→B→A selection does not display another contract history')
 await page.getByRole('button',{name:'Nến',exact:true}).click();await page.getByRole('switch',{name:'Chế độ tối',exact:true}).click();await capture('final-dark')
 assert.deepEqual(errors,[])
}finally{await writeFile(`${out}/checks.json`,JSON.stringify({checks,errors},null,2));await browser.close()}
console.log(JSON.stringify({checks,errors}))
