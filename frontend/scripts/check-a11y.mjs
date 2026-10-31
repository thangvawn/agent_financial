// A bounded DOM smoke check, not a WCAG conformance audit.
import { chromium } from 'playwright'
const targets=process.argv.slice(2)
if(!targets.length && process.env.A11Y_URL) targets.push(process.env.A11Y_URL)
if(!targets.length) {console.error('Provide A11Y_URL or page URLs to check against a running local app.');process.exit(1)}
const browser=await chromium.launch({headless:true})
let count=0
try {
 for(const url of targets) {
  const page=await browser.newPage()
  const response=await page.goto(url,{waitUntil:'networkidle'})
  if(!response?.ok()) throw new Error(`Cannot check ${url}: HTTP ${response?.status()}`)
  const errors=await page.evaluate(()=>{
   const failures=[]
   if(!document.documentElement.lang) failures.push('Document lacks lang')
   if(!document.title.trim()) failures.push('Document lacks title')
   const visible=e=>!!(e.getClientRects().length)&&getComputedStyle(e).visibility!=='hidden'
   const name=e=>e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')?.split(/\s+/).map(id=>document.getElementById(id)?.textContent||'').join(' ')||e.labels?.[0]?.textContent||e.getAttribute('title')||e.textContent
   for(const e of document.querySelectorAll('button,a[href],input:not([type=hidden]),select,textarea')) {
    if(visible(e)&&!name(e)?.trim())failures.push(`Unnamed ${e.tagName.toLowerCase()} ${e.id||e.className}`)
   }
   for(const e of document.querySelectorAll('img'))if(visible(e)&&!e.hasAttribute('alt'))failures.push(`Image without alt: ${e.getAttribute('src')}`)
   return failures
  })
  count+=errors.length;console.log(url, errors.length?'FAIL':'PASS',errors)
  await page.close()
 }
} finally {await browser.close()}
console.log('Checked document metadata, visible control names and image alt presence. Keyboard, contrast and full WCAG audit are outside this smoke check.')
process.exitCode=count?1:0
