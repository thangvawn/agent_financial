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
 if(url.pathname.includes('/catalog')&&url.searchParams.get('kind')==='book')return route.fulfill({json:{items:[{asset_id:'theme-book',title:'Theme QA PDF',author:'QA fixture',pdf_url:'/learning-assets/books/northstar-sample-reader.pdf',content_role:'full_text',kind:'book'}]}})
 if(url.pathname.includes('/catalog')||url.pathname.includes('/library'))return route.fulfill({json:{items:[],total:0,history:[],folders:[]}})
 if(url.pathname.includes('/history'))return route.fulfill({json:{points,freshness:'fresh',source:'demo'}})
 return route.fulfill({status:503,json:{detail:'QA: nguồn ngoài chưa kết nối'}})
})
const toggle=()=>page.getByRole('switch',{name:'Chế độ tối',exact:true}).filter({visible:true}).last()
async function setTheme(theme){if(await toggle().getAttribute('aria-checked')!==(theme==='dark'?'true':'false'))await toggle().click();await page.waitForFunction(t=>document.querySelector('.app-shell')?.dataset.theme===t&&document.documentElement.dataset.theme===t,theme)}
async function capture(name){for(const theme of ['dark','light']){await setTheme(theme);await page.screenshot({path:`${out}/${name}-${theme}.png`,animations:'disabled'});surfaces.push({name,theme,colors:await page.locator('main').first().evaluate(e=>({bg:getComputedStyle(e).backgroundColor,ink:getComputedStyle(e).color})),body:(await page.locator('body').innerText()).slice(0,1200)})}}
try {
 await page.goto('http://127.0.0.1:5190/dashboard-static/learn'); await page.locator('.lh-shell').waitFor()
 for (const [label,id,selector] of [['Sách & Tài liệu','library','.lh-doc-library'],['Kệ sách của tôi','shelf','.pl-library'],['Quanta Docs','docs','.qd-page-shell'],['Hỏi AI Tutor','tutor','.lh-tutor-container'],['CFA Mock','exam','.mock-room']]) {
   await page.goto('http://127.0.0.1:5190/dashboard-static/learn');await page.locator('.lh-shell').waitFor();
   await page.getByRole('tab',{name:label,exact:true}).click(); await page.locator(selector).waitFor(); await capture(id); checks.push(`${id}: both themes`)
 }
 await page.goto('http://127.0.0.1:5190/dashboard-static/learn');await page.getByRole('tab',{name:'Sách & Tài liệu',exact:true}).click();await page.getByRole('button',{name:'Theme QA PDF',exact:true}).click();await page.locator('.br-studio').waitFor()
 const notes=page.getByPlaceholder('Ghi chú khi đọc… ý chính, câu hỏi, số liệu cần nhớ.').first();await notes.fill('Theme QA: A4 note stays intact')
 const pdf=await page.locator('iframe.br-doc__frame').getAttribute('src'); const paper=await notes.evaluate(e=>getComputedStyle(e).color)
 await capture('reader');assert.equal(await notes.inputValue(),'Theme QA: A4 note stays intact');assert.equal(await notes.evaluate(e=>getComputedStyle(e).color),paper);assert.equal(await page.locator('iframe.br-doc__frame').getAttribute('src'),pdf);checks.push('Reader chrome follows theme; PDF frame and A4 note/ink retained')
 await page.goto('http://127.0.0.1:5190/dashboard-static/bctc');await page.locator('.bctc-lab-page').waitFor()
 await page.getByRole('tab',{name:'Notes',exact:true}).click();const note=page.getByLabel('Ghi chú BCTC');await note.fill('Theme QA: preserve draft');await capture('bctc-notes');assert.equal(await note.inputValue(),'Theme QA: preserve draft');checks.push('BCTC note draft retained')
 await page.getByRole('button',{name:'Bài tập thực hành',exact:true}).click();await page.locator('.rp-lab').waitFor();await capture('ratio-practice');checks.push('Ratio practice: both themes')
 await page.goto('http://127.0.0.1:5190/dashboard-static/bctc');await page.getByRole('button',{name:'Báo cáo chi tiết',exact:true}).click();await page.locator('.bctc-workspace').waitFor();await capture('bctc-research');checks.push('Detailed reports: both themes')
 await page.goto('http://127.0.0.1:5190/dashboard-static/simulation-lab');const editor=page.locator('.simlab-editor-textarea');await editor.waitFor();const original=await editor.inputValue();await editor.fill(original+'\n// Theme QA');
 await page.locator('.simlab-chart-main canvas').first().waitFor()
 await page.locator('.simlab-chart-main').evaluate(element=>{let f=element[Object.keys(element).find(k=>k.startsWith('__reactFiber$'))];while(f){let h=f.memoizedState;while(h&&typeof h==='object'){const current=h.memoizedState?.current;if(Array.isArray(current)&&typeof current[0]?.timeScale==='function'){window.__themeQaCharts=current;current[0].timeScale().setVisibleLogicalRange({from:40,to:90});return}h=h.next}f=f.return}throw Error('Live chart API not found')})
 await page.waitForFunction(()=>window.__themeQaCharts[0].timeScale().getVisibleLogicalRange()?.from===40)
 await capture('simulation-chart');assert.ok(await page.evaluate(()=>{const r=window.__themeQaCharts[0].timeScale().getVisibleLogicalRange();return Math.abs(r.from-40)<1&&Math.abs(r.to-90)<1}));checks.push('Simulation live chart retains zoom when theme changes');assert.equal(await editor.inputValue(),original+'\n// Theme QA');checks.push('Simulation code draft retained')
 for(const [name,id] of [['Visual Builder','builder'],['Quant Tearsheet','tearsheet']]){await page.getByRole('button',{name,exact:true}).click();await capture(id);checks.push(`${id}: both themes`)}
 await page.getByRole('button',{name:/AI Copilot/}).click();await page.screenshot({path:`${out}/copilot-modal-light.png`,animations:'disabled'});await page.getByRole('button',{name:'Đóng trợ lý',exact:true}).click();await setTheme('dark');await page.getByRole('button',{name:/AI Copilot/}).click();await page.screenshot({path:`${out}/copilot-modal-dark.png`,animations:'disabled'});checks.push('AI modal inherits both themes')
 assert.deepEqual(errors,[])
} finally {await writeFile(`${out}/subtabs.json`,JSON.stringify({checks,errors,surfaces},null,2));await browser.close()}
console.log(JSON.stringify({checks,errors}))
