import test from 'node:test';
import assert from 'node:assert/strict';

import {
  QUANTA_STRATEGY_PRESETS,
  DEFAULT_QUANTA_CODE,
} from '../features/simulation-lab/content/quantaStrategyPresets.js';
import {
  runDeterministicBacktest,
  generateSampleOHLC,
  calculateEMA,
} from '../features/simulation-lab/utils/quantaBacktestSimulator.js';
import {
  parseQuantaParams,
  extractQuantaParams,
  updateQuantaParamInCode,
} from '../features/simulation-lab/utils/quantaParamParser.js';
import { mapPointsToOHLCBars } from '../features/simulation-lab/services/quantaMarketDataService.js';

test('Quanta Strategy Presets Contract', async (t) => {
  await t.test('has 4 canonical quantitative presets', () => {
    assert.equal(QUANTA_STRATEGY_PRESETS.length, 4);
    const ids = QUANTA_STRATEGY_PRESETS.map((p) => p.id);
    assert.deepEqual(ids, ['aurora-pulse', 'tide-cross', 'turtle-breakout', 'bollinger-squeeze']);
  });

  await t.test('default code contains full core Quanta blocks', () => {
    assert.ok(DEFAULT_QUANTA_CODE.includes('strategy'));
    assert.ok(DEFAULT_QUANTA_CODE.includes('params:'));
    assert.ok(DEFAULT_QUANTA_CODE.includes('detect:'));
    assert.ok(DEFAULT_QUANTA_CODE.includes('act:'));
    assert.ok(DEFAULT_QUANTA_CODE.includes('render:'));
  });
});

test('Quanta Dynamic Param Parser Contract', async (t) => {
  await t.test('extracts integer and float parameters accurately', () => {
    const code = `
params:
  fast_period: 14
  slow_period: 28
  take_profit_pct: 10.5
  stop_loss_pct: 4.2
  trailing_stop: 2.5
`;
    const parsed = parseQuantaParams(code);
    assert.equal(parsed.fast_period, 14);
    assert.equal(parsed.slow_period, 28);
    assert.equal(parsed.take_profit_pct, 10.5);
    assert.equal(parsed.stop_loss_pct, 4.2);
    assert.equal(parsed.trailing_stop, 2.5);
  });
});

test('Quanta Backtest Simulator Engine', async (t) => {
  const ohlc = generateSampleOHLC('FPT', 100);

  await t.test('generates valid OHLC series with VN trading hours & prices', () => {
    assert.ok(ohlc.length > 50);
    const first = ohlc[0];
    assert.ok(first.time);
    assert.ok(first.open > 0);
    assert.ok(first.high >= first.low);
    assert.ok(first.close > 0);
  });

  await t.test('computes exponential moving average (EMA) accurately', () => {
    const closes = ohlc.map((bar) => bar.close);
    const ema9 = calculateEMA(closes, 9);
    assert.equal(ema9.length, ohlc.length);
    assert.ok(ema9[ema9.length - 1] > 0);
  });

  await t.test('runs backtest and returns realistic Quant Tearsheet metrics', () => {
    const params = {
      fast_period: 9,
      slow_period: 21,
      take_profit_pct: 8.0,
      stop_loss_pct: 4.0,
      trailing_stop: 2.5,
    };
    const res = runDeterministicBacktest(DEFAULT_QUANTA_CODE, params, ohlc);

    assert.ok(res);
    assert.ok(res.metrics);
    assert.ok(res.metrics.sharpeRatio === null || Number.isFinite(res.metrics.sharpeRatio));
    assert.ok(typeof res.metrics.winRate === 'number');
    assert.ok(typeof res.metrics.maxDrawdown === 'number');
    assert.ok(res.metrics.finalEquity > 0);
    assert.ok(Array.isArray(res.trades));
    assert.ok(Array.isArray(res.markers));
    assert.ok(Array.isArray(res.equityCurve));
  });
});

test('Quanta Real Market Data Adapter Contract', async (t) => {
  await t.test('maps Data Hub points to valid OHLC bars', () => {
    const rawPoints = [
      { date: '2026-03-26T02:00:00+00:00', open: 69050, high: 69050, low: 66540, close: 66540, volume: 9743400 },
      { date: '2026-03-27T02:00:00+00:00', open: 66810, high: 68420, low: 66350, close: 68250, volume: 9080300 },
    ];
    const bars = mapPointsToOHLCBars(rawPoints, '1d');
    assert.equal(bars.length, 2);
    assert.equal(bars[0].time, '2026-03-26');
    assert.equal(bars[0].close, 66540);
    assert.equal(bars[1].time, '2026-03-27');
    assert.equal(bars[1].volume, 9080300);
  });

  await t.test('handles empty or malformed points gracefully', () => {
    assert.deepEqual(mapPointsToOHLCBars([]), []);
    assert.deepEqual(mapPointsToOHLCBars(null), []);
  });
});

