import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'

const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/reader-studio'
await mkdir(out,{recursive:true})
const browser=await chromium.launch({headless:true,channel:'chromium',args:['--enable-unsafe-swiftshader']})
const context=await browser.newContext({viewport:{width:1600,height:1000}})
const evidence={passes:[],failures:[],pageErrors:[]}
const page=await context.newPage();page.setDefaultTimeout(20000)
page.on('pageerror',e=>evidence.pageErrors.push(e.message))
const response=await context.request.post(origin+'/api/v1/public/auth/register',{data:{name:'Reader design QA',email:`reader-design.${Date.now()}@northstar.test`,password:'Reader-design-QA-2026'}})
assert.equal(response.status(),200)
const account=await response.json()
async function setup(ctx,{noWebGL=false}={}) {
  await ctx.route('**/api/v1/public/learning/catalog?**',r=>r.fulfill({json:{items:[]}}))
  await ctx.route('**/api/v1/public/learning/reader/check?**',r=>r.fulfill({json:{status:'restricted',message:'QA external source.'}}))
  await ctx.route('**/fonts.googleapis.com/**',r=>r.fulfill({contentType:'text/css',body:''}))
  await ctx.addInitScript(({account,noWebGL})=>{
    if(window!==top)return
    localStorage.setItem('public-beta.session_id',account.session_id)
    localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))
    window.__studioDraws=0
    if(noWebGL){const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind.includes('webgl')?null:original.call(this,kind,...args)}}
    else for(const name of ['drawElements','drawArrays']){
      const original=WebGL2RenderingContext.prototype[name]
      WebGL2RenderingContext.prototype[name]=function(...args){window.__studioDraws++;return original.apply(this,args)}
    }
  },{account,noWebGL})
}
await setup(context)
const bookCard=target=>target.locator('[data-book-id="openstax-principles-microeconomics-3e"]')
async function openReader(target=page) {
  await target.goto(origin+'/dashboard-static/learn')
  await target.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click()
  await bookCard(target).getByRole('button',{name:'Đọc PDF',exact:true}).click()
  await target.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()
}
async function step(name,fn){try{await fn();evidence.passes.push(name);console.log('PASS',name)}catch(error){evidence.failures.push({name,error:error.message});await page.screenshot({path:`${out}/failed-${name}.png`,fullPage:true});throw error}}
const note='NGUYÊN LÝ KINH TẾ VI MÔ\n\n01. Sự khan hiếm & lựa chọn\nNguồn lực có giới hạn. Mỗi quyết định đều đi kèm một sự đánh đổi.\n\n02. Chi phí cơ hội\nGiá trị của phương án tốt nhất phải từ bỏ khi lựa chọn.\n\nCâu hỏi để suy ngẫm\nÁp dụng khái niệm này thế nào khi phân bổ thời gian và ngân sách?'
try {
  await openReader()
  await step('real-threejs-scene-and-idle-render-budget',async()=>{
    await page.locator('.br-desk-object[data-depth-state="ready"] canvas').waitFor()
    await page.waitForTimeout(1300)
    const before=await page.evaluate(()=>window.__studioDraws)
    assert.ok(before>0,'Three.js must actually draw geometry')
    await page.waitForTimeout(300)
    assert.equal(await page.evaluate(()=>window.__studioDraws),before,'No perpetual idle render loop')
    evidence.webgl=await page.locator('.br-desk-object canvas').evaluate(canvas=>canvas.getContext('webgl2').getParameter(7938))
    assert.equal(await page.getByRole('tab',{name:'Song song',exact:true}).getAttribute('aria-selected'),'true')
  })
  await step('focus-layouts-preserve-document-and-notes',async()=>{
    const input=page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first()
    await input.fill(note)
    const url=await page.locator('iframe.br-doc__frame').getAttribute('src')
    await page.getByRole('tab',{name:'Sách',exact:true}).click()
    assert.equal(await page.locator('.br-notes').isVisible(),false)
    assert.ok((await page.locator('.br-book').boundingBox()).width>1400)
    await page.getByRole('tab',{name:'Ghi chú',exact:true}).click()
    assert.equal(await input.inputValue(),note)
    assert.equal(await page.locator('.br-book').isVisible(),false)
    await page.getByRole('tab',{name:'Song song',exact:true}).click()
    assert.equal(await page.locator('iframe.br-doc__frame').getAttribute('src'),url)
  })
  await step('splitter-keyboard-and-pointer-control',async()=>{
    const separator=page.getByRole('separator')
    await separator.focus();await separator.press('ArrowRight')
    assert.equal(await separator.getAttribute('aria-valuenow'),'58')
    await separator.press('Home');assert.equal(await separator.getAttribute('aria-valuenow'),'28')
    await separator.press('End');assert.equal(await separator.getAttribute('aria-valuenow'),'72')
    await separator.dblclick();assert.equal(await separator.getAttribute('aria-valuenow'),'56')
    const rect=await separator.boundingBox()
    await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);await page.mouse.down();await page.mouse.move(rect.x-100,rect.y+rect.height/2,{steps:6});await page.mouse.up()
    assert.ok(Number(await separator.getAttribute('aria-valuenow'))<56)
    assert.equal(await page.evaluate(()=>document.body.classList.contains('br-resizing')),false)
    await separator.dblclick()
  })
  await step('depth-toggle-releases-webgl-and-persists',async()=>{
    await page.locator('.br-desk-object canvas').evaluate(canvas=>{window.__previousGL=canvas.getContext('webgl2')})
    await page.getByRole('button',{name:'Hiệu ứng 3D',exact:true}).click()
    assert.equal(await page.locator('.br-desk-object canvas').count(),0)
    assert.equal(await page.evaluate(()=>window.__previousGL.isContextLost()),true)
    assert.equal(await page.evaluate(()=>localStorage.getItem('learn-reader:depth')),'off')
    await page.getByRole('button',{name:'Hiệu ứng 3D',exact:true}).click()
    await page.locator('.br-desk-object[data-depth-state="ready"] canvas').waitFor()
  })
  await step('pen-eraser-and-extra-note-page',async()=>{
    await page.getByRole('button',{name:'Vẽ',exact:true}).click()
    const canvas=page.locator('.br-paper__canvas.is-ink').first(),rect=await canvas.boundingBox()
    await page.mouse.move(rect.x+75,rect.y+350);await page.mouse.down();await page.mouse.move(rect.x+200,rect.y+365,{steps:8});await page.mouse.up()
    assert.equal(await page.getByRole('button',{name:'Vẽ',exact:true}).getAttribute('aria-pressed'),'true')
    await page.getByRole('button',{name:'Tẩy',exact:true}).click()
    assert.equal(await page.getByRole('button',{name:'Tẩy',exact:true}).getAttribute('aria-pressed'),'true')
    await page.getByRole('button',{name:'Gõ',exact:true}).click()
    await page.getByRole('button',{name:'Trang',exact:true}).click()
    assert.equal(await page.locator('[data-note-paper]').count(),2)
    await page.getByRole('tablist',{name:'Trang ghi chú',exact:true}).getByRole('tab',{name:'2',exact:true}).click()
    await page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').nth(1).fill('Câu hỏi và ví dụ vận dụng của tôi.')
    await page.getByRole('tablist',{name:'Trang ghi chú',exact:true}).getByRole('tab',{name:'1',exact:true}).click()
    await page.getByRole('tab',{name:'Song song',exact:true}).click()
  })
  await step('save-notes-and-reading-location-then-reopen',async()=>{
    await page.getByLabel('Trang đang đọc',{exact:true}).fill('21')
    await page.getByRole('button',{name:'Lưu vị trí',exact:true}).click()
    await page.getByText('Đã lưu vào kệ sách.',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Lưu',exact:true}).click()
    await page.getByRole('button',{name:'Xong',exact:true}).click()
    assert.equal(await page.locator('.br-desk-object canvas').count(),0)
    await bookCard(page).getByRole('button',{name:'Đọc PDF',exact:true}).click()
    await page.locator('iframe.br-doc__frame').waitFor()
    assert.match(await page.locator('iframe.br-doc__frame').getAttribute('src'),/#page=21&view=FitH&navpanes=0/)
    assert.equal(await page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first().inputValue(),note)
    await page.waitForTimeout(2200)
    await page.screenshot({path:`${out}/reader-desktop.png`,fullPage:true})
  })
  await step('reduced-motion-is-static-and-context-loss-has-fallback',async()=>{
    await page.emulateMedia({reducedMotion:'reduce'})
    await page.waitForTimeout(250)
    const before=await page.evaluate(()=>window.__studioDraws)
    await page.mouse.move(600,110);await page.mouse.move(1000,130)
    await page.waitForTimeout(300)
    assert.equal(await page.evaluate(()=>window.__studioDraws),before)
    await page.locator('.br-desk-object canvas').evaluate(canvas=>canvas.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext())
    await page.locator('.br-desk-object[data-depth-state="fallback"]').waitFor()
    assert.equal(await page.getByRole('button',{name:'Lưu',exact:true}).isEnabled(),true)
    await page.getByRole('button',{name:'Hiệu ứng 3D',exact:true}).click();await page.getByRole('button',{name:'Hiệu ứng 3D',exact:true}).click()
    await page.locator('.br-desk-object[data-depth-state="ready"] canvas').waitFor()
    await page.emulateMedia({reducedMotion:'no-preference'})
  })
  await step('mobile-read-and-write-without-horizontal-overflow',async()=>{
    await page.setViewportSize({width:390,height:844})
    await page.waitForFunction(()=>document.querySelector('.br-stage')?.classList.contains('br-stage--book'))
    assert.equal(await page.getByRole('tab',{name:'Song song',exact:true}).count(),0)
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    assert.ok((await page.locator('iframe.br-doc__frame').boundingBox()).height>230)
    await page.screenshot({path:`${out}/reader-mobile.png`,fullPage:true})
    await page.getByRole('tab',{name:'Ghi chú',exact:true}).click()
    assert.equal(await page.locator('.br-notes').isVisible(),true)
    const notes=page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first()
    await notes.fill(note+'\n\nGhi thêm từ điện thoại.')
    await page.getByRole('button',{name:'Lưu',exact:true}).click()
    await page.screenshot({path:`${out}/notes-mobile.png`,fullPage:true})
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
  })
  await step('no-webgl-browser-still-reads-and-edits',async()=>{
    const fallbackContext=await browser.newContext({viewport:{width:1440,height:1000}})
    await setup(fallbackContext,{noWebGL:true})
    const fallback=await fallbackContext.newPage();fallback.on('pageerror',e=>evidence.pageErrors.push(e.message))
    await openReader(fallback)
    await fallback.locator('.br-desk-object[data-depth-state="fallback"]').waitFor()
    const input=fallback.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first()
    await input.fill('Reader vẫn hoạt động khi trình duyệt không hỗ trợ WebGL.')
    await fallback.getByRole('button',{name:'Lưu',exact:true}).click()
    await fallback.screenshot({path:`${out}/fallback-desktop.png`,fullPage:true})
    await fallbackContext.close()
  })
  assert.deepEqual(evidence.pageErrors,[])
}finally{
  await writeFile(`${out}/browser-evidence.json`,JSON.stringify(evidence,null,2));await browser.close()
}
console.log(JSON.stringify(evidence,null,2))
