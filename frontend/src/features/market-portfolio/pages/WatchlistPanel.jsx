import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { addMpWatchlistItem, fetchMpWatchlist, fetchMpWatchlistInstruments, removeMpWatchlistItem } from '../services/marketPortfolioApi'
import { ASSET_LABELS, filterWatchlist, formatWatchlistCap, formatWatchlistNumber } from './watchlistModel'
import './market-portfolio-panels.css'

export default function WatchlistPanel({ sessionId }) {
  const [items, setItems] = useState([])
  const [instruments, setInstruments] = useState([])
  const [symbol, setSymbol] = useState('')
  const [error, setError] = useState('')
  const [loadError, setLoadError] = useState('')
  const [catalogError, setCatalogError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('saved')
  const [assetClass, setAssetClass] = useState('')
  const request = useRef(null)
  const mounted = useRef(false)
  const mutating = useRef(false)

  const reload = useCallback(async () => {
    request.current?.abort()
    const controller = new AbortController()
    request.current = controller
    setLoading(true)
    try {
      const data = await fetchMpWatchlist(sessionId, { signal: controller.signal })
      if (mounted.current && !controller.signal.aborted) {
        setItems(data.items || [])
        setLoadError('')
      }
    } catch (err) {
      if (mounted.current && !controller.signal.aborted) setLoadError(err.message)
    } finally {
      if (mounted.current && !controller.signal.aborted) setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    mounted.current = true
    const catalogController = new AbortController()
    reload()
    fetchMpWatchlistInstruments(sessionId, { signal: catalogController.signal })
      .then(data => { if (!catalogController.signal.aborted) setInstruments(data.items || []) })
      .catch(err => { if (!catalogController.signal.aborted) setCatalogError(err.message) })
    const refresh = () => {
      if (document.visibilityState === 'visible' && !mutating.current) reload()
    }
    const timer = window.setInterval(refresh, 15000)
    document.addEventListener('visibilitychange', refresh)
    return () => {
      mounted.current = false
      request.current?.abort()
      catalogController.abort()
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', refresh)
    }
  }, [reload, sessionId])

  async function mutate(action) {
    if (mutating.current) return
    mutating.current = true
    request.current?.abort()
    setBusy(true)
    setError('')
    try {
      await action()
      if (mounted.current) await reload()
    } catch (err) {
      if (mounted.current) setError(err.message)
    } finally {
      mutating.current = false
      if (mounted.current) { setBusy(false); setLoading(false) }
    }
  }

  function onAdd(event) {
    event.preventDefault()
    if (!symbol.trim()) return
    mutate(async () => {
      const added = await addMpWatchlistItem(sessionId, symbol.trim().toUpperCase())
      if (!mounted.current) return
      setItems(current => [...current.filter(item => item.item_id !== added.item_id), added])
      setSymbol('')
      setSearch('')
      setAssetClass('')
    })
  }

  function onRemove(sym) {
    mutate(async () => {
      await removeMpWatchlistItem(sessionId, sym)
      if (mounted.current) setItems(current => current.filter(item => item.symbol !== sym))
    })
  }

  const rows = useMemo(() => filterWatchlist(items, { search, assetClass, sort }), [items, search, assetClass, sort])

  return (
    <section className="mp-watchlist-panel">
      <header className="mp-watchlist-head">
        <div>
          <span className="mp-watchlist-head__eyebrow">MARKET / WATCHLIST</span>
          <h2>Watchlist</h2>
          <p>Theo dõi cổ phiếu, chỉ số, ngoại hối, tài sản số, hàng hóa và phái sinh.</p>
        </div>
        <span className="mp-watchlist-head__count">{items.length} mã</span>
      </header>
      <div className="mp-watchlist-toolbar">
        <form className="mp-watchlist-add" onSubmit={onAdd}>
          <input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())}
            placeholder="FPT, BTC, XAU, EURUSD…" aria-label="Thêm mã tài sản"
            aria-describedby="watchlist-symbol-help" list="watchlist-instruments" maxLength={16} disabled={busy} />
          <datalist id="watchlist-instruments">{instruments.map(item => (
            <option key={item.symbol} value={item.symbol}>{item.name} · {ASSET_LABELS[item.asset_class] || 'Tài sản'}</option>
          ))}</datalist>
          <button type="submit" disabled={busy || !symbol.trim()}>{busy ? 'Đang lưu…' : '+ Thêm mã'}</button>
        </form>
        <input className="mp-watchlist-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm trong watchlist" aria-label="Tìm trong watchlist" />
        <select value={assetClass} onChange={e => setAssetClass(e.target.value)} aria-label="Loại tài sản">
          <option value="">Tất cả tài sản</option>
          {Object.entries(ASSET_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select value={sort} onChange={e => setSort(e.target.value)} aria-label="Sắp xếp watchlist">
          <option value="saved">Thứ tự đã lưu</option><option value="symbol">Mã A–Z</option>
          <option value="change_desc">Tăng giá</option><option value="change_asc">Giảm giá</option>
        </select>
      </div>
      <p id="watchlist-symbol-help" className="mp-watchlist-help">Nhập mã hoặc chọn từ gợi ý. Giá hiển thị theo đơn vị của từng tài sản.</p>
      {catalogError ? <p className="mp-watchlist-help">Chưa tải được gợi ý mã. Bạn vẫn có thể nhập mã trực tiếp.</p> : null}
      {error ? <p className="mp-error" role="alert">{error}</p> : null}
      {loadError ? <p className="mp-error" role="alert">Chưa cập nhật được watchlist: {loadError}. <button type="button" onClick={reload} disabled={busy || loading}>Thử lại</button></p> : null}
      <p className="mp-watchlist-help" role="status">{loading ? 'Đang cập nhật…' : `Hiển thị ${rows.length} / ${items.length} mã`}</p>
      {rows.length ? (
        <div className="mp-watchlist-table-wrap">
          <table className="mp-watchlist-table">
            <thead><tr><th>#</th><th>Mã tài sản</th><th>Loại</th><th>Giá</th><th>+/-</th><th>%</th><th>Vốn hóa</th><th>Dữ liệu giá</th><th>Thao tác</th></tr></thead>
            <tbody>{rows.map((item, index) => {
              const chg = item.change_pct
              const toneClass = chg == null ? '' : chg > 0 ? 'is-pos gt-px-up' : chg < 0 ? 'is-neg gt-px-dn' : 'is-ref gt-px-tc'
              const date = item.updated_at ? new Date(item.updated_at) : null
              const timestamp = date && Number.isFinite(date.getTime()) ? date.toLocaleString('vi-VN') : ''
              return <tr key={item.item_id}>
                <td className="num mp-watchlist-rank">{index + 1}</td>
                <td><strong className={`mp-watchlist-symbol ${toneClass}`}>{item.symbol}</strong><small>{item.name || item.label || '—'}</small></td>
                <td>{ASSET_LABELS[item.asset_class] || 'Chưa xác định'}</td>
                <td className={`num strong ${toneClass}`}>{formatWatchlistNumber(item.price, item)}<small className="mp-watchlist-unit">{item.unit || ''}</small></td>
                <td className={`num ${toneClass}`}>{formatWatchlistNumber(item.change, item, true)}</td>
                <td className={`num ${toneClass}`}>{chg == null ? '—' : `${chg > 0 ? '+' : ''}${Number(chg).toFixed(2)}%`}</td>
                <td className="num">{formatWatchlistCap(item)}</td>
                <td><span>{item.quote_status === 'unavailable' ? 'Chưa có giá' : item.quote_status === 'stale' ? 'Giá lưu gần nhất' : 'Đã cập nhật'}</span><small className="mp-watchlist-unit" title={item.source || ''}>{timestamp || 'Chờ nguồn dữ liệu'}</small></td>
                <td><button className="mp-watchlist-remove" type="button" onClick={() => onRemove(item.symbol)} disabled={busy} aria-label={`Bỏ theo dõi ${item.symbol}`}>Bỏ theo dõi</button></td>
              </tr>
            })}</tbody>
          </table>
        </div>
      ) : !loading && !loadError ? (
        <div className="mp-watchlist-empty"><strong>{items.length ? 'Không tìm thấy mã phù hợp' : 'Watchlist đang trống'}</strong><span>{items.length ? 'Thử thay đổi tìm kiếm hoặc loại tài sản.' : 'Thêm các mã bạn muốn theo dõi để bắt đầu.'}</span></div>
      ) : null}
    </section>
  )
}
