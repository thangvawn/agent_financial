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
try{
 for(const [route,name,selector] of [['global-terminal','market','.mp-desk'],['learn','learn','.lh-shell'],['bctc','bctc','.bctc-lab-page'],['news','news','.news-desk'],['news/social','social','.social-desk'],['news/economic-calendar','calendar','.news-desk'],['simulation-lab','simulation','.quanta-simulation-lab'],['backtest-studio','backtest','.quanta-simulation-lab']]){
  await page.goto(`http://127.0.0.1:5190/dashboard-static/${route}`);await page.locator(selector).waitFor();await capture(name);checks.push(`${name}: both themes and shared control`)
 }
 await page.goto('http://127.0.0.1:5190/dashboard-static/learn');await page.locator('.lh-shell').waitFor()
 await page.setViewportSize({width:390,height:844});await capture('learn-mobile')
 checks.push('mobile theme control visible')
 assert.deepEqual(errors,[])
}finally{await writeFile(`${out}/checks.json`,JSON.stringify({checks,errors,surfaces},null,2));await browser.close()}
console.log(JSON.stringify({checks,errors}))
