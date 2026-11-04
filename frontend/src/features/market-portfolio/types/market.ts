/**
 * Standard Market Index & Sparkline Data Contracts
 * Strictly adheres to < 200 lines limit.
 */

export interface IndexPricePoint {
  timestamp: number; // Unix epoch ms
  price: number;
}

export interface MarketBreadthStats {
  advances: number;
  ceil?: number;
  unchanged: number;
  declines: number;
  floor?: number;
}

export interface MarketIndex {
  symbol: string;
  name?: string;
  currentPrice: number;
  referencePrice: number;
  change: number;
  changePercent: number;
  volume: number;     // Triệu CP
  turnover: number;   // Tỷ VNĐ
  advances: number;
  unchanged: number;
  declines: number;
  ceil?: number;
  floor?: number;
  history: IndexPricePoint[];
  updatedAt: number;
  isDemo?: boolean;
}

export type IndexTone = 'pos' | 'neg' | 'ref';

export function getIndexTone(change: number): IndexTone {
  if (change > 0) return 'pos';
  if (change < 0) return 'neg';
  return 'ref';
}

export const TONE_COLORS = {
  pos: '#16A34A',
  neg: '#EF2929',
  ref: '#EAB308',
  dashLine: '#94A3B8'
} as const;
