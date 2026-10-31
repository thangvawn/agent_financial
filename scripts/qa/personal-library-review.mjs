import {chromium} from 'playwright'
import assert from 'node:assert/strict'
import {mkdir,readFile,writeFile} from 'node:fs/promises'
import {createHash} from 'node:crypto'

const origin=process.env.REVIEW_ORIGIN || 'http://127.0.0.1:5186'
const out='output/playwright/personal-library'
await mkdir(out,{recursive:true})
// Tiny, real three-page PDFs make this review independent of personal files.
function fixturePdf(title) {
  const objects=['<< /Type /Catalog /Pages 2 0 R >>','<< /Type /Pages /Kids [3 0 R 5 0 R 7 0 R] /Count 3 >>']
  for(let page=1;page<=3;page++){
    const content=`BT /F1 22 Tf 50 740 Td (${title}) Tj /F1 12 Tf 0 -50 Td (Page ${page} / 3 - Local upload verification) Tj ET`
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 9 0 R >> >> /Contents ${page*2+2} 0 R >>`,`<< /Length ${Buffer.byteLength(content)} >>\nstream\n${content}\nendstream`)
  }
  objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
  let body='%PDF-1.4\n';const offsets=[0]
  objects.forEach((value,index)=>{offsets.push(Buffer.byteLength(body));body+=`${index+1} 0 obj\n${value}\nendobj\n`})
  const xref=Buffer.byteLength(body)
  body+=`xref\n0 ${offsets.length}\n0000000000 65535 f \n`+offsets.slice(1).map(offset=>`${String(offset).padStart(10,'0')} 00000 n \n`).join('')
  return Buffer.from(body+`trailer\n<< /Size ${offsets.length} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`)
}
const paperPath=`${out}/paper-fixture.pdf`,documentPath=`${out}/document-fixture.pdf`
await writeFile(paperPath,fixturePdf('Research paper - QA'))
await writeFile(documentPath,fixturePdf('Personal document - QA'))
const browser=await chromium.launch({headless:true,channel:'chromium'})
const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true})
const page=await context.newPage();page.setDefaultTimeout(15000)
const evidence={passes:[],failures:[],pageErrors:[]}
page.on('pageerror',error=>evidence.pageErrors.push(error.message))
await context.route('**/api/v1/public/learning/catalog?**',route=>route.fulfill({json:{items:[]}}))
await context.route('**/api/v1/public/learning/reader/check?**',route=>route.fulfill({json:{status:'restricted',message:'QA: nguồn ngoài.'}}))
await context.route('**/fonts.googleapis.com/**',route=>route.fulfill({contentType:'text/css',body:''}))
const email=`shelf.${Date.now()}@northstar.test`,password='Local-shelf-QA-2026'
const registered=await context.request.post(origin+'/api/v1/public/auth/register',{data:{name:'Personal library QA',email,password}})
assert.equal(registered.status(),200)
let account=await registered.json()
await context.addInitScript(account=>{if(window!==window.top || localStorage.getItem('public-beta.session_id'))return;localStorage.setItem('public-beta.session_id',account.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))},account)
const paperTitle='Nghiên cứu từ máy của tôi'
let paperId
const shelf=()=>page.getByRole('tab',{name:'Kệ sách của tôi',exact:true}).click()
const card=()=>page.locator(`[data-library-id="${paperId}"]`)
async function closeReader(){await page.getByRole('button',{name:'Xong',exact:true}).click();await page.locator('.pl-library').waitFor()}
async function step(name,fn){try{await fn();evidence.passes.push(name);console.log('PASS',name)}catch(error){evidence.failures.push({name,error:error.message});await page.screenshot({path:`${out}/failed-${name}.png`,fullPage:true});throw error}}
try{
  await page.goto(origin+'/dashboard-static/learn')
  await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click()
  await step('upload-real-paper-from-local',async()=>{
    await page.getByRole('button',{name:'Thêm tài liệu',exact:true}).click()
    const dialog=page.getByRole('dialog')
    await dialog.getByLabel('File PDF').setInputFiles(paperPath)
    await dialog.getByLabel('Tên tài liệu',{exact:true}).fill(paperTitle)
    await dialog.getByLabel('Tác giả',{exact:true}).fill('Người dùng')
    await dialog.getByLabel('Loại tài liệu',{exact:true}).selectOption('paper')
    await page.screenshot({path:`${out}/upload-desktop.png`,fullPage:true})
    const [response]=await Promise.all([page.waitForResponse(r=>r.url().endsWith('/library/uploads') && r.request().method()==='POST'),dialog.getByRole('button',{name:'Tải lên kệ sách'}).click()])
    assert.equal(response.status(),201)
    const item=await response.json();paperId=item.id
    assert.equal(item.page_count,3)
    await card().getByRole('heading',{name:paperTitle}).waitFor()
    assert.equal(await card().getByLabel(`Trạng thái đọc: ${paperTitle}`).inputValue(),'want_to_read')
  })
  await step('duplicate-upload-reuses-shelf-item',async()=>{
    await page.getByRole('button',{name:'Thêm tài liệu',exact:true}).click()
    const dialog=page.getByRole('dialog');await dialog.getByLabel('File PDF').setInputFiles(paperPath)
    const [response]=await Promise.all([page.waitForResponse(r=>r.url().endsWith('/library/uploads')),dialog.getByRole('button',{name:'Tải lên kệ sách'}).click()])
    assert.equal(response.status(),200);assert.equal((await response.json()).id,paperId)
    await page.getByRole('dialog').waitFor({state:'hidden'})
    assert.equal(await page.locator('.pl-card').count(),1)
  })
  await step('failed-document-does-not-count-as-read',async()=>{
    const url=`**/library/items/${paperId}/file.pdf`
    await context.route(url,route=>route.fulfill({status:404,body:'missing'}))
    await card().getByRole('button',{name:'Mở đọc',exact:true}).click()
    await page.getByRole('heading',{name:'Không còn tại nguồn'}).waitFor()
    await closeReader()
    await card().getByText('Chưa mở đọc',{exact:true}).waitFor()
    assert.equal(await card().getByRole('combobox').inputValue(),'want_to_read')
    await context.unroute(url)
  })
  await step('read-private-pdf-and-save-position',async()=>{
    await card().getByRole('button',{name:'Mở đọc',exact:true}).click()
    await page.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()
    await page.waitForFunction(()=>document.querySelector('[aria-label="Trạng thái đọc trong kệ"]')?.value==='reading')
    await page.getByLabel('Trang đang đọc',{exact:true}).fill('2')
    await page.getByRole('button',{name:'Lưu vị trí',exact:true}).click()
    await page.getByText('Đã lưu vào kệ sách.',{exact:true}).waitFor()
    await Promise.all([page.waitForResponse(r=>r.url().includes(`/items/${paperId}`) && r.request().method()==='PATCH'),page.getByLabel('Trạng thái đọc trong kệ').selectOption('completed')])
    // Native Chromium PDF viewer renders after the blob iframe is attached.
    await page.waitForTimeout(2000)
    await page.screenshot({path:`${out}/reader-desktop.png`,fullPage:true})
    await closeReader()
    await card().getByText('1 lượt mở · Vị trí đã lưu: trang 2',{exact:false}).waitFor()
  })
  await step('resume-and-download-original-private-pdf',async()=>{
    await card().getByRole('button',{name:'Đọc tiếp',exact:true}).click()
    const frame=page.locator('iframe.br-doc__frame[src^="blob:"]');await frame.waitFor()
    assert.ok((await frame.getAttribute('src')).endsWith('#page=2'))
    await page.waitForFunction(()=>document.querySelector('[aria-label="Trạng thái đọc trong kệ"]')?.value==='completed')
    await page.waitForTimeout(1500)
    await page.screenshot({path:`${out}/reader-resumed.png`,fullPage:true})
    const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Tải PDF',exact:true}).click()])
    const expected=await readFile(paperPath),actual=await readFile(await download.path())
    assert.equal(createHash('sha256').update(actual).digest('hex'),createHash('sha256').update(expected).digest('hex'))
    await closeReader()
    await card().getByText('2 lượt mở',{exact:false}).waitFor()
  })
  await step('history-and-status-filters',async()=>{
    await page.getByRole('button',{name:/^Lịch sử đọc/}).click();await card().waitFor()
    await page.getByRole('button',{name:/^Muốn đọc/}).click();assert.equal(await page.locator('.pl-card').count(),0)
    await page.getByRole('button',{name:/^Đã đọc/}).click();await card().waitFor()
    await page.getByLabel('Loại tài liệu trên kệ').selectOption('book');assert.equal(await page.locator('.pl-card').count(),0)
    await page.getByLabel('Loại tài liệu trên kệ').selectOption('paper');await card().waitFor()
    await page.getByLabel('Tìm trong kệ sách').fill('không tồn tại');assert.equal(await page.locator('.pl-card').count(),0)
    await page.getByLabel('Tìm trong kệ sách').fill('')
    await page.getByLabel('Loại tài liệu trên kệ').selectOption('all')
    await page.getByRole('button',{name:/^Tất cả/}).click()
  })
  await step('saved-library-book-and-metadata-edit',async()=>{
    await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click()
    const book=page.locator('[data-book-id="openstax-principles-finance-2e"]')
    await book.getByRole('button',{name:'Thêm vào kệ',exact:true}).click()
    await book.getByRole('button',{name:'Đã có trên kệ',exact:true}).waitFor()
    await shelf();assert.equal(await page.locator('.pl-card').count(),2)
    await card().getByRole('button',{name:'Sửa',exact:true}).click()
    await card().getByLabel('Tên tài liệu',{exact:true}).fill('Paper đã đổi tên')
    await card().getByRole('button',{name:'Lưu thay đổi',exact:true}).click()
    await card().getByRole('heading',{name:'Paper đã đổi tên'}).waitFor()
  })
  await step('shelf-survives-refresh-and-new-login-session',async()=>{
    const login=await context.request.post(origin+'/api/v1/public/auth/login',{data:{email,password}})
    assert.equal(login.status(),200);account=await login.json()
    await page.evaluate(account=>{localStorage.setItem('public-beta.session_id',account.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(account.profile))},account)
    await page.reload();await shelf();await card().waitFor()
    assert.equal(await page.locator('.pl-card').count(),2)
    assert.equal(await card().getByRole('combobox').inputValue(),'completed')
    await page.screenshot({path:`${out}/shelf-desktop.png`,fullPage:true})
  })
  await step('second-account-cannot-list-read-edit-delete',async()=>{
    const other=await context.request.post(origin+'/api/v1/public/auth/register',{data:{name:'Other reader',email:`other.${Date.now()}@northstar.test`,password}})
    const user=await other.json(),headers={Authorization:`Bearer ${user.session_id}`}
    const base=origin+'/api/v1/public/learning/library'
    assert.deepEqual((await (await context.request.get(base,{headers})).json()).items,[])
    assert.equal((await context.request.get(`${base}/items/${paperId}/file.pdf`,{headers})).status(),404)
    assert.equal((await context.request.patch(`${base}/items/${paperId}`,{headers,data:{status:'reading'}})).status(),404)
    assert.equal((await context.request.delete(`${base}/items/${paperId}`,{headers})).status(),404)
    assert.equal((await context.request.get(`${base}/items/${paperId}/file.pdf`)).status(),401)
  })
  await step('upload-document-from-mobile-and-delete',async()=>{
    await page.setViewportSize({width:390,height:844})
    await page.getByRole('button',{name:'Thêm tài liệu',exact:true}).click()
    const dialog=page.getByRole('dialog')
    await dialog.getByLabel('File PDF').setInputFiles(documentPath)
    await dialog.getByLabel('Tên tài liệu',{exact:true}).fill('Tài liệu cá nhân')
    await dialog.getByLabel('Loại tài liệu',{exact:true}).selectOption('document')
    const [response]=await Promise.all([page.waitForResponse(r=>r.url().endsWith('/library/uploads')),dialog.getByRole('button',{name:'Tải lên kệ sách'}).click()])
    assert.equal(response.status(),201)
    const item=await response.json(),uploaded=page.locator(`[data-library-id="${item.id}"]`)
    await uploaded.getByRole('heading',{name:'Tài liệu cá nhân'}).waitFor()
    await uploaded.getByRole('button',{name:'Mở đọc',exact:true}).click()
    await page.locator('iframe.br-doc__frame[src^="blob:"]').waitFor()
    await page.waitForFunction(()=>document.querySelector('[aria-label="Trạng thái đọc trong kệ"]')?.value==='reading')
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    await page.waitForTimeout(1000)
    await page.screenshot({path:`${out}/reader-mobile.png`,fullPage:true})
    await closeReader()
    await uploaded.getByRole('button',{name:'Xóa khỏi kệ',exact:true}).click()
    await uploaded.getByRole('button',{name:'Xác nhận xóa'}).click();await uploaded.waitFor({state:'detached'})
  })
  await step('mobile-shelf-and-upload-form',async()=>{
    await page.setViewportSize({width:390,height:844})
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1))
    await page.screenshot({path:`${out}/shelf-mobile.png`,fullPage:true})
    await page.getByRole('button',{name:'Thêm tài liệu',exact:true}).click()
    await page.screenshot({path:`${out}/upload-mobile.png`,fullPage:true})
    await page.getByRole('dialog').getByLabel('File PDF').setInputFiles({name:'broken.pdf',mimeType:'application/pdf',buffer:Buffer.from('not a PDF')})
    await page.getByRole('button',{name:'Tải lên kệ sách'}).click()
    await page.getByRole('dialog').getByRole('alert').waitFor()
    assert.equal(await page.getByRole('dialog').getByRole('button',{name:'Tải lên kệ sách'}).isEnabled(),true)
    await page.getByRole('button',{name:'Đóng thêm tài liệu'}).click()
  })
  await step('delete-confirmation-removes-private-file',async()=>{
    await card().getByRole('button',{name:'Xóa khỏi kệ',exact:true}).click()
    await card().getByRole('button',{name:'Giữ lại'}).click();await card().waitFor()
    await card().getByRole('button',{name:'Xóa khỏi kệ',exact:true}).click()
    await card().getByRole('button',{name:'Xác nhận xóa'}).click();await card().waitFor({state:'detached'})
    const file=await context.request.get(`${origin}/api/v1/public/learning/library/items/${paperId}/file.pdf`,{headers:{Authorization:`Bearer ${account.session_id}`}})
    assert.equal(file.status(),404)
  })
  assert.deepEqual(evidence.pageErrors,[])
} finally {
  await writeFile(`${out}/browser-evidence.json`,JSON.stringify(evidence,null,2));await browser.close()
}
console.log(JSON.stringify(evidence,null,2))
