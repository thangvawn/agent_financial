import { useCallback, useEffect, useMemo, useState } from 'react'

import { addMpWatchlistItem, fetchMpWatchlist, removeMpWatchlistItem } from '../services/marketPortfolioApi'
import { fetchVnSnapshot } from '../services/dataHubApi'
import { formatVnd } from './formatMoney'
import './market-portfolio-panels.css'

export default function WatchlistPanel({ sessionId }) {
  const [items, setItems] = useState([])
  const [symbol, setSymbol] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [quotes, setQuotes] = useState([])
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('market_cap_desc')

  const reload = useCallback(async () => {
    const data = await fetchMpWatchlist(sessionId)
    setItems(data.items || [])
    const quoteData = await fetchVnSnapshot({ sort: 'market_cap_desc', limit: 300 })
    setQuotes(quoteData.items || [])
  }, [sessionId])

  useEffect(() => {
    let cancelled = false
    reload().catch((err) => {
      if (!cancelled) setError(err.message)
    })
    const timer = window.setInterval(() => reload().catch(() => {}), 15000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [reload])

  async function onAdd(event) {
    event.preventDefault()
    if (!symbol.trim()) return
    setBusy(true)
    setError('')
    try {
      await addMpWatchlistItem(sessionId, symbol.trim().toUpperCase())
      setSymbol('')
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const rows = useMemo(() => {
    const quoteMap = new Map(quotes.map((quote) => [quote.symbol, quote]))
    const needle = search.trim().toUpperCase()
    return items
      .map((item) => ({ ...item, ...(quoteMap.get(item.symbol) || {}) }))
      .filter((item) => !needle || item.symbol.includes(needle) || (item.name || '').toUpperCase().includes(needle))
      .sort((a, b) => {
        if (sort === 'change_desc') return Number(b.change_pct ?? -Infinity) - Number(a.change_pct ?? -Infinity)
        if (sort === 'change_asc') return Number(a.change_pct ?? Infinity) - Number(b.change_pct ?? Infinity)
        return Number(b.market_cap ?? -1) - Number(a.market_cap ?? -1)
      })
  }, [items, quotes, search, sort])

  async function onRemove(sym) {
    setBusy(true)
    setError('')
    try {
      await removeMpWatchlistItem(sessionId, sym)
      await reload()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="mp-watchlist-panel">
      <header className="mp-watchlist-head">
        <div>
          <span className="mp-watchlist-head__eyebrow">MARKET / WATCHLIST</span>
          <h2>Watchlist</h2>
          <p>Theo dõi giá, biến động và vốn hóa các mã bạn quan tâm.</p>
        </div>
        <span className="mp-watchlist-head__count">{items.length} mã</span>
      </header>
      <div className="mp-watchlist-toolbar">
        <form className="mp-watchlist-add" onSubmit={onAdd}>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Thêm mã (FPT, VCB…)"
            aria-label="Thêm mã cổ phiếu"
            maxLength={12}
            disabled={busy}
          />
          <button type="submit" disabled={busy || !symbol.trim()}>
            {busy ? 'Đang lưu…' : '+ Thêm mã'}
          </button>
        </form>
        <input className="mp-watchlist-search" value={search} onChange={(e) => setSearch(e.target.value.toUpperCase())} placeholder="Tìm trong watchlist" aria-label="Tìm trong watchlist" />
        <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sắp xếp watchlist">
          <option value="market_cap_desc">Vốn hóa</option>
          <option value="change_desc">Tăng giá</option>
          <option value="change_asc">Giảm giá</option>
        </select>
      </div>
      {error ? <p className="mp-error" role="alert">{error}. Hãy kiểm tra mã và thử lại.</p> : null}
      {rows.length ? (
        <div className="mp-watchlist-table-wrap">
          <table className="mp-watchlist-table">
            <thead><tr><th>#</th><th>Mã CK</th><th>Giá</th><th>+/-</th><th>%</th><th>Vốn hóa (tỷ)</th><th>Thao tác</th></tr></thead>
            <tbody>{rows.map((item, index) => {
              const positive = Number(item.change_pct || 0) >= 0
              return <tr key={item.item_id}>
                <td className="num mp-watchlist-rank">{index + 1}</td>
                <td><strong className="mp-watchlist-symbol">{item.symbol}</strong><small>{item.name || item.label || '—'}</small></td>
                <td className="num strong">{formatVnd(item.price)}</td>
                <td className={`num ${positive ? 'is-pos' : 'is-neg'}`}>{item.change == null ? '—' : formatVnd(item.change)}</td>
                <td className={`num ${positive ? 'is-pos' : 'is-neg'}`}>{item.change_pct == null ? '—' : `${positive ? '+' : ''}${Number(item.change_pct).toFixed(2)}%`}</td>
                <td className="num">{item.market_cap == null ? '—' : Number(item.market_cap).toLocaleString('vi-VN')}</td>
                <td><button className="mp-watchlist-remove" type="button" onClick={() => onRemove(item.symbol)} disabled={busy}>Bỏ theo dõi</button></td>
              </tr>
            })}</tbody>
          </table>
        </div>
      ) : (
        <div className="mp-watchlist-empty"><strong>{items.length ? 'Không tìm thấy mã phù hợp' : 'Watchlist đang trống'}</strong><span>{items.length ? 'Thử tìm bằng mã khác.' : 'Thêm các mã bạn muốn theo dõi để bắt đầu.'}</span></div>
      )}
    </section>
  )
}
