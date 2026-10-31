import test from 'node:test'
import assert from 'node:assert/strict'
import { loadWorkbookState, saveWorkbookState, workbookKey, emptyWorkbook } from '../../features/bctc/services/workbookState.js'
import { filterStocks } from '../../features/market-portfolio/services/stockFilters.js'
import { logoutSession } from '../../features/auth/services/sessionLifecycle.js'
const memory = () => { const m = new Map(); return { getItem: k => m.get(k) || null, setItem: (k,v) => m.set(k,v), removeItem: k=>m.delete(k) } }
test('R08 never load another owner cache', async () => {
  const storage = memory()
  storage.setItem('northstar:bctc:model:HPG', JSON.stringify({ owner: 'a', notes: 'secret' }))
  storage.setItem(workbookKey('b','HPG'), JSON.stringify({ owner: 'a', notes: 'secret' }))
  const result = await loadWorkbookState({ owner: 'b', ticker: 'HPG', storage, load: async()=>{throw new Error('offline')} })
  assert.equal(result.model.notes, '')
})
test('R10 absent model returns clean state and starts at revision zero', async () => {
  const result = await loadWorkbookState({ owner: 'a', ticker: 'VCB', storage: memory(), load: async()=>null })
  assert.equal(result.model.revision, 0)
  assert.equal(result.model.notes, '')
})
test('R10 revision conflict must not be reported as offline save', async () => {
  const storage = memory()
  await assert.rejects(saveWorkbookState({ owner:'a', ticker:'HPG', storage, model:emptyWorkbook(), save:async()=>{throw Object.assign(new Error('conflict'),{status:409})} }), /conflict/)
  assert.ok(storage.getItem(workbookKey('a','HPG')), '409 preserves draft for explicit recovery')
})
test('R05 false financial and technical matches are excluded', () => {
  const items=[{symbol:'X',price:50,change_pct:4,dividend_yield:0,pe:100,roe:1,ma20:100,rsi:20,volume:1}]
  for(const preset of ['high_dividend','value_investing','money_inflow','vcp_pattern']) assert.equal(filterStocks(items,{preset}).items.length,0)
  for(const technical of ['above_ma20','rsi_overbought','vol_2x_ma20']) assert.equal(filterStocks(items,{technical}).items.length,0)
})
test('R05 missing fields are unknown, not zero or a positive match', () => {
  const result=filterStocks([{symbol:'X',price:50,change_pct:4}],{preset:'high_dividend'})
  assert.deepEqual(result.items,[])
  assert.equal(result.unavailable,1)
})
test('R12 logout sends saved token before clearing local session', async () => {
  const storage=memory();storage.setItem('public-beta.session_id','review-session')
  let called=false
  await logoutSession({storage,fetchImpl:async(url,options)=>{
    assert.equal(url,'/api/v1/public/auth/logout')
    assert.equal(options.headers.Authorization,'Bearer review-session')
    assert.equal(storage.getItem('public-beta.session_id'),'review-session')
    called=true;return {ok:true,status:200}
  }})
  assert.ok(called);assert.equal(storage.getItem('public-beta.session_id'),null)
})
test('workbook offline save restores only the same owner and ticker', async () => {
  const storage=memory(),model={...emptyWorkbook(),notes:'my draft',revision:3}
  const offline=async()=>{throw new Error('offline')}
  const result=await saveWorkbookState({owner:'a',ticker:'HPG',storage,model,save:offline})
  assert.ok(result.offline)
  assert.equal((await loadWorkbookState({owner:'a',ticker:'HPG',storage,load:offline})).model.notes,'my draft')
  assert.equal((await loadWorkbookState({owner:'b',ticker:'HPG',storage,load:offline})).model.notes,'')
  const online=await saveWorkbookState({owner:'a',ticker:'HPG',storage,model,save:async()=>({model:{...model,revision:4}})})
  assert.equal(online.model.revision,4)
  assert.equal(storage.getItem(workbookKey('a','HPG')),null)
  await assert.rejects(loadWorkbookState({owner:'a',ticker:'HPG',storage,load:async()=>{throw Object.assign(new Error('unauthorized'),{status:401})}}),/unauthorized/)
})
test('logout failures preserve credential for retry, expired session can be cleared',async()=>{
  const storage=memory();storage.setItem('public-beta.session_id','review-session')
  await assert.rejects(logoutSession({storage,fetchImpl:async()=>({ok:false,status:503})}),/thu hồi/)
  assert.equal(storage.getItem('public-beta.session_id'),'review-session')
  await logoutSession({storage,fetchImpl:async()=>({ok:false,status:401})})
  assert.equal(storage.getItem('public-beta.session_id'),null)
  await logoutSession({storage,fetchImpl:async()=>{throw new Error('must not call')}})
})
test('filters require actual matching data and preserve unknowns',()=>{
  const items=[{symbol:'MATCH',price:200,ma20:190,ma50:180,ma200:170,dividend_yield_pct:9,consecutive_cash_dividend_years:3,
    foreign_net_buy_streak:4,rsi:80,volume:300,volume_ma20:100,prior_high_20:195,high:204,low:190,ref_price:200,industry:'Ngân hàng'}]
  for(const preset of ['breakout','strong_trend','money_inflow','high_dividend','regular_cash_div','foreign_favorite']) assert.equal(filterStocks(items,{preset}).items.length,1)
  for(const technical of ['above_ma20','above_ma50','above_ma200','rsi_overbought','vol_2x_ma20','high_volatility']) assert.equal(filterStocks(items,{technical}).items.length,1)
  assert.equal(filterStocks(items,{technical:'rsi_oversold'}).items.length,0)
  assert.equal(filterStocks(items,{sector:'Dầu khí'}).items.length,0)
  assert.equal(filterStocks(items,{sector:'Ngân hàng'}).items.length,1)
  assert.equal(filterStocks([{price:100,ma20:null}],{technical:'above_ma20'}).unavailable,1)
})
