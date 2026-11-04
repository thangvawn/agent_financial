/**
 * Reusable MarketSparkline Component with Intraday Time-Series SVG and Tooltip
 * Strictly adheres to < 200 lines limit.
 */

import React, { useId, useMemo, useState } from 'react';
import { IndexPricePoint, TONE_COLORS } from '../../types/market';

interface MarketSparklineProps {
  history: IndexPricePoint[];
  referencePrice: number;
  currentPrice: number;
  width?: number;
  height?: number;
}

export function MarketSparkline({
  history = [],
  referencePrice,
  currentPrice,
  width = 115,
  height = 44
}: MarketSparklineProps) {
  const gradId = useId();
  const [hoverPoint, setHoverPoint] = useState<{ x: number; y: number; data: IndexPricePoint } | null>(null);

  const isPos = currentPrice > referencePrice;
  const isNeg = currentPrice < referencePrice;
  const strokeColor = isPos ? TONE_COLORS.pos : isNeg ? TONE_COLORS.neg : TONE_COLORS.ref;
  const fillColor = isPos ? 'rgba(22, 163, 74, 0.14)' : isNeg ? 'rgba(239, 41, 41, 0.12)' : 'rgba(234, 179, 8, 0.12)';

  const { points, refY } = useMemo(() => {
    // Chống lỗi khi dữ liệu rỗng hoặc ít điểm
    const valid = history.length > 0 ? history : [{ timestamp: Date.now(), price: currentPrice }];
    const allPrices = [...valid.map((p) => p.price), referencePrice];

    let min = Math.min(...allPrices);
    let max = Math.max(...allPrices);
    let range = max - min;

    if (range <= 0) {
      min -= 1;
      max += 1;
      range = 2;
    } else {
      // Đệm 6% để không bị chạm viền
      min -= range * 0.06;
      max += range * 0.06;
      range = max - min;
    }

    const padTop = 3;
    const padBottom = 3;
    const availH = height - padTop - padBottom;

    const calcY = (val: number) => {
      const normalized = (val - min) / range;
      return height - padBottom - normalized * availH;
    };

    const calculatedRefY = Math.max(padTop, Math.min(height - padBottom, calcY(referencePrice)));
    const len = valid.length;

    const calculatedPoints = valid.map((pt, idx) => {
      const x = len > 1 ? (idx / (len - 1)) * width : width / 2;
      const y = Math.max(padTop, Math.min(height - padBottom, calcY(pt.price)));
      return { x, y, data: pt };
    });

    return { points: calculatedPoints, refY: calculatedRefY };
  }, [history, referencePrice, currentPrice, width, height]);

  const pathD = points.reduce((acc, p, idx) => `${acc} ${idx === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`, '');
  const areaD = `M 0 ${refY.toFixed(1)} ${pathD.replace('M', 'L')} L ${width} ${refY.toFixed(1)} Z`;

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const closest = points.reduce((prev, curr) => (Math.abs(curr.x - mouseX) < Math.abs(prev.x - mouseX) ? curr : prev));
    setHoverPoint(closest);
  };

  return (
    <div className="relative inline-block select-none" style={{ width, height }}>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="block overflow-visible cursor-crosshair"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoverPoint(null)}
        role="img"
        aria-label="Sparkline intraday"
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity={0.25} />
            <stop offset="100%" stopColor={strokeColor} stopOpacity={0.02} />
          </linearGradient>
        </defs>

        {/* Đường tham chiếu nét đứt */}
        <line
          x1={0}
          y1={refY.toFixed(1)}
          x2={width}
          y2={refY.toFixed(1)}
          stroke={TONE_COLORS.dashLine}
          strokeWidth={1}
          strokeDasharray="2,2"
          opacity={0.75}
        />

        {/* Vùng diện tích mờ */}
        <path d={areaD} fill={fillColor} />

        {/* Đường giá 1.25px */}
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth={1.35}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Điểm active khi hover */}
        {hoverPoint && (
          <circle
            cx={hoverPoint.x.toFixed(1)}
            cy={hoverPoint.y.toFixed(1)}
            r={3}
            fill={strokeColor}
            stroke="#ffffff"
            strokeWidth={1.5}
          />
        )}
      </svg>

      {/* Floating Micro Tooltip */}
      {hoverPoint && (
        <div
          className="absolute z-20 pointer-events-none transform -translate-x-1/2 -top-7 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-tight bg-slate-900 text-white shadow-md whitespace-nowrap"
          style={{ left: Math.max(20, Math.min(width - 20, hoverPoint.x)) }}
        >
          {hoverPoint.data.price.toLocaleString('vi-VN', { minimumFractionDigits: 2 })}
        </div>
      )}
    </div>
  );
}
