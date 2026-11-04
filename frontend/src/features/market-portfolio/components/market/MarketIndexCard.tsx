/**
 * MarketIndexCard: High-density Vietnam Stock Market Index Card
 * Strictly adheres to < 200 lines limit.
 */

import React from 'react';
import { MarketIndex, getIndexTone } from '../../types/market';
import { MarketSparkline } from './MarketSparkline';
import { MarketBreadth } from './MarketBreadth';

interface MarketIndexCardProps {
  data: MarketIndex;
  isSelected?: boolean;
  onSelect?: (symbol: string) => void;
}

export function MarketIndexCard({ data, isSelected = false, onSelect }: MarketIndexCardProps) {
  const tone = getIndexTone(data.change);
  const isPos = tone === 'pos';
  const isNeg = tone === 'neg';

  const toneColorClass = isPos ? 'text-emerald-600' : isNeg ? 'text-red-500' : 'text-amber-500';

  // Format số chuẩn vi-VN
  const formattedPrice = data.currentPrice.toLocaleString('vi-VN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  const formattedChange = (data.change > 0 ? '+' : '') + data.change.toLocaleString('vi-VN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });

  const formattedPct = (data.changePercent > 0 ? '+' : '') + data.changePercent.toLocaleString('vi-VN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }) + '%';

  const formattedVol = data.volume.toLocaleString('vi-VN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }) + ' Triệu CP';

  const formattedVal = data.turnover.toLocaleString('vi-VN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }) + ' Tỷ';

  return (
    <div
      className={`relative flex justify-between items-start bg-white border rounded-xl p-3.5 shadow-sm transition-all duration-200 cursor-pointer select-none hover:-translate-y-0.5 hover:shadow-md ${
        isSelected ? 'border-blue-500 ring-2 ring-blue-500/20 bg-blue-50/20' : 'border-slate-200 hover:border-slate-300'
      }`}
      onClick={() => onSelect?.(data.symbol)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSelect?.(data.symbol)}
    >
      {/* CỘT TRÁI: Tên, Giá lớn, Khối lượng & Độ rộng */}
      <div className="flex flex-col flex-1 min-w-0 pr-2">
        <div className="text-[14px] font-bold text-slate-800 tracking-tight leading-none">
          {data.symbol}
        </div>

        <div className={`text-[25px] font-extrabold tracking-tight leading-tight my-1 tabular-nums ${toneColorClass}`}>
          {formattedPrice}
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500 whitespace-nowrap mb-1">
          <span>{formattedVol}</span>
          <span className="opacity-40">|</span>
          <span>{formattedVal}</span>
        </div>

        <MarketBreadth
          advances={data.advances}
          ceil={data.ceil}
          unchanged={data.unchanged}
          declines={data.declines}
          floor={data.floor}
        />
      </div>

      {/* CỘT PHẢI: % thay đổi, +/- điểm, Sparkline góc dưới */}
      <div className="flex flex-col items-end flex-shrink-0">
        <div className={`text-[14px] font-bold leading-tight ${toneColorClass}`}>
          {formattedPct}
        </div>

        <div className={`text-[13px] font-semibold leading-tight my-0.5 tabular-nums ${toneColorClass}`}>
          {formattedChange}
        </div>

        <div className="mt-1 flex items-end justify-end w-[115px] h-[44px]">
          <MarketSparkline
            history={data.history}
            referencePrice={data.referencePrice}
            currentPrice={data.currentPrice}
            width={115}
            height={44}
          />
        </div>
      </div>
    </div>
  );
}
