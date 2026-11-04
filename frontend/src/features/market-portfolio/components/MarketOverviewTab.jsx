import { useMemo, useState } from 'react'
import { IndexCardsBar } from './IndexCardsBar'
import MarketHeatmap from './MarketHeatmap'
import useMarketHeatmap from '../hooks/useMarketHeatmap'
import { buildMarketOverview, selectOverviewMovers } from '../services/marketOverviewModel'
import { formatNumber, formatChange, formatMetric, number } from '../services/marketHeatmapModel'
import './market-overview-tab.css'

const EMPTY = []
const GLOBAL_MARKETS = [
  { symbol: 'SPX', label: 'S&P 500' },
  { symbol: 'NDX', label: 'NASDAQ 100' },
  { symbol: 'DJI', label: 'Dow Jones' },
  { symbol: 'DAX', label: 'DAX' },
  { symbol: 'NIKKEI', label: 'Nikkei 225' },
  { symbol: 'HANGSENG', label: 'Hang Seng' },
]
const MODES = [
  { key: 'gainers', label: 'Tăng mạnh' },
  { key: 'losers', label: 'Giảm mạnh' },
  { key: 'liquidity', label: 'Thanh khoản' },
]
const tone = value => value == null ? '' : value > 0 ? 'is-up' : value < 0 ? 'is-down' : 'is-flat'

function BreadthTrack({ row }) {
  return <span className="market-overview__breadth-track" aria-hidden="true">
    {['up', 'flat', 'down'].map(key => <i key={key} className={`is-${key}`} style={{ width: row.known > 0 ? `${row[key] / row.known * 100}%` : '0%' }} />)}
  </span>
}

function MarketPulse({ model, ready }) {
  const { totals, exchanges } = model
  return <section className="market-overview__pulse" aria-label="Nhịp thị trường">
    <div className="market-overview__pulse-summary">
      <div className="market-overview__pulse-title"><strong>Toàn thị trường</strong><small>{ready ? `${formatNumber(totals.traded, 0)} mã đã giao dịch` : 'Đang chờ dữ liệu'}</small></div>
      <div className="market-overview__pulse-breadth">
        <div className="market-overview__counts">
          <span><strong className="is-up">{formatNumber(ready ? totals.up : null, 0)}</strong> tăng</span>
          <span><strong className="is-flat">{formatNumber(ready ? totals.flat : null, 0)}</strong> tham chiếu</span>
          <span><strong className="is-down">{formatNumber(ready ? totals.down : null, 0)}</strong> giảm</span>
        </div>
        <BreadthTrack row={totals} />
      </div>
      <div className="market-overview__turnover"><small>Giá trị giao dịch</small><strong>{formatMetric(totals.turnover, 'value')}</strong></div>
    </div>
    <details className="market-overview__breadth-details">
      <summary>Độ rộng theo sàn</summary>
      <div className="market-overview__exchanges">
        {exchanges.map(row => <div className="market-overview__exchange" key={row.exchange}>
          <strong>{row.exchange === 'UPCOM' ? 'UPCoM' : row.exchange}</strong>
          <span className="is-up">{formatNumber(ready ? row.up : null, 0)} tăng</span>
          <span className="is-flat">{formatNumber(ready ? row.flat : null, 0)} tham chiếu</span>
          <span className="is-down">{formatNumber(ready ? row.down : null, 0)} giảm</span>
          <BreadthTrack row={row} />
        </div>)}
      </div>
      <p className="market-overview__footnote">Chỉ đếm mã đã giao dịch và có giá, % thay đổi hợp lệ.{totals.traded > totals.known ? ` ${formatNumber(totals.traded - totals.known, 0)} mã đã giao dịch chưa đủ dữ liệu biến động.` : ''}</p>
    </details>
  </section>
}

function SectorLiquidity({ sectors, ready }) {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? sectors : sectors.slice(0, 6)
  return <section className="market-overview__panel" aria-labelledby="overview-sector-title">
    <header className="market-overview__panel-heading"><h2 id="overview-sector-title">Thanh khoản theo ngành</h2><span>Tỷ trọng GTGD</span></header>
    <ol className="market-overview__sector-list">
      {visible.map(row => <li key={row.id}>
        <div><strong>{row.name}</strong><span>{formatMetric(row.value, 'value')}</span><small>{formatNumber(row.share, 1)}%</small></div>
        <span className="market-overview__sector-track" aria-hidden="true"><i style={{ width: `${row.share}%` }} /></span>
      </li>)}
    </ol>
    {!sectors.length && <p className="market-overview__empty">{ready ? 'Chưa có giá trị giao dịch theo ngành.' : 'Đang chờ dữ liệu ngành…'}</p>}
    {sectors.length > 6 && <button type="button" className="market-overview__more" aria-expanded={expanded} onClick={() => setExpanded(v => !v)}>{expanded ? 'Thu gọn' : `Xem cả ${sectors.length} ngành`}</button>}
    <p className="market-overview__footnote">Tính từ GTGD có dữ liệu trên HOSE, HNX và UPCoM.</p>
  </section>
}

function MoversPanel({ stocks, ready, onSelect }) {
  const [mode, setMode] = useState('gainers')
  const [liquidOnly, setLiquidOnly] = useState(true)
  const rows = useMemo(() => selectOverviewMovers(stocks, { mode, liquidOnly }), [stocks, mode, liquidOnly])
  return <section className="market-overview__panel market-overview__movers" aria-labelledby="overview-movers-title">
    <header className="market-overview__panel-heading"><h2 id="overview-movers-title">Cổ phiếu nổi bật</h2><span>Toàn thị trường</span></header>
    <div className="market-overview__mover-controls">
      <div className="market-overview__mode-group" role="group" aria-label="Nhóm cổ phiếu nổi bật">
        {MODES.map(item => <button key={item.key} type="button" aria-pressed={mode === item.key} onClick={() => setMode(item.key)}>{item.label}</button>)}
      </div>
      <label className="market-overview__liquid"><input type="checkbox" checked={liquidOnly} onChange={e => setLiquidOnly(e.target.checked)} />GTGD ≥ 1 tỷ</label>
    </div>
    <table className="market-overview__mover-table">
      <thead><tr><th scope="col">Mã</th><th scope="col">Giá (đ)</th><th scope="col">Thay đổi</th><th scope="col">GTGD</th></tr></thead>
      <tbody>{rows.map(row => <tr key={row.symbol}>
        <td><button type="button" onClick={() => onSelect?.(row.symbol)} title={row.name} aria-label={`Mở ${row.symbol}`}><strong>{row.symbol}</strong><small>{row.exchange}</small></button></td>
        <td>{formatNumber(row.price, 0)}</td><td className={tone(row.change_pct)}>{formatChange(row.change_pct)}</td><td>{formatMetric(row.value, 'value')}</td>
      </tr>)}</tbody>
    </table>
    {!rows.length && <p className="market-overview__empty">{!ready ? 'Đang chờ dữ liệu cổ phiếu…' : liquidOnly ? 'Chưa có mã phù hợp với GTGD từ 1 tỷ. Bỏ chọn ngưỡng để xem thêm.' : 'Chưa có mã phù hợp trong phiên.'}</p>}
  </section>
}

export default function MarketOverviewTab({ indexItems = [], selectedSymbol, onSelectSymbol }) {
  const feed = useMarketHeatmap()
  const items = feed.data?.items || EMPTY
  const model = useMemo(() => buildMarketOverview(items), [items])
  const indicesBySymbol = useMemo(() => new Map(indexItems.map(item => [String(item.symbol || '').toUpperCase(), item])), [indexItems])
  const ready = Boolean(feed.data)
  return <main className="market-overview" aria-label="Tổng quan thị trường và cổ phiếu">
    <IndexCardsBar compact indexItems={indexItems} selectedSymbol={selectedSymbol} onSelect={onSelectSymbol} />
    <MarketPulse model={model} ready={ready} />
    <MarketHeatmap feed={feed} onSelectSymbol={onSelectSymbol} />
    <div className="market-overview__grid">
      <SectorLiquidity sectors={model.sectors} ready={ready} />
      <MoversPanel stocks={model.stocks} ready={ready} onSelect={onSelectSymbol} />
    </div>
    <section className="market-overview__panel market-overview__global" aria-labelledby="market-overview-global-title">
      <header className="market-overview__panel-heading"><h2 id="market-overview-global-title">Chỉ số quốc tế</h2><span>Tham chiếu bối cảnh thị trường</span></header>
      <div className="market-overview__global-grid">{GLOBAL_MARKETS.map(({ symbol, label }) => {
        const change = number(indicesBySymbol.get(symbol)?.change_pct)
        return <div className="market-overview__global-quote" key={symbol}><span><strong>{label}</strong><small>{symbol}</small></span><span className={tone(change)}>{formatChange(change)}</span></div>
      })}</div>
    </section>
  </main>
}
