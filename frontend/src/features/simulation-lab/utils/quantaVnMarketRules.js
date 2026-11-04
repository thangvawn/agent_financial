/**
 * quantaVnMarketRules.js
 * Vietnam Stock Market Trading Rules & Settlement Mechanics.
 * Strict quantitative enforcement: Price bands, Ticks, Tax, Fees, Slippage.
 */

export const VN_EXCHANGE_LIMITS = {
  HOSE: 0.07,
  HSX: 0.07,
  HNX: 0.10,
  UPCOM: 0.15,
};

export const VN_FEES = {
  COMMISSION_PCT: 0.15, // 0.15% phi moi gioi
  SELL_TAX_PCT: 0.10,    // 0.10% thue ban
  SLIPPAGE_PCT: 0.15,    // 0.15% uoc tinh truot gia khop lenh
};

export function roundToVnPriceTick(price) {
  const p = Math.round(Number(price) || 0);
  if (p <= 0) return 0;
  if (p < 10000) return Math.round(p / 10) * 10;
  if (p < 50000) return Math.round(p / 50) * 50;
  return Math.round(p / 100) * 100;
}

export function calculatePriceBands(refPrice, exchange = 'HOSE') {
  const limitPct = VN_EXCHANGE_LIMITS[exchange] || 0.07;
  const rawCeil = refPrice * (1 + limitPct);
  const rawFloor = refPrice * (1 - limitPct);
  return {
    refPrice: roundToVnPriceTick(refPrice),
    ceilingPrice: roundToVnPriceTick(rawCeil),
    floorPrice: roundToVnPriceTick(rawFloor),
  };
}

export function evaluateVnExecution(rawPrice, isBuy = true) {
  const basePrice = Number(rawPrice) || 0;
  const slippageMul = isBuy ? (1 + VN_FEES.SLIPPAGE_PCT / 100) : (1 - VN_FEES.SLIPPAGE_PCT / 100);
  const executionPrice = roundToVnPriceTick(basePrice * slippageMul);
  const feePct = isBuy ? VN_FEES.COMMISSION_PCT : (VN_FEES.COMMISSION_PCT + VN_FEES.SELL_TAX_PCT);
  return {
    basePrice,
    executionPrice,
    feePct,
    slippagePct: VN_FEES.SLIPPAGE_PCT,
  };
}

export function checkLiquidityStatus(bars = [], window = 20) {
  if (!Array.isArray(bars) || bars.length === 0) {
    return { status: 'UNKNOWN', avgVolume: 0, isSafe: true };
  }
  const slice = bars.slice(-window);
  const totalVol = slice.reduce((sum, b) => sum + (Number(b.volume) || 0), 0);
  const avgVolume = Math.round(totalVol / Math.max(1, slice.length));
  const isSafe = avgVolume >= 50000;
  return {
    status: isSafe ? 'SAFE' : 'WARNING_ILLIQUID',
    avgVolume,
    isSafe,
  };
}
