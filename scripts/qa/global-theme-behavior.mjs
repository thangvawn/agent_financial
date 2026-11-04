import { chromium } from 'playwright'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import assert from 'node:assert/strict'
const out='output/global-theme'
await mkdir(out,{recursive:true})
const session=JSON.parse(await readFile(`${out}/session.json`,'utf8'))
const browser=await chromium.launch()
const context=await browser.newContext({viewport:{width:1440,height:1000}})
await context.addInitScript(s=>{localStorage.setItem('public-beta.session_id',s.session_id);localStorage.setItem('public-beta.user_profile',JSON.stringify(s.profile));localStorage.setItem('learn-reader:depth','off')},session)
const page=await context.newPage(),errors=[],checks=[],surfaces=[]
const points=Array.from({length:160},(_,i)=>({date:new Date(Date.UTC(2025,0,i+1)).toISOString(),open:80+i/8,close:81+i/8+Math.sin(i),high:83+i/8,low:79+i/8,volume:100000+i*100}))
const periods=['2025','2024','2023']; const workspace={company:{ticker:'FPT',name:'Doanh nghiệp QA',industry:'Công nghệ',latest_period:'2025'},statements:Object.fromEntries(['income','balance','cash_flow'].map(kind=>[kind,{periods,rows:[{key:'revenue',label:'Revenue',values:periods.map((period,i)=>({period,value:[3000000000,2400000000,2000000000][i]}))},{key:'net_income',label:'Net income',values:periods.map((period,i)=>({period,value:[600000000,400000000,300000000][i]}))}]}])),trend:{periods,series:[]},ratios:{groups:[]},data_provenance:{provider:'QA fixture'}}
page.on('pageerror',e=>errors.push(e.message))
await page.route('**/*',async route=>{
 const url=new URL(route.request().url())
 if(url.hostname!=='127.0.0.1'&&url.hostname!=='localhost')return route.abort()
 if(url.pathname.endsWith('/company-workspace'))return route.fulfill({json:workspace})
 if(url.pathname.includes('/learning-assets/'))return route.fulfill({contentType:'application/pdf',body:await readFile('frontend/public/learning-assets/books/northstar-sample-reader.pdf')})
 if(!url.pathname.startsWith('/api/'))return route.continue()
 if(url.pathname.includes('/auth/')||url.pathname.includes('/vn-market/')||url.pathname.endsWith('/global-terminal'))return route.continue()
 if(url.pathname.includes('/catalog')||url.pathname.includes('/library'))return route.fulfill({json:{items:[],total:0,history:[],folders:[]}})
 if(url.pathname.includes('/history'))return route.fulfill({json:{points,freshness:'fresh',source:'demo'}})
 return route.fulfill({status:503,json:{detail:'QA: nguồn ngoài chưa kết nối'}})
})
const toggle=()=>page.getByRole('switch',{name:'Chế độ tối',exact:true}).filter({visible:true}).first()
async function setTheme(theme){if(await toggle().getAttribute('aria-checked')!==(theme==='dark'?'true':'false'))await toggle().click();await page.waitForFunction(t=>document.querySelector('.app-shell')?.dataset.theme===t&&document.documentElement.dataset.theme===t,theme)}
async function capture(name){for(const theme of ['dark','light']){await setTheme(theme);await page.screenshot({path:`${out}/${name}-${theme}.png`,animations:'disabled'});surfaces.push({name,theme,colors:await page.locator('main').first().evaluate(e=>({bg:getComputedStyle(e).backgroundColor,ink:getComputedStyle(e).color})),body:(await page.locator('body').innerText()).slice(0,1200)})}}
try {
 await context.addInitScript(()=>{localStorage.setItem('public-beta.market-theme','light')})
 await page.goto('http://127.0.0.1:5190/dashboard-static/global-terminal');await page.locator('.mp-desk').waitFor();assert.equal(await toggle().getAttribute('aria-checked'),'false');checks.push('Legacy Market light preference migrated')
 await setTheme('dark')
 for(const name of ['Learn Hub','BCTC','News','Simulation Lab','Market & Portfolio']){await page.locator('.connected-nav').getByRole('button',{name,exact:true}).click();await page.waitForFunction(()=>document.querySelector('.app-shell')?.dataset.theme==='dark');assert.equal(await toggle().getAttribute('aria-checked'),'true')}
 await setTheme('light');await page.reload();await page.locator('.mp-desk').waitFor();assert.equal(await toggle().getAttribute('aria-checked'),'false');checks.push('Shared preference survives SPA navigation and reload')
 const other=await context.newPage();await other.goto('http://127.0.0.1:5190/dashboard-static/news');await other.getByRole('switch',{name:'Chế độ tối'}).click();await page.waitForFunction(()=>document.querySelector('.app-shell').dataset.theme==='dark');await other.close();checks.push('Browser tabs synchronize preference')
 for(const name of ['Cổ phiếu','Watchlist','Chỉ số','Ngoại hối','Phái sinh','Tài sản số','Hàng hóa','Lệnh giấy','Danh mục']){await page.getByRole('tab',{name,exact:true}).click();await setTheme('light');await setTheme('dark');assert.equal(await page.getByRole('tab',{name,exact:true}).getAttribute('aria-selected'),'true');checks.push(`Market ${name}: theme retains active tab`)}
 await page.setViewportSize({width:390,height:844});const box=await toggle().boundingBox();assert.ok(box.x>=0&&box.x+box.width<=390);await toggle().focus();await page.keyboard.press('Space');assert.equal(await toggle().getAttribute('aria-checked'),'false');checks.push('Shared mobile control is visible and keyboard accessible')
 await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:5190/dashboard-static/login');await page.locator('.auth-page').waitFor();await capture('auth');assert.equal(await page.locator('.app-shell').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(244, 247, 250)');assert.equal(await page.locator('.auth-page button[type=submit]').evaluate(e=>getComputedStyle(e).color),'rgb(255, 255, 255)');checks.push('Authentication surface follows global theme')
 await context.addInitScript(()=>{localStorage.removeItem('public-beta.session_id');localStorage.removeItem('public-beta.user_profile')});await page.goto('http://127.0.0.1:5190/dashboard-static/home');await page.locator('.sparkle-home').waitFor();await capture('home');checks.push('Public homepage follows global theme')
 await context.addInitScript(()=>{const read=Storage.prototype.getItem,write=Storage.prototype.setItem;Storage.prototype.getItem=function(k){if(k==='public-beta.theme')throw new DOMException('Blocked','SecurityError');return read.call(this,k)};Storage.prototype.setItem=function(k,v){if(k==='public-beta.theme')throw new DOMException('Blocked','SecurityError');return write.call(this,k,v)}})
 await page.reload();await page.locator('.sparkle-home').waitFor();await setTheme('light');checks.push('Shared theme remains usable when preference storage is blocked')
 assert.deepEqual(errors,[])
}finally{await writeFile(`${out}/behavior.json`,JSON.stringify({checks,errors,surfaces},null,2));await browser.close()}
console.log(JSON.stringify({checks,errors}))
