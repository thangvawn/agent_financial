import test from 'node:test'
import assert from 'node:assert/strict'
import { runDeterministicBacktest, generateSyntheticOHLCV, calcEMA } from '../../features/simulation-lab/utils/quantaBacktestSimulator.js'
import { parseQuantaParams } from '../../features/simulation-lab/utils/quantaParamParser.js'
import { QUANTA_STRATEGY_PRESETS } from '../../features/simulation-lab/content/quantaStrategyPresets.js'
import { computeTodaySignal } from '../../features/simulation-lab/utils/quantaTodaySignalEngine.js'
import { mapPointsToOHLCBars } from '../../features/simulation-lab/services/quantaMarketDataService.js'
const bars = generateSyntheticOHLCV('HPG', 400)
const run = code => runDeterministicBacktest(code, parseQuantaParams(code), bars)
test('R03 different strategy rules produce different trades', () => {
  assert.notDeepEqual(run(QUANTA_STRATEGY_PRESETS[2].code).trades, run(QUANTA_STRATEGY_PRESETS[3].code).trades)
})
test('R03 unsupported strategy must fail instead of running EMA', () => {
  assert.throws(() => run('strategy "bad"\ndetect:\n  x = unsupported(close)\nact:\n  when x:\n    enter long with wnav 5pct\n  when position.is_long:\n    close long'), /hỗ trợ|cú pháp|không hợp lệ/i)
})
test('R04 flat equity has undefined risk ratios', () => {
  const flat = bars.map(b => ({ ...b, open: 100000, high: 100000, low: 100000, close: 100000 }))
  const res = runDeterministicBacktest('', {}, flat)
  assert.equal(res.metrics.sharpeRatio, null)
  assert.equal(res.metrics.sortinoRatio, null)
  assert.equal(res.metrics.cagr, 0)
})
test('R06 two latest closes cannot substitute for EMA history', () => {
  const data = bars.slice(0, 100).map((b, i) => ({ ...b, close: 200000 - i * 1000 }))
  data.at(-1).close = data.at(-2).close + 100
  assert.ok(calcEMA(data, 21).at(-1) < calcEMA(data, 55).at(-1))
  assert.notEqual(computeTodaySignal({ bars: data }).action, 'BUY')
})
test('R07 short history is never silently replaced with synthetic data', () => {
  assert.throws(() => runDeterministicBacktest('', {}, bars.slice(0, 20)), /dữ liệu|lịch sử|nến/i)
})
test('R09 hourly bars retain distinct ordered timestamps', () => {
  const out = mapPointsToOHLCBars([{ date: '2025-01-02T09:00:00Z', close: 100 }, { date: '2025-01-02T10:00:00Z', close: 101 }])
  assert.ok(out[0].time < out[1].time)
})
test('R11 trade PnL includes fees on both sides', () => {
  const result = run(QUANTA_STRATEGY_PRESETS[1].code)
  assert.ok(result.trades.length > 0)
  for (const t of result.trades.filter(t => t.exitDate)) {
    const expected = t.shares * (t.exitPrice * 0.9975 - t.entryPrice * 1.0015)
    assert.ok(Math.abs(t.pnl - expected) < 1, `${t.pnl} vs ${expected}`)
  }
})
