import React, { useState, useMemo } from 'react'

export function ForeignFlowButterfly({ items = [], onSelectSymbol }) {
  const [metric, setMetric] = useState('value') // 'value' (Tỷ), 'volume' (Tr CP)

  const { topBuy, topSell, maxVal } = useMemo(() => {
    const valid = (items || []).filter((it) => it.symbol && it.symbol.length <= 4)
    
    const finite = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
    const net = (item, direct, buy, sell, divisor) => finite(item[direct]) ? Number(item[direct])
      : finite(item[buy]) && finite(item[sell]) ? (Number(item[buy]) - Number(item[sell])) / divisor : null
    const flows = valid.map(item => ({
      symbol: item.symbol,
      val: metric === 'value'
        ? net(item, 'foreign_net_val_billion', 'foreign_buy_val', 'foreign_sell_val', 1e9)
        : net(item, 'foreign_net_vol_million', 'foreign_buy_vol', 'foreign_sell_vol', 1e6),
    })).filter(item => Number.isFinite(item.val))
    const buyers = flows.filter(item => item.val > 0).sort((a,b) => b.val-a.val).slice(0,8)
    const sellers = flows.filter(item => item.val < 0).map(item => ({...item, val:-item.val})).sort((a,b) => b.val-a.val).slice(0,8)
    return {topBuy:buyers, topSell:sellers, maxVal:Math.max(1,...flows.map(item => Math.abs(item.val)))}
  }, [items, metric])

  const unitLabel = metric === 'value' ? 'Tỷ VNĐ' : 'Triệu CP'

  return (
    <div className="foreign-butterfly-card">
      <div className="butterfly-header">
        <div className="butterfly-title-wrap">
          <h3 className="butterfly-title">Giao Dịch Khối Ngoại (Cánh Bướm)</h3>
        </div>
        <div className="metric-toggle-btns">
          <button
            type="button"
            className={`btn-toggle ${metric === 'value' ? 'is-active' : ''}`}
            onClick={() => setMetric('value')}
          >
            Giá trị (Tỷ)
          </button>
          <button
            type="button"
            className={`btn-toggle ${metric === 'volume' ? 'is-active' : ''}`}
            onClick={() => setMetric('volume')}
          >
            Khối lượng (Tr CP)
          </button>
        </div>
      </div>

      {!topBuy.length && !topSell.length && <p role="status">Chưa có dữ liệu giao dịch khối ngoại.</p>}
      <div className="butterfly-columns-container">
        {/* Cột Mua Ròng (Bên Trái) */}
        <div className="butterfly-wing buy-wing">
          <div className="wing-header">
            <span className="wing-title text-pos">Top Mua Ròng</span>
            <span className="wing-unit">({unitLabel})</span>
          </div>
          <div className="bars-list">
            {topBuy.map((item) => {
              const widthPct = Math.min(100, Math.max(8, (item.val / maxVal) * 100))
              return (
                <div
                  key={item.symbol}
                  className="bar-row buy-row"
                  onClick={() => onSelectSymbol?.(item.symbol)}
                  onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelectSymbol?.(item.symbol) } }}
                  role="button"
                  tabIndex={0}
                >
                  <span className="sym-tag bold">{item.symbol}</span>
                  <div className="bar-track">
                    <div className="bar-fill fill-pos" style={{ width: `${widthPct}%` }}>
                      <span className="bar-label-inner">+{item.val.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Cột Bán Ròng (Bên Phải) */}
        <div className="butterfly-wing sell-wing">
          <div className="wing-header">
            <span className="wing-title text-neg">Top Bán Ròng</span>
            <span className="wing-unit">({unitLabel})</span>
          </div>
          <div className="bars-list">
            {topSell.map((item) => {
              const widthPct = Math.min(100, Math.max(8, (item.val / maxVal) * 100))
              return (
                <div
                  key={item.symbol}
                  className="bar-row sell-row"
                  onClick={() => onSelectSymbol?.(item.symbol)}
                  onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelectSymbol?.(item.symbol) } }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="bar-track align-right">
                    <div className="bar-fill fill-neg" style={{ width: `${widthPct}%` }}>
                      <span className="bar-label-inner">-{item.val.toFixed(1)}</span>
                    </div>
                  </div>
                  <span className="sym-tag bold">{item.symbol}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
