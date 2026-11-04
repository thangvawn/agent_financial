import React, { useState } from 'react'

const MOCK_VCP = [
  { symbol: 'FPT', contraction: '3 lần (VCP)', volDry: 'Kiệt 65%', base: 'Nền phẳng 7 tuần', changePct: 2.1 },
  { symbol: 'CTR', contraction: '2 lần (VCP)', volDry: 'Kiệt 52%', base: 'Cốc tay cầm 10 tuần', changePct: 1.8 },
  { symbol: 'DGC', contraction: '4 lần (VCP)', volDry: 'Kiệt 70%', base: 'Nền VCP chặt 5 tuần', changePct: 3.4 },
  { symbol: 'FRT', contraction: '2 lần (VCP)', volDry: 'Kiệt 48%', base: 'Gãy rũ bứt phá', changePct: 1.5 }
]

const MOCK_CLOSE_HIGH_LOW = {
  highs: [
    { symbol: 'GVR', closeHighPct: '98.5%', changePct: 4.8, volRatio: '2.4x' },
    { symbol: 'KBC', closeHighPct: '96.2%', changePct: 3.5, volRatio: '1.9x' },
    { symbol: 'SZC', closeHighPct: '95.0%', changePct: 3.1, volRatio: '1.7x' }
  ],
  lows: [
    { symbol: 'NVL', closeLowPct: '99.0%', changePct: -4.2, volRatio: '1.8x' },
    { symbol: 'PDR', closeLowPct: '94.5%', changePct: -3.6, volRatio: '1.5x' },
    { symbol: 'DXG', closeLowPct: '92.1%', changePct: -2.9, volRatio: '1.4x' }
  ]
}

const MOCK_STREAKS = [
  { symbol: 'TCB', streak: 5, type: 'up', totalGain: '+11.2%' },
  { symbol: 'MBB', streak: 4, type: 'up', totalGain: '+7.8%' },
  { symbol: 'MSN', streak: 4, type: 'down', totalLoss: '-8.5%' },
  { symbol: 'VRE', streak: 3, type: 'down', totalLoss: '-5.2%' }
]

export function MarketMomentumWidgets({ onSelectSymbol }) {
  const [subTab, setSubTab] = useState('vcp') // 'vcp' | 'high_low' | 'streak'

  return (
    <div className="momentum-widget-card">
      <div className="momentum-header">
        <div className="tab-pill-group">
          <button
            type="button"
            className={`tab-pill ${subTab === 'vcp' ? 'is-active' : ''}`}
            onClick={() => setSubTab('vcp')}
          >
            Mô hình VCP
          </button>
          <button
            type="button"
            className={`tab-pill ${subTab === 'high_low' ? 'is-active' : ''}`}
            onClick={() => setSubTab('high_low')}
          >
            Đóng Đỉnh / Đáy
          </button>
          <button
            type="button"
            className={`tab-pill ${subTab === 'streak' ? 'is-active' : ''}`}
            onClick={() => setSubTab('streak')}
          >
            Chuỗi Tăng/Giảm
          </button>
        </div>
      </div>

      <div className="momentum-content">
        {subTab === 'vcp' && (
          <div className="vcp-list">
            <div className="table-mini-header">
              <span>Mã CK</span>
              <span>Độ thu hẹp</span>
              <span>Độ cạn cung</span>
              <span>Mô hình cơ sở</span>
            </div>
            {MOCK_VCP.map((it) => (
              <div
                key={it.symbol}
                className="vcp-row"
                onClick={() => onSelectSymbol?.(it.symbol)}
                role="button"
                tabIndex={0}
              >
                <span className="sym bold text-pos">{it.symbol}</span>
                <span className="badge-tag">{it.contraction}</span>
                <span className="text-muted">{it.volDry}</span>
                <span className="text-secondary">{it.base}</span>
              </div>
            ))}
          </div>
        )}

        {subTab === 'high_low' && (
          <div className="high-low-grid">
            <div className="hl-col">
              <span className="hl-title text-pos">Đóng Sát Đỉnh (Phe mua)</span>
              {MOCK_CLOSE_HIGH_LOW.highs.map((h) => (
                <div key={h.symbol} className="hl-row" onClick={() => onSelectSymbol?.(h.symbol)} role="button" tabIndex={0}>
                  <strong className="text-pos">{h.symbol}</strong>
                  <span>Sát đỉnh {h.closeHighPct}</span>
                  <span className="badge-pos">+{h.changePct}%</span>
                </div>
              ))}
            </div>
            <div className="hl-col">
              <span className="hl-title text-neg">Đóng Sát Đáy (Phe bán)</span>
              {MOCK_CLOSE_HIGH_LOW.lows.map((l) => (
                <div key={l.symbol} className="hl-row" onClick={() => onSelectSymbol?.(l.symbol)} role="button" tabIndex={0}>
                  <strong className="text-neg">{l.symbol}</strong>
                  <span>Sát đáy {l.closeLowPct}</span>
                  <span className="badge-neg">{l.changePct}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {subTab === 'streak' && (
          <div className="streak-list">
            {MOCK_STREAKS.map((st) => (
              <div
                key={st.symbol}
                className="streak-row"
                onClick={() => onSelectSymbol?.(st.symbol)}
                role="button"
                tabIndex={0}
              >
                <span className={`sym bold ${st.type === 'up' ? 'text-pos' : 'text-neg'}`}>{st.symbol}</span>
                <span className={`streak-badge ${st.type === 'up' ? 'is-up' : 'is-down'}`}>
                  {st.type === 'up' ? `${st.streak} phiên tăng liên tiếp` : `${st.streak} phiên giảm liên tiếp`}
                </span>
                <strong className={st.type === 'up' ? 'text-pos' : 'text-neg'}>
                  {st.totalGain || st.totalLoss}
                </strong>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
