import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir,writeFile} from 'node:fs/promises'

const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/notebook-continuation'
await mkdir(out,{recursive:true})
const browser=await chromium.launch({headless:true,channel:'chromium'})
const context=await browser.newContext({viewport:{width:1600,height:1000},reducedMotion:'reduce'})
const page=await context.newPage();page.setDefaultTimeout(15000)
const evidence={passes:[],failures:[],pageErrors:[]}
page.on('pageerror',error=>evidence.pageErrors.push(error.message))
await context.route('**/api/v1/public/learning/catalog?**',route=>route.fulfill({json:{items:[]}}))
await context.route('**/api/v1/public/learning/reader/check?**',route=>route.fulfill({json:{status:'restricted',message:'QA external source'}}))
await context.route('**/fonts.googleapis.com/**',route=>route.fulfill({contentType:'text/css',body:''}))
const response=await context.request.post(origin+'/api/v1/public/auth/register',{data:{name:'Notebook QA',email:`notebook.${Date.now()}@northstar.test`,password:'Notebook-local-QA-2026'}})
assert.equal(response.status(),200)
const account=await response.json()
await context.addInitScript(account=>{
  if(window!==top)return
  localStorage.setItem('public-beta.session_id',account.session_id)
  localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))
  localStorage.setItem('learn-reader:depth','off')
},account)
const papers=()=>page.locator('[data-note-paper]')
const inputs=()=>page.locator('textarea.br-paper__text')
const joined=()=>inputs().evaluateAll(nodes=>nodes.map(node=>node.value).join(''))
const book=()=>page.locator('[data-book-id="openstax-principles-microeconomics-3e"]')
async function open(){await book().getByRole('button',{name:'Đọc PDF',exact:true}).click();await page.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()}
async function reset(){
  await page.getByRole('button',{name:'Xong',exact:true}).click()
  await page.evaluate(()=>{for(const key of Object.keys(localStorage)){if(key.startsWith('learn-reader:')){try{if(JSON.parse(localStorage.getItem(key))?.pages)localStorage.removeItem(key)}catch{ /* preference */ }}}})
  await open()
  if(await page.getByRole('tab',{name:'Ghi chú',exact:true}).isVisible())await page.getByRole('tab',{name:'Ghi chú',exact:true}).click()
}
async function waitForFocus(index){await page.waitForFunction(index=>document.activeElement===document.querySelectorAll('textarea.br-paper__text')[index],index)}
async function step(name,fn){try{await fn();evidence.passes.push(name);console.log('PASS',name)}catch(error){evidence.failures.push({name,error:error.message});await page.screenshot({path:`${out}/failed-${name}.png`,fullPage:true});throw error}}
const longText=Array.from({length:58},(_,i)=>`Dòng ${i+1}: Khả năng lựa chọn, chi phí cơ hội 🌱.`).join('\n')
try{
  await page.goto(origin+'/dashboard-static/learn')
  await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click();await open()
  await step('a4-paper-ratio-through-split-focus-and-mobile-layouts',async()=>{
    async function assertA4() {
      const box=await papers().first().boundingBox()
      assert.ok(Math.abs(box.height/box.width-297/210)<.005,`Expected A4 portrait, got ${box.width} × ${box.height}`)
      const text=await inputs().first().boundingBox()
      assert.ok(Math.abs(text.height-(box.height-2))<2,'Writing area follows the full paper height')
    }
    await assertA4()
    await page.getByRole('tab',{name:'Ghi chú',exact:true}).click();await assertA4()
    assert.ok((await papers().first().boundingBox()).height>1100,'Full A4 note page is taller than the previous 620px paper')
    await page.setViewportSize({width:1400,height:1600})
    await inputs().first().fill('SỔ GHI CHÚ A4\n\nÝ chính của tài liệu\n\nNhững khái niệm cần nhớ và câu hỏi để suy ngẫm.\n\nVí dụ áp dụng\n\nGhi lại cách vận dụng kiến thức vào thực tế.')
    await page.screenshot({path:`${out}/paper-a4.png`,fullPage:true})
    await inputs().first().fill('')
    await page.setViewportSize({width:390,height:844});await assertA4()
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    await page.setViewportSize({width:1600,height:1000})
    await page.getByRole('tab',{name:'Song song',exact:true}).click()
  })
  await step('scroll-adds-one-page-without-stealing-focus-or-layout',async()=>{
    await page.waitForTimeout(400);assert.equal(await papers().count(),1)
    await inputs().first().fill('Ý chính ban đầu.')
    const rect=await page.locator('.br-notes__scroll').boundingBox()
    await page.mouse.move(rect.x+rect.width-30,rect.y+rect.height-35);await page.mouse.wheel(0,900)
    await page.waitForFunction(()=>document.querySelectorAll('[data-note-paper]').length===2)
    await page.waitForTimeout(300)
    assert.equal(await papers().count(),2)
    assert.equal(await inputs().first().inputValue(),'Ý chính ban đầu.')
    assert.equal(await page.getByRole('tab',{name:'Song song',exact:true}).getAttribute('aria-selected'),'true')
    await waitForFocus(0)
    const top=await page.locator('.br-notes__scroll').evaluate(el=>el.scrollTop)
    await page.locator('.br-notes__scroll').evaluate(el=>{for(let i=0;i<20;i++)el.dispatchEvent(new Event('scroll'))})
    assert.equal(await papers().count(),2)
    assert.equal(await page.locator('.br-notes__scroll').evaluate(el=>el.scrollTop),top)
  })
  await step('long-paste-reuses-blank-page-and-keeps-every-character',async()=>{
    const blankId=await papers().nth(1).getAttribute('data-note-page-id')
    await inputs().first().fill(longText)
    await page.waitForFunction(()=>document.querySelectorAll('[data-note-paper]').length>2)
    const count=await papers().count();await waitForFocus(count-1)
    assert.equal(await papers().nth(1).getAttribute('data-note-page-id'),blankId)
    assert.equal(await joined(),longText)
    assert.ok(await inputs().evaluateAll(nodes=>nodes.every(node=>node.scrollHeight<=node.clientHeight+1)))
    assert.ok(await papers().evaluateAll(nodes=>nodes.every((node,index)=>!index || node.getBoundingClientRect().top>=nodes[index-1].getBoundingClientRect().bottom+10)),'A4 sheets must occupy separate grid rows without overlap')
    await page.keyboard.insertText('\nGhi tiếp ở trang mới.')
    assert.equal(await joined(),longText+'\nGhi tiếp ở trang mới.')
    await page.screenshot({path:`${out}/continued-desktop.png`,fullPage:true})
  })
  await step('editing-earlier-page-preserves-later-notes-and-caret',async()=>{
    const previous=await inputs().evaluateAll(nodes=>nodes.slice(1).map(node=>node.value))
    const replacement=longText+'\nPhần được chèn trước ghi chú cũ.'
    await inputs().first().evaluate((input,text)=>{
      input.focus();Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,text)
      input.setSelectionRange(8,8);input.dispatchEvent(new Event('input',{bubbles:true}))
    },replacement)
    await waitForFocus(0)
    await page.waitForTimeout(150)
    assert.equal(await joined(),replacement+previous.join(''))
    assert.equal(await inputs().first().evaluate(input=>input.selectionStart),8)
  })
  await step('continued-pages-save-and-reopen-without-duplication',async()=>{
    const text=await joined(),count=await papers().count()
    await page.getByRole('button',{name:'Xong',exact:true}).click();await open()
    assert.equal(await joined(),text);assert.equal(await papers().count(),count)
  })
  await step('vietnamese-composition-finishes-before-pagination',async()=>{
    await reset()
    const input=inputs().first()
    await input.evaluate((input,text)=>{
      input.focus();input.dispatchEvent(new CompositionEvent('compositionstart',{bubbles:true,data:''}))
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(input,text)
      input.setSelectionRange(text.length,text.length)
      input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertCompositionText',isComposing:true,data:'ế'}))
    },longText)
    assert.equal(await papers().count(),1);assert.equal(await input.inputValue(),longText)
    await input.dispatchEvent('compositionend',{data:'ế'})
    await page.waitForFunction(()=>document.querySelectorAll('[data-note-paper]').length>1)
    assert.equal(await joined(),longText)
    await waitForFocus((await papers().count())-1)
  })
  await step('drawing-near-bottom-prepares-next-paper-and-keeps-ink',async()=>{
    await reset()
    await page.getByRole('button',{name:'Vẽ',exact:true}).click()
    await page.locator('.br-notes__scroll').evaluate(el=>{el.scrollTop=el.scrollHeight-el.clientHeight})
    await page.waitForTimeout(150)
    assert.equal(await papers().count(),1,'Programmatic scroll alone must not add blank pages')
    const rect=await page.locator('.br-paper__canvas.is-ink').boundingBox()
    await page.mouse.move(rect.x+60,rect.y+rect.height*.95);await page.mouse.down()
    await page.mouse.move(rect.x+130,rect.y+rect.height*.96,{steps:6});await page.mouse.up()
    await page.waitForFunction(()=>document.querySelectorAll('[data-note-paper]').length===2)
    await page.getByRole('button',{name:'Lưu',exact:true}).click()
    assert.ok(await page.evaluate(()=>Object.keys(localStorage).some(key=>{try{return JSON.parse(localStorage.getItem(key))?.pages?.[0]?.drawingDataUrl?.startsWith('data:image/png')}catch{return false}})))
  })
  await step('mobile-pagination-keeps-caret-visible-and-full-text',async()=>{
    await page.setViewportSize({width:390,height:844});await reset()
    await inputs().first().fill(longText)
    await page.waitForFunction(()=>document.querySelectorAll('[data-note-paper]').length>1)
    await waitForFocus((await papers().count())-1)
    assert.equal(await joined(),longText)
    assert.ok(await inputs().evaluateAll(nodes=>nodes.every(node=>node.scrollHeight<=node.clientHeight+1)))
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    assert.ok(await papers().evaluateAll(nodes=>nodes.every((node,index)=>!index || node.getBoundingClientRect().top>=nodes[index-1].getBoundingClientRect().bottom+10)),'Mobile A4 pages must never overlap')
    assert.ok(await page.locator('.br-pages__strip').evaluate(strip=>{
      const bounds=strip.getBoundingClientRect(),active=strip.querySelector('[aria-selected="true"]').getBoundingClientRect()
      return bounds.height<50 && active.left>=bounds.left-1 && active.right<=bounds.right+1
    }),'Many page tabs stay in one row and the active page remains visible')
    await page.keyboard.insertText('\nGhi thêm từ điện thoại.')
    assert.equal(await joined(),longText+'\nGhi thêm từ điện thoại.')
    await page.waitForTimeout(200)
    const mobilePosition=await page.locator('.br-notes__scroll').evaluate(scroll=>{
      const input=document.activeElement,rect=input.getBoundingClientRect(),viewport=scroll.getBoundingClientRect()
      return {top:rect.top,bottom:rect.bottom,viewTop:viewport.top,viewBottom:viewport.bottom}
    })
    assert.ok(mobilePosition.top<mobilePosition.viewBottom && mobilePosition.bottom>mobilePosition.viewTop,'The focused A4 page must remain visible after typing')
    // Full-page capture can resize this fixed workspace and move its inner scroll.
    await page.screenshot({path:`${out}/continued-mobile.png`})
  })
  await step('mobile-touch-at-bottom-adds-one-empty-page',async()=>{
    await reset()
    await page.locator('.br-notes__scroll').evaluate(el=>{el.scrollTop=el.scrollHeight-el.clientHeight})
    await page.waitForTimeout(150)
    assert.equal(await papers().count(),1)
    const rect=await page.locator('.br-notes__scroll').boundingBox()
    const cdp=await context.newCDPSession(page)
    await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true})
    const x=Math.round(rect.x+rect.width/2),y=Math.round(rect.y+rect.height-30)
    await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]})
    for(let i=1;i<=8;i++){
      await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y-i*10}]})
      await page.waitForTimeout(25)
    }
    await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]})
    await page.waitForFunction(()=>document.querySelectorAll('[data-note-paper]').length===2)
    await page.waitForTimeout(300)
    assert.equal(await papers().count(),2)
    assert.equal(await joined(),'')
    await cdp.detach()
  })
  assert.deepEqual(evidence.pageErrors,[])
}finally{
  await writeFile(`${out}/browser-evidence.json`,JSON.stringify(evidence,null,2));await browser.close()
}
console.log(JSON.stringify(evidence,null,2))
