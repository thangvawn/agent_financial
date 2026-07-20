import { useEffect, useMemo, useState } from 'react'
import { Activity, ArrowUpRight, Bitcoin, RefreshCw, Search, SlidersHorizontal, WalletCards } from 'lucide-react'
import { fetchMpCryptoSnapshot } from '../services'

const money = (value, digits = 2) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  const number = Number(value)
  if (number >= 1_000_000_000_000) return `$${(number / 1_000_000_000_000).toFixed(2)}T`
  if (number >= 1_000_000_000) return `$${(number / 1_000_000_000).toFixed(2)}B`
  if (number >= 1_000_000) return `$${(number / 1_000_000).toFixed(2)}M`
  return `$${number.toLocaleString('en-US', { maximumFractionDigits: digits })}`
}

const price = (value) => {
  if (value === null || value === undefined) return '—'
  return `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: Number(value) < 1 ? 4 : 2, maximumFractionDigits: 4 })}`
}

function Change({ value, compact = false }) {
  if (value === null || value === undefined) return <span className="crypto-change is-flat">—</span>
  const positive = Number(value) >= 0
  return <span className={`crypto-change ${positive ? 'is-up' : 'is-down'}`}>{positive ? '+' : ''}{Number(value).toFixed(compact ? 2 : 3)}%</span>
}

function Sparkline({ points = [], positive = true }) {
  const values = points.length > 1 ? points : [1, 1.02, 0.99, 1.03, 1.01]
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const path = values.map((value, index) => `${index ? 'L' : 'M'} ${(index / (values.length - 1)) * 100} ${28 - ((value - min) / span) * 24}`).join(' ')
  return (
    <svg className={`crypto-sparkline ${positive ? 'is-up' : 'is-down'}`} viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">
      <path d={path} fill="none" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

function Metric({ label, value, tone = '' }) {
  return <div className="crypto-metric"><span>{label}</span><strong className={tone}>{value}</strong></div>
}

export default function CryptoPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState('market_cap')
  const [selected, setSelected] = useState('BTC')

  async function load() {
    try {
      setLoading(true)
      const payload = await fetchMpCryptoSnapshot()
      setData(payload)
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    async function initialLoad() {
      try {
        const payload = await fetchMpCryptoSnapshot()
        if (!cancelled) { setData(payload); setError('') }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    initialLoad()
    const timer = setInterval(initialLoad, 30000)
    return () => { cancelled = true; clearInterval(timer) }
  }, [])

  const items = data?.items || []
  const visibleItems = useMemo(() => {
    const filtered = items.filter((item) => `${item.symbol} ${item.name}`.toLowerCase().includes(query.toLowerCase()))
    return [...filtered].sort((a, b) => {
      if (sort === 'change') return (b.change_pct ?? -Infinity) - (a.change_pct ?? -Infinity)
      if (sort === 'volume') return (b.volume_24h ?? -Infinity) - (a.volume_24h ?? -Infinity)
      return (b.market_cap ?? -Infinity) - (a.market_cap ?? -Infinity)
    })
  }, [items, query, sort])
  const selectedCoin = items.find((item) => item.symbol === selected) || items[0]
  const stats = useMemo(() => ({
    marketCap: items.reduce((sum, item) => sum + (item.market_cap || 0), 0),
    volume: items.reduce((sum, item) => sum + (item.volume_24h || 0), 0),
    gainers: items.filter((item) => item.change_pct > 0).length,
    losers: items.filter((item) => item.change_pct < 0).length,
  }), [items])

  if (loading && !data) return <section className="mp-panel crypto-page"><div className="crypto-loading"><Activity size={18} /> Đang kết nối dữ liệu tài sản số...</div></section>
  if (error && !data) return <section className="mp-panel crypto-page"><div className="crypto-empty"><WalletCards size={24} /><strong>Không tải được tài sản số</strong><span>{error}</span><button onClick={load}>Thử lại</button></div></section>

  return (
    <section className="mp-panel crypto-page">
      <header className="crypto-page__head">
        <div>
          <div className="crypto-kicker"><Bitcoin size={14} /> DIGITAL ASSETS / MARKET MONITOR</div>
          <h2>Thị trường tài sản số</h2>
          <p>Giá giao ngay, vốn hóa và dòng thanh khoản 24 giờ trên các tài sản dẫn dắt thị trường.</p>
        </div>
        <div className="crypto-page__status">
          <span className={`gt-status-dot ${data?.freshness === 'fresh' ? 'is-live' : ''}`} />
          <span>{data?.freshness === 'fresh' ? 'LIVE FEED' : 'CACHED FEED'}</span>
          <small>{data?.source || '—'} · {data?.as_of ? new Date(data.as_of).toLocaleTimeString('vi-VN') : '—'}</small>
          <button className="crypto-icon-button" onClick={load} aria-label="Làm mới dữ liệu"><RefreshCw size={15} className={loading ? 'is-spinning' : ''} /></button>
        </div>
      </header>

      <div className="crypto-metrics">
        <Metric label="Tổng vốn hóa theo dõi" value={money(stats.marketCap, 1)} />
        <Metric label="Khối lượng 24 giờ" value={money(stats.volume, 1)} />
        <Metric label="Đang tăng / giảm" value={`${stats.gainers} / ${stats.losers}`} tone="is-positive" />
        <Metric label="Tài sản trong feed" value={items.length} />
      </div>

      <div className="crypto-layout">
        <div className="crypto-main-column">
          <div className="crypto-section-head">
            <div><span className="crypto-section-index">01</span><h3>Market board</h3></div>
            <div className="crypto-controls">
              <label className="crypto-search"><Search size={14} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm BTC, Ethereum..." /></label>
              <label className="crypto-sort"><SlidersHorizontal size={13} /><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="market_cap">Vốn hóa</option><option value="change">Biến động</option><option value="volume">Thanh khoản</option></select></label>
            </div>
          </div>
          <div className="crypto-table-wrap">
            <table className="crypto-table">
              <thead><tr><th>#</th><th>Tài sản</th><th>Giá USD</th><th>24h</th><th>Biểu đồ 7 ngày</th><th>Vốn hóa</th><th>KL 24h</th></tr></thead>
              <tbody>{visibleItems.map((coin, index) => {
                const up = (coin.change_pct ?? 0) >= 0
                return <tr key={coin.symbol} className={selectedCoin?.symbol === coin.symbol ? 'is-selected' : ''} onClick={() => setSelected(coin.symbol)}>
                  <td className="crypto-rank">{coin.market_cap_rank || index + 1}</td>
                  <td><div className="crypto-asset"><span className="crypto-asset__icon">{coin.symbol.slice(0, 1)}</span><span><strong>{coin.symbol}</strong><small>{coin.name}</small></span></div></td>
                  <td className="num crypto-price">{price(coin.price)}</td>
                  <td className="num"><Change value={coin.change_pct} compact /></td>
                  <td className="crypto-chart-cell"><Sparkline points={coin.sparkline} positive={up} /></td>
                  <td className="num crypto-muted">{money(coin.market_cap, 1)}</td>
                  <td className="num crypto-muted">{money(coin.volume_24h, 1)}</td>
                </tr>
              })}</tbody>
            </table>
            {!visibleItems.length && <div className="crypto-table-empty">Không tìm thấy tài sản phù hợp.</div>}
          </div>
        </div>

        <aside className="crypto-focus-card">
          <div className="crypto-focus-card__top"><span className="crypto-kicker">SELECTED ASSET</span><span className="crypto-live-pill"><span /> 24H</span></div>
          {selectedCoin ? <>
            <div className="crypto-focus-identity"><span className="crypto-focus-icon">{selectedCoin.symbol.slice(0, 1)}</span><div><h3>{selectedCoin.name}</h3><span>{selectedCoin.symbol} / USD</span></div></div>
            <div className="crypto-focus-price">{price(selectedCoin.price)} <Change value={selectedCoin.change_pct} /></div>
            <div className="crypto-focus-chart"><Sparkline points={selectedCoin.sparkline} positive={(selectedCoin.change_pct ?? 0) >= 0} /></div>
            <div className="crypto-focus-grid"><Metric label="Cao nhất 24h" value={price(selectedCoin.high_24h)} /><Metric label="Thấp nhất 24h" value={price(selectedCoin.low_24h)} /><Metric label="Vốn hóa" value={money(selectedCoin.market_cap)} /><Metric label="Nguồn cung" value={selectedCoin.circulating_supply ? Number(selectedCoin.circulating_supply).toLocaleString('en-US', { maximumFractionDigits: 0 }) : '—'} /></div>
            <div className="crypto-focus-note"><ArrowUpRight size={14} /> Dữ liệu được chọn theo vốn hóa thị trường</div>
          </> : <div className="crypto-empty">Chưa có asset trong feed.</div>}
        </aside>
      </div>
    </section>
  )
}
