import test from 'node:test'
import assert from 'node:assert/strict'
import {runQuantaSimulation} from '../../features/simulation-lab/utils/quantaBacktestSimulator.js'
import {compileStrategy} from '../../features/simulation-lab/utils/quantaStrategy.js'
import {rsi,sma} from '../../features/simulation-lab/utils/quantaIndicators.js'
import {applyBinary} from '../../features/simulation-lab/utils/quantaExpression.js'
import {emptyWorkbook,loadWorkbookState,saveWorkbookState,workbookKey} from '../../features/bctc/services/workbookState.js'
import {saveBlueprint,loadSavedBlueprints} from '../../features/simulation-lab/services/quantaBlueprintStorage.js'
const bars=Array.from({length:50},(_,i)=>({time:new Date(Date.UTC(2025,0,1+i)).toISOString().slice(0,10),open:10000,high:10100,low:9900,close:10000,volume:100000}))
const code=condition=>`strategy "QA"\ndetect:\n  bullish = market.close > 9000\nact:\n  when ${condition} and not position.is_long:\n    enter long with wnav 50pct\n  when position.is_long and market.close < 1:\n    close long`
const storage=()=>{const data=new Map();return {getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)}}
test('boolean equality is equivalent and unknown remains unknown',()=>{
 assert.equal(applyBinary('==',true,true),true)
 assert.equal(applyBinary('!=',true,false),true)
 assert.equal(applyBinary('==',null,null),null)
 assert.equal(runQuantaSimulation({bars,code:code('bullish')}).openPosition.entryDate,runQuantaSimulation({bars,code:code('bullish == true')}).openPosition.entryDate)
})
test('history and nested indicators contribute to required warmup',()=>{
 assert.throws(()=>runQuantaSimulation({bars,code:code('not (market.close > market.close[100])')}),/lịch sử/)
 assert.ok(compileStrategy(code('rsi(sma(market.close, 30), 30) > 50'),bars).warmup>=59)
 assert.equal(compileStrategy(code('not (market.close > market.close[100])'),bars).signal(5,{}),null)
})
test('RSI does not treat gaps as zero prices and resets smoothing after gaps',()=>{
 const x=rsi(sma(bars.map(b=>b.close),5),5)
 assert.equal(x[8],null);assert.equal(x[9],50);assert.equal(x[20],50)
 assert.deepEqual(rsi([1,2,3,null,3,3,3],2),[null,null,100,null,null,null,50])
})
test('newer offline workbook survives reconnection and keeps original base revision',async()=>{
 const s=storage(),draft={...emptyWorkbook(),revision:2,notes:'new draft'}
 await saveWorkbookState({owner:'A',ticker:'FPT',storage:s,model:draft,save:async()=>{throw new Error('offline')}})
 const loaded=await loadWorkbookState({owner:'A',ticker:'FPT',storage:s,load:async()=>({model:{...emptyWorkbook(),revision:2,notes:'old server'}})})
 assert.equal(loaded.model.notes,'new draft');assert.equal(loaded.restoredDraft,true)
 const conflict=await loadWorkbookState({owner:'A',ticker:'FPT',storage:s,load:async()=>({model:{...emptyWorkbook(),revision:3,notes:'changed elsewhere'}})})
 assert.equal(conflict.model.revision,2);assert.equal(conflict.conflict,true)
 await assert.rejects(saveWorkbookState({owner:'A',ticker:'FPT',storage:s,model:draft,save:async()=>{throw Object.assign(new Error('conflict'),{status:409})}}))
 assert.ok(s.getItem(workbookKey('A','FPT')))
})
test('saved strategies are private to account and survive new session for same owner',()=>{
 globalThis.window={localStorage:storage()}
 saveBlueprint({name:'A only',code:code('bullish')},'A')
 assert.equal(loadSavedBlueprints('B').length,0)
 assert.equal(loadSavedBlueprints('A')[0].name,'A only')
 delete globalThis.window
})
