/**
 * MarketOverview: 4 Market Index Overview Cards Container
 * Strictly adheres to < 200 lines limit.
 */

import React from 'react';
import { MarketIndex } from '../../types/market';
import { useMarketIndices } from '../../hooks/useMarketIndices';
import { MarketIndexCard } from './MarketIndexCard';

interface MarketOverviewProps {
  indices?: MarketIndex[];
  selectedSymbol?: string;
  onSelect?: (symbol: string) => void;
  className?: string;
}

export function MarketOverview({
  indices: propIndices,
  selectedSymbol,
  onSelect,
  className = ''
}: MarketOverviewProps) {
  const { indices: hookIndices, loading, error, isLive } = useMarketIndices({
    initialData: propIndices,
    autoSubscribe: !propIndices
  });

  const displayIndices = propIndices && propIndices.length > 0 ? propIndices : hookIndices;

  if (loading && displayIndices.length === 0) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 my-3 ${className}`}>
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="h-[108px] bg-slate-100 rounded-xl animate-pulse border border-slate-200" />
        ))}
      </div>
    );
  }

  return (
    <section className={`w-full my-2.5 ${className}`} aria-label="Tổng quan 4 chỉ số thị trường">
      {error && (
        <div className="mb-2 px-3 py-1.5 text-xs text-amber-700 bg-amber-50 rounded-lg border border-amber-200">
          ⚠️ {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {displayIndices.map((item) => (
          <MarketIndexCard
            key={item.symbol}
            data={item}
            isSelected={selectedSymbol === item.symbol}
            onSelect={onSelect}
          />
        ))}
      </div>
    </section>
  );
}

export default MarketOverview;
