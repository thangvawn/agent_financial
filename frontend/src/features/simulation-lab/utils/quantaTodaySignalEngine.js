/**
 * quantaTodaySignalEngine.js
 * Generates Today's Actionable Signal (BUY / SELL / HOLD) based on the latest candle.
 */
import { roundToVnPriceTick, calculatePriceBands, checkLiquidityStatus } from './quantaVnMarketRules.js';

export function computeTodaySignal({ bars = [], params = {}, trades = [] }) {
  if (!Array.isArray(bars) || bars.length < 10) {
    return null;
  }

  const latestBar = bars[bars.length - 1];
  const prevBar = bars[bars.length - 2] || latestBar;
  const currentPrice = Number(latestBar.close || latestBar.price || 0);

  const fastLen = Number(params.fast_len || params.fast_period || 21);
  const slowLen = Number(params.slow_len || params.slow_period || 55);

  // Check last trade state
  const lastTrade = trades.length > 0 ? trades[trades.length - 1] : null;
  const inPosition = Boolean(lastTrade && !lastTrade.exitDate);

  // Fast & Slow EMA on latest bar
  const kFast = 2 / (fastLen + 1);
  const kSlow = 2 / (slowLen + 1);
  const prevClose = Number(prevBar.close || currentPrice);
  const estFastEma = prevClose * (1 - kFast) + currentPrice * kFast;
  const estSlowEma = prevClose * (1 - kSlow) + currentPrice * kSlow;

  const isCrossUp = estFastEma > estSlowEma && Number(prevBar.close) <= estSlowEma;
  const isCrossDown = estFastEma < estSlowEma;

  let action = 'WAIT';
  let actionLabel = 'CHỜ TÍN HIỆU MỚI';
  let color = 'slate';
  let rationale = `Đang theo dõi biến động quanh EMA(${fastLen}).`;

  const stopLoss = roundToVnPriceTick(currentPrice * 0.94);
  const takeProfit = roundToVnPriceTick(currentPrice * 1.12);

  if (inPosition) {
    const entryPrice = lastTrade?.entryPrice || currentPrice;
    const unrealizedPnl = (((currentPrice - entryPrice) / entryPrice) * 100).toFixed(2);
    if (isCrossDown || currentPrice <= stopLoss) {
      action = 'SELL';
      actionLabel = currentPrice <= stopLoss ? 'BÁN CẮT LỖ (STOP-LOSS)' : 'BÁN CHỐT VỊ THẾ';
      color = 'rose';
      rationale = `Tín hiệu đảo chiều. Vị thế hiện tại đang ghi nhận ${unrealizedPnl}%.`;
    } else {
      action = 'HOLD';
      actionLabel = 'TIẾP TỤC NẮM GIỮ';
      color = 'amber';
      rationale = `Vị thế mở từ ${lastTrade.entryDate} @ ${entryPrice.toLocaleString('vi-VN')} đ (Lãi thả nổi: ${unrealizedPnl}%).`;
    }
  } else if (isCrossUp) {
    action = 'BUY';
    actionLabel = 'MUA MỚI (BUY SIGNAL)';
    color = 'emerald';
    rationale = `EMA(${fastLen}) vừa cắt lên EMA(${slowLen}). Xuất hiện xung lực bứt phá.`;
  }

  const bands = calculatePriceBands(currentPrice);
  const liquidity = checkLiquidityStatus(bars);

  return {
    action,
    actionLabel,
    color,
    asOfDate: latestBar.time,
    currentPrice: roundToVnPriceTick(currentPrice),
    stopLossPrice: stopLoss,
    takeProfitPrice: takeProfit,
    riskRewardRatio: 2.0,
    confidenceScore: inPosition ? 78 : isCrossUp ? 88 : 65,
    rationale,
    bands,
    liquidity,
  };
}
