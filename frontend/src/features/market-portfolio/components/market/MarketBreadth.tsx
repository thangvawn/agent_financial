/**
 * MarketBreadth Component: 5-color market breadth indicator
 * Strictly adheres to < 200 lines limit.
 */

import React from 'react';

interface MarketBreadthProps {
  advances: number;
  ceil?: number;
  unchanged: number;
  declines: number;
  floor?: number;
}

export function MarketBreadth({
  advances = 0,
  ceil = 0,
  unchanged = 0,
  declines = 0,
  floor = 0
}: MarketBreadthProps) {
  return (
    <div className="flex items-center gap-2 text-[11px] font-semibold tracking-tight text-slate-600 pt-0.5">
      {/* Mã tăng (Ceil tím nếu có) */}
      <span className="inline-flex items-center gap-0.5 text-emerald-600" title="Mã tăng (Tím: giá trần)">
        <span>▲</span>
        <span>{advances}</span>
        {ceil > 0 && <span className="font-bold text-purple-600">({ceil})</span>}
      </span>

      {/* Mã không đổi / tham chiếu */}
      <span className="inline-flex items-center gap-0.5 text-amber-500" title="Mã đứng giá tham chiếu">
        <span>■</span>
        <span>{unchanged}</span>
      </span>

      {/* Mã giảm (Floor xanh lơ nếu có) */}
      <span className="inline-flex items-center gap-0.5 text-red-500" title="Mã giảm (Lam: giá sàn)">
        <span>▼</span>
        <span>{declines}</span>
        {floor > 0 && <span className="font-bold text-cyan-500">({floor})</span>}
      </span>
    </div>
  );
}
