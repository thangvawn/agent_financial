import test from 'node:test';
import assert from 'node:assert/strict';
import {
  roundToVnPriceTick,
  calculatePriceBands,
  evaluateVnExecution,
  checkLiquidityStatus,
} from '../features/simulation-lab/utils/quantaVnMarketRules.js';
import { computeTodaySignal } from '../features/simulation-lab/utils/quantaTodaySignalEngine.js';
import { generateSyntheticOHLCV, runDeterministicBacktest } from '../features/simulation-lab/utils/quantaBacktestSimulator.js';

test('Quanta VN Market Rules Contract', async (t) => {
  await t.test('rounds prices according to Vietnamese tick sizes', () => {
    assert.equal(roundToVnPriceTick(8542), 8540); // < 10k: tick 10
    assert.equal(roundToVnPriceTick(26435), 26450); // 10k-50k: tick 50
    assert.equal(roundToVnPriceTick(135480), 135500); // >= 50k: tick 100
  });

  await t.test('calculates correct HOSE price bands (+-7%)', () => {
    const bands = calculatePriceBands(100000, 'HOSE');
    assert.equal(bands.refPrice, 100000);
    assert.equal(bands.ceilingPrice, 107000);
    assert.equal(bands.floorPrice, 93000);
  });

  await t.test('applies realistic slippage and tax/fees', () => {
    const buyExec = evaluateVnExecution(100000, true);
    assert.ok(buyExec.executionPrice >= 100000); // slippage up on buy
    assert.equal(buyExec.feePct, 0.15);

    const sellExec = evaluateVnExecution(100000, false);
    assert.ok(sellExec.executionPrice <= 100000); // slippage down on sell
    assert.equal(sellExec.feePct, 0.25); // 0.15% fee + 0.10% tax
  });

  await t.test('detects liquidity warnings accurately', () => {
    const safeBars = Array.from({ length: 20 }, () => ({ volume: 150000 }));
    assert.equal(checkLiquidityStatus(safeBars).isSafe, true);

    const illiquidBars = Array.from({ length: 20 }, () => ({ volume: 12000 }));
    assert.equal(checkLiquidityStatus(illiquidBars).isSafe, false);
    assert.equal(checkLiquidityStatus(illiquidBars).status, 'WARNING_ILLIQUID');
  });
});

test('Quanta Today Actionable Signal Engine Contract', async (t) => {
  await t.test('computes complete TodaySignal payload with stop-loss and take-profit', () => {
    const bars = generateSyntheticOHLCV('FPT', 60);
    const signal = computeTodaySignal({
      bars,
      params: { fast_len: 21, slow_len: 55 },
      trades: [],
    });

    assert.ok(signal);
    assert.ok(['BUY', 'SELL', 'HOLD', 'WAIT'].includes(signal.action));
    assert.ok(typeof signal.actionLabel === 'string');
    assert.ok(signal.currentPrice > 0);
    assert.ok(signal.stopLossPrice < signal.currentPrice);
    assert.ok(signal.takeProfitPrice > signal.currentPrice);
    assert.ok(signal.bands.ceilingPrice > signal.bands.floorPrice);
    assert.ok(signal.liquidity.status);
  });

  await t.test('runDeterministicBacktest includes todaySignal in output', () => {
    const bars = generateSyntheticOHLCV('HPG', 80);
    const result = runDeterministicBacktest('', { fast_len: 21, slow_len: 55 }, bars);

    assert.ok(result.todaySignal);
    assert.ok(result.todaySignal.currentPrice > 0);
    assert.ok(result.todaySignal.action);
  });
});
