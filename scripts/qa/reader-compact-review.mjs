import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'
const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/reader-compact'
await mkdir(out,{recursive:true})
const browser=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-swiftshader']})
const context=await browser.newContext({viewport:{width:1600,height:1000},reducedMotion:'reduce'})
const page=await context.newPage();page.setDefaultTimeout(15000)
const evidence={passes:[],failures:[],pageErrors:[],geometry:{}}
page.on('pageerror',e=>evidence.pageErrors.push(e.message))
for(const [url,json] of [['**/api/v1/public/learning/catalog?**',{items:[]}],['**/api/v1/public/learning/reader/check?**',{status:'restricted',message:'QA external source'}]])await context.route(url,r=>r.fulfill({json}))
await context.route('**/fonts.googleapis.com/**',r=>r.fulfill({contentType:'text/css',body:''}))
const response=await context.request.post(origin+'/api/v1/public/auth/register',{data:{name:'Compact reader QA',email:`compact.${Date.now()}@northstar.test`,password:'Compact-reader-QA-2026'}})
assert.equal(response.status(),200)
const account=await response.json()
await context.addInitScript(account=>{if(window!==top)return;localStorage.setItem('public-beta.session_id',account.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))},account)
async function measure(){return page.evaluate(()=>{
  const rect=selector=>{const r=document.querySelector(selector).getBoundingClientRect();return {top:r.top,height:r.height,width:r.width}}
  return {header:rect('.br-top'),bar:rect('.br-workspace-bar'),paper:rect('[data-note-paper]'),document:rect('.br-doc__frame'),notes:rect('.br-notes__scroll')}
})}
async function step(name,fn){try{await fn();evidence.passes.push(name);console.log('PASS',name)}catch(e){evidence.failures.push({name,error:e.message});await page.screenshot({path:`${out}/failed-${name}.png`});throw e}}
const input=()=>page.locator('textarea.br-paper__text').first()
try{
  await page.goto(origin+'/dashboard-static/learn');await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click()
  await page.locator('[data-book-id="openstax-principles-finance-2e"]').getByRole('button',{name:'Đọc PDF',exact:true}).click()
  await page.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()
  await page.waitForFunction(()=>document.querySelector('[aria-label="Trạng thái đọc trong kệ"]')?.value==='reading')
  await step('desktop-chrome-leaves-more-space-for-reading',async()=>{
    const geometry=await measure();evidence.geometry.desktop=geometry
    assert.ok(geometry.header.height<=60,`Header is ${geometry.header.height}px`)
    assert.ok(geometry.bar.height<=54,`Reading tools are ${geometry.bar.height}px`)
    assert.ok(geometry.paper.top<=280,`Note paper starts at ${geometry.paper.top}px`)
    assert.ok(geometry.document.top<=215,`PDF starts at ${geometry.document.top}px`)
    assert.ok(geometry.notes.height>=680)
    await input().fill('NGUYÊN LÝ TÀI CHÍNH\n\nGiá trị thời gian của tiền\nMột đồng hôm nay khác một đồng nhận trong tương lai.\n\nCâu hỏi cần suy ngẫm\nMức sinh lời kỳ vọng có tương xứng với rủi ro?')
    await page.waitForTimeout(2000)
    await page.screenshot({path:`${out}/desktop.png`})
  })
  await step('compact-tools-keep-notes-pdf-and-threejs-state',async()=>{
    const url=await page.locator('iframe.br-doc__frame').getAttribute('src'),note=await input().inputValue()
    await page.getByRole('tab',{name:'Ghi chú',exact:true}).click();await page.getByRole('tab',{name:'Song song',exact:true}).click()
    assert.equal(await page.locator('iframe.br-doc__frame').getAttribute('src'),url);assert.equal(await input().inputValue(),note)
    await page.locator('.br-desk-object[data-depth-state="ready"] canvas').waitFor()
    await page.getByRole('button',{name:'Hiệu ứng 3D',exact:true}).click();assert.equal(await page.locator('.br-desk-object canvas').count(),0)
    await page.getByRole('button',{name:'Hiệu ứng 3D',exact:true}).click();await page.locator('.br-desk-object[data-depth-state="ready"] canvas').waitFor()
    await page.getByLabel('Trang đang đọc',{exact:true}).fill('4');await page.getByRole('button',{name:'Lưu vị trí',exact:true}).click()
    await page.getByText('Đã lưu vào kệ sách.',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Vẽ',exact:true}).click();await page.getByLabel('Màu bút',{exact:true}).fill('#134e4a')
    assert.equal(await page.getByRole('button',{name:'Xóa nét',exact:true}).isVisible(),true)
    await page.getByRole('button',{name:'Tẩy',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Tẩy',exact:true}).getAttribute('aria-pressed'),'true')
    await page.getByRole('button',{name:'Gõ',exact:true}).click()
    await page.getByRole('button',{name:'Trang',exact:true}).click()
    await page.getByLabel('Ghi chú trang 2',{exact:true}).fill('Ghi chú bổ sung.')
    await page.getByRole('button',{name:'Lưu',exact:true}).click()
  })
  await step('mobile-position-tools-expand-only-when-needed',async()=>{
    await page.setViewportSize({width:390,height:844})
    await page.getByRole('tab',{name:'Ghi chú',exact:true}).click()
    const scroll=page.locator('.br-notes__scroll');await scroll.evaluate(el=>{el.scrollTop=0})
    const geometry=await measure();evidence.geometry.mobile=geometry
    assert.ok(geometry.header.height<=60,`Mobile header is ${geometry.header.height}px`)
    assert.ok(geometry.bar.height<=60,`Mobile tools are ${geometry.bar.height}px`)
    assert.ok(geometry.paper.top<=350,`Mobile paper starts at ${geometry.paper.top}px`)
    assert.ok(geometry.notes.height>=480)
    assert.equal(await page.getByLabel('Trang đang đọc',{exact:true}).isVisible(),false)
    const toggle=page.getByRole('button',{name:'Vị trí đọc',exact:true})
    await toggle.click();assert.equal(await toggle.getAttribute('aria-expanded'),'true')
    await page.getByLabel('Trang đang đọc',{exact:true}).press('Escape')
    assert.equal(await toggle.getAttribute('aria-expanded'),'false')
    await toggle.press('Enter');assert.equal(await toggle.getAttribute('aria-expanded'),'true')
    await page.getByLabel('Trang đang đọc',{exact:true}).fill('5');await page.getByRole('button',{name:'Lưu vị trí',exact:true}).click()
    await page.getByText('Đã lưu vào kệ sách.',{exact:true}).waitFor()
    await toggle.click();assert.equal(await toggle.getAttribute('aria-expanded'),'false')
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    await page.screenshot({path:`${out}/mobile-notes.png`})
    await page.getByRole('tab',{name:'Sách',exact:true}).click()
    assert.ok((await page.locator('iframe.br-doc__frame').boundingBox()).height>=490)
    await page.screenshot({path:`${out}/mobile-pdf.png`})
  })
  await step('narrow-split-and-small-phone-controls-remain-usable',async()=>{
    await page.setViewportSize({width:1280,height:800})
    await page.getByRole('tab',{name:'Song song',exact:true}).click()
    const separator=page.getByRole('separator');await separator.focus();await separator.press('End')
    await page.getByRole('button',{name:'Vẽ',exact:true}).click()
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    assert.ok(await page.locator('.br-notes').evaluate(el=>el.scrollWidth<=el.clientWidth+2))
    await page.getByRole('button',{name:'Gõ',exact:true}).click()
    await page.setViewportSize({width:360,height:800});await page.getByRole('tab',{name:'Ghi chú',exact:true}).click()
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    for(const name of ['Gõ','Vẽ','Tẩy','Chèn ảnh','Trang'])assert.equal(await page.getByRole('button',{name,exact:true}).isVisible(),true)
    await page.getByRole('button',{name:'Xong',exact:true}).click()
  })
  assert.deepEqual(evidence.pageErrors,[])
}finally{await writeFile(`${out}/browser-evidence.json`,JSON.stringify(evidence,null,2));await browser.close()}
console.log(JSON.stringify(evidence,null,2))
