import { useEffect, useMemo, useState } from 'react'
import { Activity, ArrowUpRight, Box, RefreshCw, Search, SlidersHorizontal } from 'lucide-react'
import { fetchMpCommoditiesSnapshot } from '../services'

const GROUPS = [
  ['all', 'Tất cả nhóm'], ['metals', 'Kim loại'], ['energy', 'Năng lượng'],
  ['grains', 'Ngũ cốc'], ['raw_materials', 'Nguyên liệu'],
]

function number(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  return Number(value).toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}

function money(value) {
  if (value === null || value === undefined) return '—'
  return `$${number(value, Number(value) < 10 ? 3 : 2)}`
}

function Change({ value }) {
  if (value === null || value === undefined) return <span className="commodity-change is-flat">—</span>
  const up = Number(value) >= 0
  return <span className={`commodity-change ${up ? 'is-up' : 'is-down'}`}>{up ? '+' : ''}{number(value, 2)}%</span>
}

function Sparkline({ row }) {
  const base = Number(row.price) || 1
  const change = Number(row.change_pct) || 0
  const points = [base - change * .6, base - change * .25, base + change * .15, base + change * .4, base + change]
  const min = Math.min(...points), max = Math.max(...points), span = max - min || 1
  const path = points.map((point, index) => `${index ? 'L' : 'M'} ${index * 25} ${28 - ((point - min) / span) * 23}`).join(' ')
  return <svg className={`commodity-spark ${change >= 0 ? 'is-up' : 'is-down'}`} viewBox="0 0 100 32" preserveAspectRatio="none"><path d={path} vectorEffect="non-scaling-stroke" /></svg>
}

export default function CommoditiesPanel() {
  const [data, setData] = useState(null)
  const [query, setQuery] = useState('')
  const [group, setGroup] = useState('all')
  const [sort, setSort] = useState('liquidity')
  const [selected, setSelected] = useState('XAU')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() {
    try {
      setLoading(true)
      const payload = await fetchMpCommoditiesSnapshot()
      setData(payload)
      setError('')
    } catch (err) { setError(err.message) } finally { setLoading(false) }
  }

  useEffect(() => {
    let cancelled = false
    async function initialLoad() {
      try {
        const payload = await fetchMpCommoditiesSnapshot()
        if (!cancelled) { setData(payload); setError('') }
      } catch (err) { if (!cancelled) setError(err.message) }
      finally { if (!cancelled) setLoading(false) }
    }
    initialLoad()
    const timer = setInterval(initialLoad, 30000)
    return () => { cancelled = true; clearInterval(timer) }
  }, [])

  const items = data?.items || []
  const filtered = useMemo(() => {
    const rows = items.filter((row) => (group === 'all' || row.category === group) && `${row.symbol} ${row.name}`.toLowerCase().includes(query.toLowerCase()))
    return [...rows].sort((a, b) => sort === 'change' ? (b.change_pct ?? -Infinity) - (a.change_pct ?? -Infinity) : sort === 'price' ? (b.price ?? -Infinity) - (a.price ?? -Infinity) : (b.volume_24h ?? -Infinity) - (a.volume_24h ?? -Infinity))
  }, [items, group, query, sort])
  const selectedRow = items.find((row) => row.symbol === selected) || filtered[0]
  const advancing = items.filter((row) => row.change_pct > 0).length
  const declining = items.filter((row) => row.change_pct < 0).length

  if (loading && !data) return <section className="mp-panel commodity-page"><div className="commodity-empty"><Activity size={18} /> Đang tải dữ liệu hàng hóa...</div></section>
  if (error && !data) return <section className="mp-panel commodity-page"><div className="commodity-empty"><strong>Không tải được dữ liệu</strong><span>{error}</span><button onClick={load}>Thử lại</button></div></section>

  return <section className="mp-panel commodity-page">
    <header className="commodity-head">
      <div><div className="commodity-kicker"><Box size={14} /> GLOBAL COMMODITIES / MARKET BOARD</div><h2>Thị trường hàng hóa</h2><p>Giá tham chiếu quốc tế, biến động và thanh khoản của các nhóm hàng hóa theo dõi.</p></div>
      <div className="commodity-status"><span className={`gt-status-dot ${data?.freshness === 'fresh' ? 'is-live' : ''}`} /><span>{data?.freshness === 'fresh' ? 'FRESH SNAPSHOT' : 'CACHED SNAPSHOT'}</span><small>{data?.provider} · {data?.data_interval} · {data?.as_of ? new Date(data.as_of).toLocaleTimeString('vi-VN') : '—'}</small><button onClick={load} aria-label="Làm mới"><RefreshCw size={14} className={loading ? 'is-spinning' : ''} /></button></div>
    </header>
    <div className="commodity-summary"><div><span>Hợp đồng theo dõi</span><strong>{items.length}</strong></div><div><span>Đang tăng</span><strong className="is-up">{advancing}</strong></div><div><span>Đang giảm</span><strong className="is-down">{declining}</strong></div><div><span>Nguồn dữ liệu</span><strong className="commodity-source">{data?.source || '—'}</strong></div></div>
    <div className="commodity-layout">
      <main>
        <div className="commodity-toolbar"><div className="commodity-groups">{GROUPS.map(([key, label]) => <button key={key} className={group === key ? 'is-active' : ''} onClick={() => setGroup(key)}>{label}</button>)}</div><div className="commodity-tools"><label><Search size={13} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm hàng hóa" /></label><label><SlidersHorizontal size={13} /><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="liquidity">Thanh khoản</option><option value="change">Tăng giá</option><option value="price">Giá</option></select></label></div></div>
        <div className="commodity-table-wrap"><table className="commodity-table"><thead><tr><th>#</th><th>Mã hàng hóa</th><th>Giá</th><th>+/-%</th><th>Tổng KL</th><th>Biểu đồ</th><th>Đơn vị</th></tr></thead><tbody>{filtered.map((row, index) => <tr key={row.symbol} className={selectedRow?.symbol === row.symbol ? 'is-selected' : ''} onClick={() => setSelected(row.symbol)}><td className="commodity-rank">{index + 1}</td><td><div className="commodity-asset"><span>{row.symbol.slice(0, 1)}</span><div><strong>{row.symbol}</strong><small>{row.name}</small></div></div></td><td className="num commodity-price">{money(row.price)}</td><td className="num"><Change value={row.change_pct} /></td><td className="num commodity-muted">{row.volume_24h ? number(row.volume_24h, 0) : '—'}</td><td><Sparkline row={row} /></td><td className="commodity-muted">{row.unit || '—'}</td></tr>)}</tbody></table>{!filtered.length && <div className="commodity-table-empty">Không có dữ liệu trong nhóm này.</div>}</div>
      </main>
      <aside className="commodity-focus">{selectedRow ? <><div className="commodity-focus-top"><span className="commodity-kicker">SELECTED CONTRACT</span><span>{selectedRow.category?.replace('_', ' ')}</span></div><div className="commodity-focus-identity"><span>{selectedRow.symbol.slice(0, 1)}</span><div><h3>{selectedRow.name}</h3><small>{selectedRow.symbol} · {selectedRow.unit || '—'}</small></div></div><div className="commodity-focus-price">{money(selectedRow.price)} <Change value={selectedRow.change_pct} /></div><div className="commodity-focus-chart"><Sparkline row={selectedRow} /></div><div className="commodity-focus-grid"><div><span>Cao nhất</span><strong>{money(selectedRow.high_24h)}</strong></div><div><span>Thấp nhất</span><strong>{money(selectedRow.low_24h)}</strong></div><div><span>Khối lượng</span><strong>{selectedRow.volume_24h ? number(selectedRow.volume_24h, 0) : '—'}</strong></div><div><span>Provider</span><strong>{selectedRow.source || '—'}</strong></div></div><p className="commodity-note"><ArrowUpRight size={14} /> Dữ liệu được lưu vào bảng commodity_quotes</p></> : <div className="commodity-empty">Chưa có hàng hóa.</div>}</aside>
    </div>
  </section>
}
