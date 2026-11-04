/**
 * Market Data Service with Intraday Time-Series Generator & Realtime Stream
 * Strictly adheres to < 200 lines limit.
 */

import { MarketIndex, IndexPricePoint } from '../types/market';

function generateIntradayTimeSeries(
  symbol: string,
  currentPrice: number,
  referencePrice: number,
  pointsCount = 40
): IndexPricePoint[] {
  const result: IndexPricePoint[] = [];
  const baseTime = new Date();
  baseTime.setHours(9, 15, 0, 0);
  const startTs = baseTime.getTime();
  const stepMs = 6 * 60 * 1000; // mỗi điểm cách 6 phút

  const isPos = currentPrice >= referencePrice;
  const deltaTotal = currentPrice - referencePrice;
  const seed = (symbol.charCodeAt(0) * 19 + symbol.charCodeAt(symbol.length - 1) * 37) % 100;

  for (let i = 0; i < pointsCount; i++) {
    const t = startTs + i * stepMs;
    const progress = i / (pointsCount - 1);
    let p: number;

    if (symbol === 'UPCOM') {
      // UPCOM: đầu phiên phẳng sát tham chiếu, sau đó bật tăng mạnh
      if (i < 10) {
        p = referencePrice + (deltaTotal * 0.05) + (((i % 3) - 1) * 0.04);
      } else if (i === 10 || i === 11) {
        p = referencePrice + deltaTotal * (0.4 + (i - 10) * 0.4);
      } else {
        const jitter = Math.sin(i * 1.5 + seed) * 0.06 + (((i % 4) - 2) * 0.02);
        p = currentPrice + jitter;
      }
    } else {
      // Các chỉ số giảm (VNINDEX, VN30, HNX30)
      const slope = referencePrice + (deltaTotal * progress);
      const wave = Math.sin(progress * Math.PI * 3 + seed) * (Math.abs(deltaTotal) * 0.18);
      const noise = ((i % 5) - 2) * (Math.abs(deltaTotal) * 0.04);
      p = slope + wave + noise;
    }

    if (i === pointsCount - 1) p = currentPrice;
    if (i === 0) p = referencePrice + (deltaTotal * 0.05);

    result.push({ timestamp: t, price: Number(p.toFixed(2)) });
  }

  return result;
}

export const INITIAL_MARKET_INDICES: MarketIndex[] = [
  {
    symbol: 'VNINDEX',
    name: 'VN-Index',
    currentPrice: 1720.98,
    referencePrice: 1735.09,
    change: -14.11,
    changePercent: -0.81,
    volume: 470.35,
    turnover: 10645.09,
    advances: 154,
    ceil: 4,
    unchanged: 60,
    declines: 148,
    floor: 6,
    history: generateIntradayTimeSeries('VNINDEX', 1720.98, 1735.09),
    updatedAt: Date.now(),
    isDemo: true
  },
  {
    symbol: 'VN30',
    name: 'VN30-Index',
    currentPrice: 1869.38,
    referencePrice: 1873.43,
    change: -4.05,
    changePercent: -0.22,
    volume: 230.10,
    turnover: 6695.07,
    advances: 13,
    ceil: 0,
    unchanged: 2,
    declines: 15,
    floor: 0,
    history: generateIntradayTimeSeries('VN30', 1869.38, 1873.43),
    updatedAt: Date.now(),
    isDemo: true
  },
  {
    symbol: 'HNX30',
    name: 'HNX30-Index',
    currentPrice: 431.70,
    referencePrice: 432.43,
    change: -0.73,
    changePercent: -0.17,
    volume: 24.59,
    turnover: 415.71,
    advances: 11,
    ceil: 1,
    unchanged: 4,
    declines: 13,
    floor: 0,
    history: generateIntradayTimeSeries('HNX30', 431.70, 432.43),
    updatedAt: Date.now(),
    isDemo: true
  },
  {
    symbol: 'UPCOM',
    name: 'UPCoM-Index',
    currentPrice: 124.73,
    referencePrice: 124.24,
    change: 0.49,
    changePercent: 0.39,
    volume: 17.41,
    turnover: 326.40,
    advances: 105,
    ceil: 14,
    unchanged: 79,
    declines: 77,
    floor: 9,
    history: generateIntradayTimeSeries('UPCOM', 124.73, 124.24),
    updatedAt: Date.now(),
    isDemo: true
  }
];

export function getInitialMarketIndices(): MarketIndex[] {
  return INITIAL_MARKET_INDICES.map((item) => ({
    ...item,
    history: [...item.history]
  }));
}

export function subscribeMarketIndices(callback: (indices: MarketIndex[]) => void): () => void {
  let state = getInitialMarketIndices();
  callback(state);

  const timer = setInterval(() => {
    state = state.map((item) => {
      // Nhẹ nhàng thêm 1 bước biến thiên nhỏ cho điểm hiện tại
      const microJitter = ((Math.random() - 0.48) * 0.15);
      const newPrice = Number((item.currentPrice + microJitter).toFixed(2));
      const newChange = Number((newPrice - item.referencePrice).toFixed(2));
      const newPct = Number(((newChange / item.referencePrice) * 100).toFixed(2));
      const now = Date.now();

      // Cập nhật điểm giá mới vào cuối mảng history mà không làm mất dữ liệu cũ
      const lastHistory = item.history[item.history.length - 1];
      let nextHistory = [...item.history];

      if (lastHistory && now - lastHistory.timestamp < 30000) {
        // Cập nhật điểm cuối nếu trong cùng cửa sổ 30s
        nextHistory[nextHistory.length - 1] = { timestamp: now, price: newPrice };
      } else {
        // Đẩy điểm mới
        nextHistory.push({ timestamp: now, price: newPrice });
        if (nextHistory.length > 60) nextHistory = nextHistory.slice(-60);
      }

      return {
        ...item,
        currentPrice: newPrice,
        change: newChange,
        changePercent: newPct,
        history: nextHistory,
        updatedAt: now
      };
    });

    callback(state);
  }, 2500);

  return () => clearInterval(timer);
}
