import test from 'node:test'
import assert from 'node:assert/strict'
import { loadWorkbookState, saveWorkbookState, workbookKey, emptyWorkbook } from '../../features/bctc/services/workbookState.js'
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
