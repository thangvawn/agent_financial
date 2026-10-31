import test from 'node:test'
import assert from 'node:assert/strict'
import { ema, sma, rsi, atr, indicator } from '../../features/simulation-lab/utils/quantaIndicators.js'
import { parseExpression, applyBinary } from '../../features/simulation-lab/utils/quantaExpression.js'
import { compileStrategy, emaStrategy } from '../../features/simulation-lab/utils/quantaStrategy.js'
import { performanceMetrics } from '../../features/simulation-lab/utils/quantaMetrics.js'
import { runDeterministicBacktest, generateSyntheticOHLCV } from '../../features/simulation-lab/utils/quantaBacktestSimulator.js'
import { computeTodaySignal } from '../../features/simulation-lab/utils/quantaTodaySignalEngine.js'
import { loadQuantaMarketBars, mapPointsToOHLCBars } from '../../features/simulation-lab/services/quantaMarketDataService.js'
const bars=Array.from({length:100},(_,i)=>({time:new Date(Date.UTC(2025,0,i+1)).toISOString().slice(0,10),open:100000,high:102000,low:98000,close:100000,volume:200000}))
const simple = condition => `strategy "Fixture"\ndetect:\n  c = market.close\nact:\n  when ${condition} and not position.is_long:\n    enter long with wnav 50pct\n  when position.is_long and c < 99000:\n    close long`
test('indicators agree with hand computed values',()=>{
  assert.deepEqual(ema([10,20,30],3),[10,15,22.5])
  assert.deepEqual(sma([10,20,30],2),[null,15,25])
  assert.equal(rsi([10,11,12,13],2).at(-1),100)
  assert.equal(rsi([10,10,10,10],2).at(-1),50)
  assert.equal(rsi([13,12,11,10],2).at(-1),0)
  assert.equal(atr([11,12,13],[9,10,11],[10,11,12],2).at(-1),2)
  assert.deepEqual(indicator('donchian',[[10,20,30],[8,18,28],[2,2,2]]).at(-1),{upper:30,lower:18})
  const bb=indicator('bbands',[[10,20,30],[3,3,3],[2,2,2]]).at(-1)
  assert.ok(Math.abs(bb.upper-(20+2*Math.sqrt(200/3)))<1e-10)
  assert.equal(bb.middle,20)
  assert.throws(()=>indicator('sma',[[1,2],[0,0]]),/Chu kỳ/)
  assert.throws(()=>indicator('evil',[[1]]),/hỗ trợ/)
})
test('metrics use calendar CAGR, drawdown and sampled excess returns',()=>{
  const eq=[{time:'2024-01-01',equity:100},{time:'2024-07-01',equity:120},{time:'2025-01-01',equity:90}]
  const m=performanceMetrics(eq,[],100,{interval:'1wk',riskFreeRate:0})
  assert.equal(m.maxDrawdown,25)
  assert.ok(Math.abs(m.totalReturnPct+10)<1e-10)
  assert.ok(Math.abs(m.cagr-((0.9**(365.25/366)-1)*100))<1e-10)
  const mean=(0.2-0.25)/2,sd=Math.sqrt(((0.2-mean)**2+(-0.25-mean)**2))
  assert.ok(Math.abs(m.sharpeRatio-mean/sd*Math.sqrt(52))<1e-10)
  assert.ok(Math.abs(m.sortinoRatio-mean/Math.sqrt(0.25**2/2)*Math.sqrt(52))<1e-10)
  assert.equal(m.profitFactor,null)
  assert.throws(()=>performanceMetrics(eq,[],100,{interval:'invalid'}),/thời gian/)
})
test('user edits affect rules; execution waits for next bar, and fees reconcile',()=>{
  const data=bars.slice(0,10).map(b=>({...b}))
  data[3].close=101000;data[4].open=101500;data[6].close=98000;data[7].open=98500
  const result=runDeterministicBacktest(simple('c > 100500'),{},data)
  assert.equal(result.trades[0].entryDate,data[4].time)
  assert.equal(result.trades[0].entryPrice,101500)
  assert.equal(result.trades[0].exitDate,data[7].time)
  assert.equal(result.metrics.finalEquity,100000000+result.trades[0].pnl)
  assert.equal(runDeterministicBacktest(simple('c > 200000'),{},data).trades.length,0)
  const open=runDeterministicBacktest(simple('c > 99999'),{},bars.slice(0,10))
  assert.ok(open.openPosition)
  assert.equal(open.todaySignal.action,'HOLD')
  assert.equal(open.todaySignal.confidenceScore,null)
  assert.equal(open.todaySignal.stopLossPrice,null)
})
test('compiler rejects unsupported syntax, cycles and invalid parameters',()=>{
  for(const code of [simple('evil'),simple('c > 0').replace('c = market.close','c = c + 1'),simple('c > 0').replace('50pct','200pct'),simple('c > 0').replace('detect:','unknown:'),simple('c > 0').replace('c = market.close','c = market.secret'),simple('c > 0').replace('c = market.close','c = ema(market.close, 0)'),simple('c > 0').replace('c = market.close','c = position.is_long')]) assert.throws(()=>compileStrategy(code,bars))
  assert.throws(()=>parseExpression('globalThis.x=1'))
  assert.throws(()=>parseExpression('market.close[-1]'))
  assert.throws(()=>parseExpression('(1+2'))
  assert.throws(()=>parseExpression('1 2'))
  assert.equal(applyBinary('/',1,0),null)
  assert.equal(applyBinary('>',null,0),null)
  assert.equal(applyBinary('crossunder',1,2,3,2),true)
  assert.equal(applyBinary('crossover',1,2,null,2),null)
  assert.equal(applyBinary('==',2,2),true)
  assert.equal(applyBinary('!=',1,2),true)
  assert.equal(applyBinary('%',5,2),1)
  assert.equal(applyBinary('>=',2,2),true)
  assert.equal(applyBinary('<=',1,2),true)
  assert.equal(applyBinary('-',2,1),1)
  assert.equal(applyBinary('+',2,1),3)
  assert.equal(applyBinary('*',2,3),6)
})
test('numeric timestamps, gaps and malformed history cannot silently change sources',async()=>{
  const hourly=bars.slice(0,60).map((b,i)=>({...b,time:Date.UTC(2025,0,2,9+i)/1000}))
  assert.equal(runDeterministicBacktest('',{},hourly,{interval:'1h'}).bars.length,60)
  assert.throws(()=>runDeterministicBacktest('',{},[...bars,bars[0]]),/thời gian/)
  assert.deepEqual(mapPointsToOHLCBars([null,{date:'bad',close:10},{date:'2025-01-01',close:0}]),[])
  assert.throws(()=>mapPointsToOHLCBars([{date:'2025-01-01',close:10},{date:'2025-01-01',close:10}]),/trùng/)
  const original=globalThis.fetch
  try {
    globalThis.fetch=async()=>({ok:true,json:async()=>({points:bars.slice(0,20),source:'fixture'})})
    const feed=await loadQuantaMarketBars('HPG','1y','1h');assert.equal(feed.count,20);assert.equal(feed.ticker,'HPG'); assert.equal(typeof feed.firstDate,'string')
    assert.throws(()=>runDeterministicBacktest('',{},feed.bars),/nến/)
    globalThis.fetch=async()=>{throw new Error('offline')}
    await assert.rejects(loadQuantaMarketBars('VCB'),/offline/)
  } finally {globalThis.fetch=original}
})
test('signal handles actual open positions and long EMA history',()=>{
  assert.equal(computeTodaySignal({bars:[]}),null)
  const data=generateSyntheticOHLCV('HPG',200)
  const strategy=compileStrategy(emaStrategy(),data)
  assert.ok(strategy.warmup>=50)
  const signal=computeTodaySignal({bars:data,openPosition:{entryPrice:25000},params:{stop_loss_pct:4,take_profit_pct:8}})
  assert.ok(['HOLD','SELL'].includes(signal.action))
  assert.equal(signal.stopLossPrice,24000)
  assert.equal(signal.takeProfitPrice,27000)
})
