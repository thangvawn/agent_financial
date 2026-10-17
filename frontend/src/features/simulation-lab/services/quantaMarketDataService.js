import { fetchInstrumentHistory } from '../../market-portfolio/services/dataHubApi.js';
import { generateSyntheticOHLCV } from '../utils/quantaBacktestSimulator.js';

export function mapPointsToOHLCBars(points = []) {
  if (!Array.isArray(points) || points.length === 0) return [];

  return points
    .filter((p) => p && (p.date || p.time) && (p.close !== undefined || p.price !== undefined))
    .map((p) => {
      const rawDate = p.date || p.time || '';
      const timeStr = String(rawDate).split('T')[0];
      const closeVal = Number(p.close ?? p.price ?? 0);
      const openVal = Number(p.open ?? p.price ?? closeVal);
      const highVal = Number(p.high ?? Math.max(openVal, closeVal));
      const lowVal = Number(p.low ?? Math.min(openVal, closeVal));
      const volumeVal = Number(p.volume ?? 0);

      return {
        time: timeStr,
        open: Math.round(openVal),
        high: Math.round(highVal),
        low: Math.round(lowVal),
        close: Math.round(closeVal),
        volume: Math.round(volumeVal),
      };
    })
    .filter((b) => b.time && b.close > 0)
    .sort((a, b) => (a.time > b.time ? 1 : -1));
}

const PERIOD_DAYS_MAP = {
  '3mo': 65,
  '6mo': 130,
  '1y': 250,
  '2y': 500,
  '3y': 750,
  '5y': 1250,
  '10y': 2500,
  'max': 3500,
};

export async function loadQuantaMarketBars(ticker = 'FPT', period = '1y', interval = '1d') {
  try {
    const rawData = await fetchInstrumentHistory(ticker, { period, interval });
    if (rawData && Array.isArray(rawData.points) && rawData.points.length >= 10) {
      const bars = mapPointsToOHLCBars(rawData.points);
      if (bars.length >= 10) {
        return {
          bars,
          source: rawData.source || 'vnstock',
          asOf: rawData.as_of || new Date().toISOString(),
          isReal: true,
          count: bars.length,
          ticker: ticker.toUpperCase(),
          firstDate: bars[0]?.time,
          lastDate: bars[bars.length - 1]?.time,
          period,
          interval,
        };
      }
    }
  } catch (err) {
    console.warn(`[QuantaData] Khong the tai data that cho ${ticker}, dung fallback:`, err?.message);
  }

  const fallbackCount = PERIOD_DAYS_MAP[period] || 250;
  const fallbackBars = generateSyntheticOHLCV(ticker, fallbackCount);
  return {
    bars: fallbackBars,
    source: 'synthetic',
    asOf: new Date().toISOString(),
    isReal: false,
    count: fallbackBars.length,
    ticker: ticker.toUpperCase(),
    firstDate: fallbackBars[0]?.time,
    lastDate: fallbackBars[fallbackBars.length - 1]?.time,
    period,
    interval,
  };
}
