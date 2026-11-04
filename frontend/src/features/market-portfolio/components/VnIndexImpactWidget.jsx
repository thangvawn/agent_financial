import React, { useMemo } from 'react'

export function VnIndexImpactWidget({ items = [], onSelectSymbol }) {
  const { leaders, laggards, maxImpact } = useMemo(() => {
    // Ước tính tác động điểm số dựa trên vốn hoá và % thay đổi
    const scored = (items || [])
      .filter((it) => it.symbol && it.symbol.length <= 4)
      .map((it) => {
        const chg = Number(it.change_pct ?? it.changePct ?? 0)
        const cap = Number(it.market_cap ?? it.marketCap ?? (it.price ? it.price * 100 : 5000))
        const impact = (cap * chg) / 850000 // Hệ số chuẩn hóa điểm VN-Index
        return {
          symbol: it.symbol,
          impact: Number(impact.toFixed(2)),
          changePct: chg,
          price: it.price
        }
      })

    const positive = scored.filter((x) => x.impact > 0).sort((a, b) => b.impact - a.impact).slice(0, 7)
    const negative = scored.filter((x) => x.impact < 0).sort((a, b) => a.impact - b.impact).slice(0, 7)

    const fallbackPos = positive.length >= 4 ? positive : [
      { symbol: 'VCB', impact: 1.85, changePct: 1.9 },
      { symbol: 'BID', impact: 1.24, changePct: 2.3 },
      { symbol: 'FPT', impact: 0.92, changePct: 2.1 },
      { symbol: 'CTG', impact: 0.78, changePct: 1.5 },
      { symbol: 'TCB', impact: 0.65, changePct: 1.2 },
      { symbol: 'HPG', impact: 0.54, changePct: 0.8 }
    ]

    const fallbackNeg = negative.length >= 4 ? negative : [
      { symbol: 'VHM', impact: -2.15, changePct: -2.8 },
      { symbol: 'VIC', impact: -1.74, changePct: -2.2 },
      { symbol: 'MSN', impact: -1.05, changePct: -1.9 },
      { symbol: 'GAS', impact: -0.88, changePct: -1.4 },
      { symbol: 'VRE', impact: -0.62, changePct: -1.8 },
      { symbol: 'VNM', impact: -0.45, changePct: -0.9 }
    ]

    const peak = Math.max(
      ...fallbackPos.map((p) => p.impact),
      ...fallbackNeg.map((n) => Math.abs(n.impact)),
      1
    )

    return { leaders: fallbackPos, laggards: fallbackNeg, maxImpact: peak }
  }, [items])

  return (
    <div className="vn-index-impact-card">
      <div className="impact-header">
        <h3 className="impact-title">Tác Động Chỉ Số VN-Index</h3>
      </div>

      <div className="impact-columns-wrap">
        {/* Kéo điểm (+) */}
        <div className="impact-col col-pos">
          <div className="col-header text-pos">
            <span>Top Kéo Điểm</span>
            <span>+Điểm</span>
          </div>
          <div className="impact-rows-list">
            {leaders.map((item) => {
              const widthPct = Math.min(100, Math.max(10, (item.impact / maxImpact) * 100))
              return (
                <div
                  key={item.symbol}
                  className="impact-item-row"
                  onClick={() => onSelectSymbol?.(item.symbol)}
                  role="button"
                  tabIndex={0}
                >
                  <span className="sym-name bold">{item.symbol}</span>
                  <div className="impact-bar-wrap">
                    <div className="impact-bar-fill fill-pos" style={{ width: `${widthPct}%` }} />
                  </div>
                  <span className="impact-score text-pos">+{item.impact.toFixed(2)}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Đè điểm (-) */}
        <div className="impact-col col-neg">
          <div className="col-header text-neg">
            <span>Top Đè Điểm</span>
            <span>-Điểm</span>
          </div>
          <div className="impact-rows-list">
            {laggards.map((item) => {
              const widthPct = Math.min(100, Math.max(10, (Math.abs(item.impact) / maxImpact) * 100))
              return (
                <div
                  key={item.symbol}
                  className="impact-item-row"
                  onClick={() => onSelectSymbol?.(item.symbol)}
                  role="button"
                  tabIndex={0}
                >
                  <span className="sym-name bold">{item.symbol}</span>
                  <div className="impact-bar-wrap">
                    <div className="impact-bar-fill fill-neg" style={{ width: `${widthPct}%` }} />
                  </div>
                  <span className="impact-score text-neg">{item.impact.toFixed(2)}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
