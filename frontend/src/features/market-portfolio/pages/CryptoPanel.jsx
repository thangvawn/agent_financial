import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Activity, ArrowUpRight, Bitcoin, Layers, RefreshCw, Search, SlidersHorizontal, TrendingUp, WalletCards } from 'lucide-react'
import { fetchMpCryptoSnapshot } from '../services'
import CryptoOrderBookWidget from './CryptoOrderBookWidget'
import TradingViewRealtimeWidget from './TradingViewRealtimeWidget'

const DEFAULT_CRYPTO_POLL_MS = 15_000
const MIN_CRYPTO_POLL_MS = 5_000
const BINANCE_STREAM_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'USDCUSDT', 'SOLUSDT', 'TRXUSDT',
  'DOGEUSDT', 'LINKUSDT', 'ADAUSDT', 'XLMUSDT', 'NEARUSDT', 'BCHUSDT', 'UNIUSDT',
  'HBARUSDT', 'LTCUSDT', 'AVAXUSDT', 'SUIUSDT', 'SHIBUSDT', 'DOTUSDT', 'PEPEUSDT',
  'ICPUSDT', 'ARBUSDT', 'FILUSDT', 'APTUSDT', 'OPUSDT', 'INJUSDT',
]
const BINANCE_SYMBOL_MAP = Object.fromEntries(BINANCE_STREAM_SYMBOLS.map((symbol) => [symbol, symbol.replace(/USDT$/, '')]))
const BINANCE_STREAM_URL = `wss://stream.binance.com:9443/stream?streams=${BINANCE_STREAM_SYMBOLS.map((symbol) => `${symbol.toLowerCase()}@miniTicker`).join('/')}`

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
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  const absolute = Math.abs(number)
  const digits = absolute >= 1 ? 2 : absolute >= 0.1 ? 4 : absolute >= 0.01 ? 5 : absolute >= 0.0001 ? 6 : absolute >= 0.000001 ? 8 : 10
  return `$${number.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
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
  const [focusTab, setFocusTab] = useState('orderbook') // 'orderbook' | 'overview' | 'chart'
  const previousQuotesRef = useRef(new Map())
  const liveQuotesRef = useRef(new Map())
  const pulseTimerRef = useRef(null)
  const [updatedSymbols, setUpdatedSymbols] = useState(() => new Set())
  const [streamStatus, setStreamStatus] = useState('connecting')

  const pulseSymbols = useCallback((symbols) => {
    if (!symbols.length) return
    setUpdatedSymbols(new Set(symbols))
    if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current)
    pulseTimerRef.current = window.setTimeout(() => setUpdatedSymbols(new Set()), 1000)
  }, [])

  const applyPayload = useCallback((payload) => {
    const mergedPayload = {
      ...payload,
      items: (payload?.items || []).map((item) => {
        const live = liveQuotesRef.current.get(item.symbol)
        if (!live) return item
        const liveTime = Date.parse(live.updated_at || '')
        const snapshotTime = Date.parse(item.updated_at || '')
        return !Number.isFinite(snapshotTime) || (Number.isFinite(liveTime) && liveTime >= snapshotTime)
          ? { ...item, ...live }
          : item
      }),
    }
    const changed = (mergedPayload.items || [])
      .filter((item) => {
        const previous = previousQuotesRef.current.get(item.symbol)
        previousQuotesRef.current.set(item.symbol, { price: item.price, updated_at: item.updated_at })
        return previous && (previous.price !== item.price || previous.updated_at !== item.updated_at)
      })
      .map((item) => item.symbol)
    pulseSymbols(changed)
    setData(mergedPayload)
  }, [pulseSymbols])

  async function load() {
    try {
      setLoading(true)
      const payload = await fetchMpCryptoSnapshot()
      applyPayload(payload)
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    let timer = null
    let controller = null
    let pollDelay = DEFAULT_CRYPTO_POLL_MS
    let failures = 0

    function schedule(success) {
      if (cancelled || document.visibilityState === 'hidden') return
      failures = success ? 0 : failures + 1
      const retryDelay = Math.min(120_000, pollDelay * (2 ** Math.min(failures, 3)))
      const delay = success
        ? pollDelay
        : retryDelay
      timer = window.setTimeout(tick, delay)
    }

    async function tick() {
      if (cancelled || document.visibilityState === 'hidden') return
      controller?.abort()
      controller = new AbortController()
      try {
        const payload = await fetchMpCryptoSnapshot({ signal: controller.signal })
        if (cancelled) return
        const serverInterval = Number(payload?.refresh_interval_seconds)
        if (Number.isFinite(serverInterval) && serverInterval > 0) {
          // Reads are cheap because the API serves the shared snapshot. Keep
          // the UI responsive at 15s while the backend owns provider refresh
          // cadence and rate limiting.
          pollDelay = Math.min(DEFAULT_CRYPTO_POLL_MS, Math.max(MIN_CRYPTO_POLL_MS, serverInterval * 1000))
        }
        applyPayload(payload)
        setError('')
        setLoading(false)
        schedule(true)
      } catch (err) {
        if (err.name === 'AbortError' || cancelled) return
        setError(err.message)
        setLoading(false)
        schedule(false)
      }
    }

    function handleVisibilityChange() {
      if (document.visibilityState !== 'visible') {
        if (timer) window.clearTimeout(timer)
        timer = null
        controller?.abort()
        return
      }
      if (!timer) tick()
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    tick()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
      controller?.abort()
      if (pulseTimerRef.current) window.clearTimeout(pulseTimerRef.current)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [applyPayload])

  useEffect(() => {
    let socket = null
    let reconnectTimer = null
    let cancelled = false
    let reconnectAttempt = 0

    function scheduleReconnect() {
      if (cancelled || document.visibilityState === 'hidden' || reconnectTimer) return
      const delay = Math.min(30_000, 1_000 * (2 ** Math.min(reconnectAttempt, 5)))
      reconnectAttempt += 1
      setStreamStatus('reconnecting')
      reconnectTimer = window.setTimeout(() => {
        reconnectTimer = null
        connect()
      }, delay)
    }

    function connect() {
      if (cancelled || document.visibilityState === 'hidden') return
      if (!window.WebSocket) {
        setStreamStatus('polling')
        return
      }
      setStreamStatus(reconnectAttempt ? 'reconnecting' : 'connecting')
      try {
        socket = new window.WebSocket(BINANCE_STREAM_URL)
      } catch {
        scheduleReconnect()
        return
      }
      socket.onopen = () => {
        reconnectAttempt = 0
        setStreamStatus('live')
      }
      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data)
          const tick = parsed?.data || parsed
          const symbol = BINANCE_SYMBOL_MAP[tick?.s]
          const numericPrice = Number(tick?.c)
          const eventTime = Number(tick?.E)
          if (!symbol || !Number.isFinite(numericPrice) || !Number.isFinite(eventTime)) return
          const updatedAt = new Date(eventTime).toISOString()
          const previousLive = liveQuotesRef.current.get(symbol)
          if (previousLive && Date.parse(previousLive.updated_at) > eventTime) return
          const openPrice = Number(tick?.o)
          const changePct = Number.isFinite(openPrice) && openPrice !== 0 ? ((numericPrice / openPrice) - 1) * 100 : null
          const high24h = Number(tick?.h)
          const low24h = Number(tick?.l)
          const liveQuote = {
            price: numericPrice,
            updated_at: updatedAt,
          }
          if (Number.isFinite(changePct)) liveQuote.change_pct = changePct
          if (Number.isFinite(high24h)) liveQuote.high_24h = high24h
          if (Number.isFinite(low24h)) liveQuote.low_24h = low24h
          liveQuotesRef.current.set(symbol, liveQuote)
          previousQuotesRef.current.set(symbol, { price: liveQuote.price, updated_at: liveQuote.updated_at })
          setData((current) => {
            if (!current?.items) return current
            return {
              ...current,
              source: 'binance_ws',
              as_of: updatedAt,
              items: current.items.map((item) => item.symbol === symbol ? { ...item, ...liveQuote } : item),
            }
          })
          pulseSymbols([symbol])
        } catch {
          // Ignore malformed provider messages; the REST poll remains the fallback.
        }
      }
      socket.onerror = () => {
        setStreamStatus('polling')
        socket?.close()
      }
      socket.onclose = () => {
        socket = null
        if (!cancelled && document.visibilityState === 'visible') scheduleReconnect()
      }
    }

    function handleVisibilityChange() {
      if (document.visibilityState === 'hidden') {
        if (reconnectTimer) window.clearTimeout(reconnectTimer)
        reconnectTimer = null
        socket?.close()
        socket = null
        setStreamStatus('polling')
        return
      }
      if (!socket && !reconnectTimer) {
        reconnectAttempt = 0
        connect()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    connect()
    return () => {
      cancelled = true
      if (reconnectTimer) window.clearTimeout(reconnectTimer)
      socket?.close()
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [pulseSymbols])

  const items = useMemo(() => data?.items || [], [data?.items])
  const visibleItems = useMemo(() => {
    const filtered = items.filter((item) => `${item.symbol} ${item.name}`.toLowerCase().includes(query.toLowerCase()))
    return [...filtered].sort((a, b) => {
      if (sort === 'change') return (b.change_pct ?? -Infinity) - (a.change_pct ?? -Infinity)
      if (sort === 'volume') return (b.volume_24h ?? -Infinity) - (a.volume_24h ?? -Infinity)
      return (b.market_cap ?? -Infinity) - (a.market_cap ?? -Infinity)
    })
  }, [items, query, sort])
  const selectedCoin = items.find((item) => item.symbol === selected) || items[0]
  const latestQuoteAt = useMemo(() => {
    const timestamps = items.map((item) => new Date(item.updated_at || 0).getTime()).filter(Number.isFinite)
    return timestamps.length ? new Date(Math.max(...timestamps)).toLocaleTimeString('vi-VN') : null
  }, [items])
  const stats = useMemo(() => ({
    marketCap: items.reduce((sum, item) => sum + (item.market_cap || 0), 0),
    volume: items.reduce((sum, item) => sum + (item.volume_24h || 0), 0),
    gainers: items.filter((item) => item.change_pct > 0).length,
    losers: items.filter((item) => item.change_pct < 0).length,
  }), [items])

  if (loading && !data) return <section className="mp-panel crypto-page"><div className="crypto-loading"><Activity size={18} /> Đang kết nối dữ liệu tài sản số...</div></section>
  if (error && !data) return <section className="mp-panel crypto-page"><div className="crypto-empty"><WalletCards size={24} /><strong>Không tải được tài sản số</strong><span>{error}</span><button type="button" onClick={load} disabled={loading}>Thử lại</button></div></section>

  return (
    <section className="mp-panel crypto-page">
      <header className="crypto-page__head">
        <div>
          <div className="crypto-kicker"><Bitcoin size={14} /> TÀI SẢN SỐ</div>
          <h2>Thị trường tài sản số</h2>
          <p>Giá giao ngay, vốn hóa và dòng thanh khoản 24 giờ trên các tài sản dẫn dắt thị trường.</p>
        </div>
        <div className="crypto-page__status">
          <span className={`gt-status-dot ${streamStatus === 'live' || data?.freshness === 'fresh' ? 'is-live' : ''}`} />
          <span>{streamStatus === 'live' ? 'TICK LIVE' : data?.freshness === 'fresh' ? 'LIVE FEED' : 'CACHED FEED'}</span>
          <small>{streamStatus === 'live' ? 'Binance WS' : data?.source || '—'} · quote {latestQuoteAt || '—'}</small>
          <button type="button" className="crypto-icon-button" onClick={load} disabled={loading} aria-label="Làm mới dữ liệu"><RefreshCw size={15} className={loading ? 'is-spinning' : ''} /></button>
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
            <div><h3>Bảng giá thị trường</h3></div>
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
                return <tr key={coin.symbol} className={`${selectedCoin?.symbol === coin.symbol ? 'is-selected' : ''} ${updatedSymbols.has(coin.symbol) ? 'is-updating' : ''}`} onClick={() => setSelected(coin.symbol)}>
                  <td className="crypto-rank">{coin.market_cap_rank || index + 1}</td>
                  <td><div className="crypto-asset"><span className="crypto-asset__icon">{coin.symbol.slice(0, 1)}</span><span><strong className={up ? 'is-up' : 'is-down'}>{coin.symbol}</strong><small>{coin.name}</small></span></div></td>
                  <td className={`num crypto-price ${up ? 'is-up' : 'is-down'} ${updatedSymbols.has(coin.symbol) ? 'is-updating' : ''}`}>{price(coin.price)}</td>
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
          <div className="crypto-focus-card__top">
            <span className="crypto-kicker">TÀI SẢN ĐANG CHỌN</span>
            <span className="crypto-live-pill"><span /> 24H</span>
          </div>
          {selectedCoin ? (() => {
            const focusUp = (selectedCoin.change_pct ?? 0) >= 0
            return (
              <>
                <div className="crypto-focus-identity">
                  <span className="crypto-focus-icon">{selectedCoin.symbol.slice(0, 1)}</span>
                  <div>
                    <h3>{selectedCoin.name}</h3>
                    <span className={focusUp ? 'is-up' : 'is-down'}>{selectedCoin.symbol} / USD</span>
                  </div>
                </div>

                <div className={`crypto-focus-price ${focusUp ? 'is-up' : 'is-down'}`}>
                  {price(selectedCoin.price)} <Change value={selectedCoin.change_pct} />
                </div>

                <div className="crypto-focus-tabs">
                  <button
                    type="button"
                    className={`crypto-focus-tab ${focusTab === 'orderbook' ? 'is-active' : ''}`}
                    onClick={() => setFocusTab('orderbook')}
                  >
                    <Layers size={13} /> Sổ lệnh L2
                  </button>
                  <button
                    type="button"
                    className={`crypto-focus-tab ${focusTab === 'overview' ? 'is-active' : ''}`}
                    onClick={() => setFocusTab('overview')}
                  >
                    <Activity size={13} /> Thống kê
                  </button>
                  <button
                    type="button"
                    className={`crypto-focus-tab ${focusTab === 'chart' ? 'is-active' : ''}`}
                    onClick={() => setFocusTab('chart')}
                  >
                    <TrendingUp size={13} /> Biểu đồ TV
                  </button>
                </div>

                {focusTab === 'orderbook' && (
                  <CryptoOrderBookWidget symbol={selectedCoin.symbol} basePrice={selectedCoin.price} />
                )}

                {focusTab === 'overview' && (
                  <>
                    <div className="crypto-focus-chart">
                      <Sparkline points={selectedCoin.sparkline} positive={focusUp} />
                    </div>
                    <div className="crypto-focus-grid">
                      <Metric label="Cao nhất 24h" value={price(selectedCoin.high_24h)} />
                      <Metric label="Thấp nhất 24h" value={price(selectedCoin.low_24h)} />
                      <Metric label="Vốn hóa" value={money(selectedCoin.market_cap)} />
                      <Metric label="Nguồn cung" value={selectedCoin.circulating_supply ? Number(selectedCoin.circulating_supply).toLocaleString('en-US', { maximumFractionDigits: 0 }) : '—'} />
                    </div>
                  </>
                )}

                {focusTab === 'chart' && (
                  <div style={{ marginTop: '8px' }}>
                    <TradingViewRealtimeWidget symbol={selectedCoin.symbol} height={480} />
                  </div>
                )}

                <div className="crypto-focus-note">
                  <ArrowUpRight size={14} /> Dữ liệu L2 WebSocket kết nối trực tiếp sàn Binance
                </div>
              </>
            )
          })() : <div className="crypto-empty">Chưa có asset trong feed.</div>}
        </aside>
      </div>
    </section>
  )
}
