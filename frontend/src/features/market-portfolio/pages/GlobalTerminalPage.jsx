import { useEffect, useMemo, useRef, useState } from 'react'

import {
  fetchGlobalTerminal,
  fetchInstrumentHistory,
  fetchVnSnapshot,
  fetchMpCompanyProfile,
  fetchMpCompanyShareholders
} from '../services'
import { fetchNewsFeed } from '../../news/services/newsApi'
import { fetchFinancialCockpit } from '../../bctc/services/financialsApi'
import LightweightChartPanel from './LightweightChartPanel'
import './global-terminal.css'

const TAB_CATEGORY = {
  dashboard: 'dashboard',
  markets: 'indices',
  indices: 'indices',
  vn_stocks: 'vn_stocks',
}

const TAB_MAP = {
  dashboard: { view: 'vn_stocks', default_symbol: 'FPT' },
  indices: { view: 'indices', default_symbol: 'VNINDEX' },
}

const DEFAULT_TABS = [
  { id: 'dashboard', label: 'Dashboard', default_symbol: 'VNINDEX' },
  { id: 'vn_stocks', label: 'VN Stocks', default_symbol: 'FPT' },
  { id: 'markets', label: 'Indices', default_symbol: 'VNINDEX' },
]

const PRIORITY = ['VNINDEX', 'VN30', 'HNXINDEX', 'FPT', 'VCB', 'MWG']

const CHART_PRESETS = [
  { id: '1D', label: '1D', period: '1d', interval: '5m' },
  { id: '5D', label: '5D', period: '5d', interval: '15m' },
  { id: '1M', label: '1M', period: '1mo', interval: '1d' },
  { id: '3M', label: '3M', period: '3mo', interval: '1d' },
  { id: '6M', label: '6M', period: '6mo', interval: '1d' },
  { id: 'YTD', label: 'YTD', period: '1y', interval: '1d', ytd: true },
  { id: '1Y', label: '1Y', period: '1y', interval: '1d' },
  { id: '2Y', label: '2Y', period: '2y', interval: '1d' },
  { id: '5Y', label: '5Y', period: '5y', interval: '1wk' },
  { id: 'MAX', label: 'Max', period: 'max', interval: '1mo' },
]

const DEFAULT_PRESET_ID = '6M'

export default function GlobalTerminalPage({ activeTab = 'dashboard', onOpenProLab, onOpenNews }) {
  const mappedView = TAB_MAP[activeTab]?.view || 'dashboard'
  const isVnMode = activeTab === 'dashboard'
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState(mappedView)
  const [command, setCommand] = useState('')
  const [selectedSymbol, setSelectedSymbol] = useState('VNINDEX')
  const [presetId, setPresetId] = useState(DEFAULT_PRESET_ID)
  const [history, setHistory] = useState(null)
  const [historyError, setHistoryError] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [refreshTick, setRefreshTick] = useState(0)
  const [historyRefreshTick, setHistoryRefreshTick] = useState(0)
  const [vnSnapshot, setVnSnapshot] = useState(null)
  const [vnLoading, setVnLoading] = useState(false)
  const [vnError, setVnError] = useState('')
  const [vnSort, setVnSort] = useState('market_cap_desc')
  const [vnPageSize, setVnPageSize] = useState(50)
  const [vnExchange, setVnExchange] = useState('')
  const [vnSearch, setVnSearch] = useState('')
  const [debouncedVnSearch, setDebouncedVnSearch] = useState('')
  const [detailedMode, setDetailedMode] = useState(false)
  const [activeDetailSymbol, setActiveDetailSymbol] = useState(null)
  
  const terminalRequestSeqRef = useRef(0)
  const historyRequestSeqRef = useRef(0)
  const vnRequestSeqRef = useRef(0)
  const historyCacheRef = useRef(new Map())
  const commandInputRef = useRef(null)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedVnSearch(vnSearch.trim()), 320)
    return () => window.clearTimeout(timer)
  }, [vnSearch])

  useEffect(() => {
    function handleShortcut(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        commandInputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [])

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()

    async function run() {
      const requestId = ++terminalRequestSeqRef.current
      setLoading(true)
      setError('')
      try {
        const data = await fetchGlobalTerminal({ view: activeView, signal: controller.signal })
        if (cancelled || requestId !== terminalRequestSeqRef.current) return
        setPayload(data)
        setSelectedSymbol((current) => current || data?.terminal?.default_symbol || 'VNINDEX')
      } catch (err) {
        if (err.name === 'AbortError') return
        if (cancelled || requestId !== terminalRequestSeqRef.current) return
        setError(err.message)
      } finally {
        if (!cancelled && requestId === terminalRequestSeqRef.current) setLoading(false)
      }
    }

    run()
    // Backend snapshot TTL is 15s, so keep the board/ranking near realtime.
    const timer = window.setInterval(run, 15000)
    return () => {
      cancelled = true
      controller.abort()
      window.clearInterval(timer)
    }
  }, [activeView, refreshTick])

  useEffect(() => {
    if (activeView !== 'vn_stocks') return undefined
    let cancelled = false
    const controller = new AbortController()
    async function run() {
      const requestId = ++vnRequestSeqRef.current
      setVnLoading(true)
      setVnError('')
      try {
        const data = await fetchVnSnapshot({
          sort: vnSort,
          exchange: vnExchange,
          search: debouncedVnSearch,
          limit: vnPageSize,
          signal: controller.signal,
        })
        if (cancelled || requestId !== vnRequestSeqRef.current) return
        setVnSnapshot(data)
      } catch (err) {
        if (err.name === 'AbortError') return
        if (cancelled || requestId !== vnRequestSeqRef.current) return
        setVnError(err.message)
      } finally {
        if (!cancelled && requestId === vnRequestSeqRef.current) setVnLoading(false)
      }
    }
    run()
    // The backend snapshot has a 15s TTL; refresh the board and its rank near realtime.
    const timer = window.setInterval(run, 15000)
    return () => {
      cancelled = true
      controller.abort()
      window.clearInterval(timer)
    }
  }, [activeView, vnSort, vnExchange, debouncedVnSearch, vnPageSize, refreshTick])

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()

    async function run() {
      const requestId = ++historyRequestSeqRef.current
      const preset = CHART_PRESETS.find((item) => item.id === presetId) || CHART_PRESETS[4]
      const cacheKey = `${selectedSymbol}:${preset.id}`
      const cached = historyCacheRef.current.get(cacheKey)
      if (cached?.refreshVersion === historyRefreshTick) {
        setHistory(cached.data)
        setHistoryError('')
        setHistoryLoading(false)
        return
      }
      setHistoryLoading(true)
      setHistoryError('')
      setHistory(null)
      try {
        const data = await fetchInstrumentHistory(selectedSymbol, {
          period: preset.period,
          interval: preset.interval,
          signal: controller.signal,
        })
        if (cancelled || requestId !== historyRequestSeqRef.current) return
        const normalized = { ...data, presetId: preset.id, ytd: Boolean(preset.ytd) }
        historyCacheRef.current.set(cacheKey, { data: normalized, refreshVersion: historyRefreshTick })
        setHistory(normalized)
      } catch (err) {
        if (err.name === 'AbortError') return
        if (cancelled || requestId !== historyRequestSeqRef.current) return
        setHistoryError(err.message)
      } finally {
        if (!cancelled && requestId === historyRequestSeqRef.current) setHistoryLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
      controller.abort()
    }
  }, [selectedSymbol, presetId, historyRefreshTick])

  // Sync activeView when parent tab changes
  useEffect(() => {
    const mapped = TAB_MAP[activeTab]?.view || 'dashboard'
    setActiveView(mapped)
    const defaultSymbol = TAB_MAP[activeTab]?.default_symbol
    if (defaultSymbol) setSelectedSymbol(defaultSymbol)
    setActiveDetailSymbol(null) // Reset detail view when changing tab
  }, [activeTab])

  function handleTab(nextView) {
    setActiveView(nextView)
    const tabDefault = payload?.navigation?.tabs?.find((tab) => tab.id === nextView)?.default_symbol
      || DEFAULT_TABS.find((tab) => tab.id === nextView)?.default_symbol
    if (tabDefault) setSelectedSymbol(tabDefault)
    setActiveDetailSymbol(null)
  }

  function handleRefreshAll() {
    setRefreshTick((current) => current + 1)
    setHistoryRefreshTick((current) => current + 1)
  }

  function handleCommandSubmit(event) {
    event.preventDefault()
    const raw = command.trim()
    if (!raw) return
    const normalized = raw.toLowerCase().replace(/\s+/g, '_')
    const tab = (payload?.navigation?.tabs || DEFAULT_TABS).find(
      (item) => item.id === normalized || item.label.toLowerCase() === raw.toLowerCase()
    )
    if (tab) {
      handleTab(tab.id)
    } else {
      const sym = raw.toUpperCase()
      setSelectedSymbol(sym)
      if (isVnTab) setActiveDetailSymbol(sym)
    }
    setCommand('')
  }

  function handleSelectRow(sym) {
    setSelectedSymbol(sym)
    const isIndex = ['VNINDEX', 'VN30', 'HNXINDEX', 'HNX30', 'UPCOM'].includes(sym)
    if (!isIndex && isVnTab) {
      setActiveDetailSymbol(sym)
    } else {
      setActiveDetailSymbol(null)
    }
  }

  if (loading && !payload) {
    return <TerminalLoadingState />
  }

  if (error && !payload) {
    return (
      <section className="global-terminal global-terminal--error" role="alert">
        <h2>Dữ liệu thị trường chưa sẵn sàng</h2>
        <p>Không thể kết nối nguồn dữ liệu lúc này. Hãy thử lại sau ít phút.</p>
        <button type="button" className="gt-error__retry" onClick={() => setRefreshTick((n) => n + 1)}>
          Thử lại
        </button>
      </section>
    )
  }

  const widgets = payload?.widgets || {}
  let tabs = payload?.navigation?.tabs || DEFAULT_TABS
  tabs = tabs.filter((tab) => tab.id !== 'ai_chat')
  if (!tabs.some((tab) => tab.id === 'vn_stocks')) {
    const vnTabDef = DEFAULT_TABS.find((tab) => tab.id === 'vn_stocks')
    if (vnTabDef) tabs = [tabs[0], vnTabDef, ...tabs.slice(1)]
  }
  const isVnTab = activeView === 'vn_stocks' || isVnMode
  const watchlist = isVnTab
    ? (vnSnapshot?.items || []).map((item) => ({
        symbol: item.symbol,
        name: item.name,
        price: item.price,
        market_cap: item.market_cap,
        shares_outstanding: item.shares_outstanding,
        change_pct: item.change_pct,
        change: item.change,
        focus: item.exchange ? `${item.exchange}${item.name ? ` · ${item.name}` : ''}` : item.name,
        volume: item.volume,
      }))
    : buildWatchlist(widgets, activeView)
  const tickerItems = payload?.ticker_tape || []
  const indexItems = sortByPriority([...(widgets.global_indices || []), ...(widgets.global_snapshot || [])])
  const selectedQuote = isVnTab
    ? (vnSnapshot?.items || []).find((item) => item.symbol === selectedSymbol)
    : findQuote(widgets, selectedSymbol)

  return (
    <section className="global-terminal">
      <CompactSearchBar
        inputRef={commandInputRef}
        command={command}
        onCommandChange={setCommand}
        onCommandSubmit={handleCommandSubmit}
        timestamp={payload?.terminal?.as_of}
        syncing={loading || vnLoading || historyLoading}
        onRefresh={handleRefreshAll}
      />

      {activeView !== 'indices' ? (
        <IndexCardsRow tickerItems={tickerItems} selectedSymbol={selectedSymbol} onSelect={handleSelectRow} />
      ) : null}

      {isVnTab ? (
        activeDetailSymbol ? (
          <VnDetailedTickerPage
            symbol={activeDetailSymbol}
            onBack={() => setActiveDetailSymbol(null)}
            quote={selectedQuote}
            history={history}
            historyLoading={historyLoading}
            historyError={historyError}
            presetId={presetId}
            onPresetChange={setPresetId}
            onRetryHistory={() => setHistoryRefreshTick((n) => n + 1)}
            onOpenNews={onOpenNews}
            onSelect={handleSelectRow}
          />
        ) : (
          <div className="gt-full-workspace">
            <FilterChipsBar
              sort={vnSort}
              onSortChange={setVnSort}
              exchange={vnExchange}
              onExchangeChange={setVnExchange}
              search={vnSearch}
              onSearchChange={setVnSearch}
              total={vnSnapshot?.total}
              showing={vnSnapshot?.items?.length || 0}
              loading={vnLoading}
              freshness={vnSnapshot?.freshness}
              asOf={vnSnapshot?.as_of}
              pageSize={vnPageSize}
              onPageSizeChange={setVnPageSize}
              detailedMode={detailedMode}
              onDetailedModeChange={setDetailedMode}
            />
            {detailedMode ? (
              <VnPriceBoard
                items={vnSnapshot?.items || []}
                selectedSymbol={selectedSymbol}
                onSelect={handleSelectRow}
                total={vnSnapshot?.total}
                loading={vnLoading}
                error={vnError}
                freshness={vnSnapshot?.freshness}
                asOf={vnSnapshot?.as_of}
              />
            ) : (
              <VnOverviewTable
                items={vnSnapshot?.items || []}
                selectedSymbol={selectedSymbol}
                onSelect={handleSelectRow}
                total={vnSnapshot?.total}
                loading={vnLoading}
                error={vnError}
                freshness={vnSnapshot?.freshness}
                asOf={vnSnapshot?.as_of}
              />
            )}
          </div>
        )
      ) : activeView === 'indices' ? (
        <IndicesMarketBoard items={indexItems} selectedSymbol={selectedSymbol} onSelect={handleSelectRow} />
      ) : (
        <div className="gt-full-workspace gt-full-workspace--indices">
          <aside className="gt-indices-rail">
            <Watchlist
              title={watchlistTitle(activeView)}
              items={watchlist}
              selectedSymbol={selectedSymbol}
              onSelect={setSelectedSymbol}
              vnControls={null}
            />
          </aside>
          <main className="gt-indices-main">
            <InstrumentHero quote={selectedQuote} history={history} symbol={selectedSymbol} />
            <InstrumentChart
              history={history}
              loading={historyLoading}
              error={historyError}
              presetId={presetId}
              onPresetChange={setPresetId}
              onRetry={() => setHistoryRefreshTick((n) => n + 1)}
            />
            <InstrumentNews items={widgets.market_news || []} onOpenNews={onOpenNews} />
          </main>
          <aside className="gt-indices-sidebar">
            <MarketPulseCard pulse={widgets.market_pulse || {}} />
            <TrustFeedCard trust={payload?.trust} topics={payload?.topics || []} />
          </aside>
        </div>
      )}

      <StatusBar
        topics={payload?.topics || []}
        timestamp={payload?.terminal?.as_of}
        source={history?.source}
      />
    </section>
  )
}

/* ====================== Compact Search Bar ====================== */
function CompactSearchBar({ inputRef, command, onCommandChange, onCommandSubmit, timestamp, syncing, onRefresh }) {
  return (
    <header className="gt-search-bar">
      <form className="gt-search-bar__form" onSubmit={onCommandSubmit}>
        <span className="gt-search-bar__icon" aria-hidden="true">⌕</span>
        <input
          ref={inputRef}
          aria-label="Tìm mã cổ phiếu"
          value={command}
          onChange={(event) => onCommandChange(event.target.value)}
          placeholder="Tìm mã cổ phiếu… (FPT, VCB, VNINDEX)"
        />
        <kbd className="gt-search-bar__kbd">⌘K</kbd>
      </form>
      <div className="gt-search-bar__status">
        <span className={`gt-search-bar__dot ${syncing ? 'is-syncing' : ''}`} aria-hidden="true" />
        <span className="gt-search-bar__live">{syncing ? 'SYNC' : 'LIVE'}</span>
        <span>{formatTimestamp(timestamp)}</span>
        <button
          type="button"
          className="gt-search-bar__refresh"
          onClick={onRefresh}
          disabled={syncing}
          aria-label="Làm mới dữ liệu"
        >
          ↻
        </button>
      </div>
    </header>
  )
}

function getIndexCardSparkline(symbol, changePct, width = 68, height = 28) {
  const seed = symbol.charCodeAt(0) + (symbol.charCodeAt(1) || 0)
  const points = 12
  const prices = []
  let current = 100
  prices.push(current)
  for (let i = 1; i < points - 1; i++) {
    const factor = Math.sin(seed + i) * 8
    current += factor
    prices.push(current)
  }
  prices.push(100 + (Number(changePct) || 0) * 12)
  
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  return prices
    .map((val, idx) => {
      const x = (idx / (points - 1)) * width
      const y = height - ((val - min) / range) * (height - 4) - 2
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
}

function getStockSparklinePath(symbol, changePct, width = 60, height = 20) {
  const seed = symbol.charCodeAt(0) + (symbol.charCodeAt(1) || 0) + (symbol.charCodeAt(2) || 0)
  const points = 10
  const prices = []
  let current = 50
  prices.push(current)
  for (let i = 1; i < points - 1; i++) {
    const factor = Math.cos(seed * i) * 6
    current += factor
    prices.push(current)
  }
  prices.push(50 + (Number(changePct) || 0) * 8)
  
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  return prices
    .map((val, idx) => {
      const x = (idx / (points - 1)) * width
      const y = height - ((val - min) / range) * (height - 4) - 2
      return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
}

function buildStockMiniChart(row, width = 60, height = 24) {
  const ref = Number(row.ref_price || row.price || 1)
  const close = Number(row.price || ref)
  const low = Number(row.low || Math.min(ref, close))
  const high = Number(row.high || Math.max(ref, close))
  const spread = Math.max(high - low, Math.abs(close - ref) * 0.8, ref * 0.004)
  const seed = [...String(row.symbol || '')].reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const pointCount = 16
  const prices = Array.from({ length: pointCount }, (_, index) => {
    const progress = index / (pointCount - 1)
    if (index === 0) return ref
    if (index === pointCount - 1) return close
    const drift = ref + (close - ref) * progress
    const wave = Math.sin(seed * 0.17 + index * 1.35) * spread * 0.18 * (1 - progress * 0.35)
    return Math.min(high + spread * 0.12, Math.max(low - spread * 0.12, drift + wave))
  })
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || Math.max(Math.abs(max) * 0.01, 1)
  const point = (value, index) => ({
    x: (index / Math.max(prices.length - 1, 1)) * width,
    y: height - ((value - min) / range) * (height - 4) - 2,
  })
  const coords = prices.map(point)
  const path = coords.map((p, index) => `${index === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  const last = coords[coords.length - 1]
  const first = coords[0]
  const area = `${path} L ${last.x.toFixed(1)} ${height} L ${first.x.toFixed(1)} ${height} Z`
  const refY = Number.isFinite(ref) && ref > 0 ? point(ref, 0).y : null
  return { path, area, last, refY, aboveReference: close >= ref }
}

/* ====================== Index Cards Row ====================== */
function IndexCardsRow({ tickerItems, selectedSymbol, onSelect }) {
  const indices = useMemo(() => {
    if (!tickerItems?.length) return []
    const priority = ['VNINDEX', 'VN30', 'HNXINDEX', 'HNX30', 'UPCOM']
    const sorted = [...tickerItems].sort((a, b) => {
      const ai = priority.indexOf(a.symbol)
      const bi = priority.indexOf(b.symbol)
      if (ai === -1 && bi === -1) return 0
      if (ai === -1) return 1
      if (bi === -1) return -1
      return ai - bi
    })
    return sorted.slice(0, 4)
  }, [tickerItems])

  if (!indices.length) {
    return (
      <div className="gt-index-cards">
        {[0, 1, 2].map((i) => (
          <div key={i} className="gt-index-card gt-index-card--skeleton">
            <div className="gt-skel gt-skel--bar" style={{ width: '60%' }} />
            <div className="gt-skel gt-skel--price" style={{ width: '40%', height: '28px' }} />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="gt-index-cards">
      {indices.map((item) => {
        const positive = Number(item.change_pct) >= 0
        return (
          <button
            type="button"
            key={item.symbol}
            className={`gt-index-card ${item.symbol === selectedSymbol ? 'is-selected' : ''}`}
            onClick={() => onSelect(item.symbol)}
          >
            <div className="gt-index-card__main">
              <span className="gt-index-card__name">{item.symbol}</span>
              <span className="gt-index-card__price">{formatPrice(item.price)}</span>
              <span className={`gt-index-card__change ${positive ? 'is-pos' : 'is-neg'}`}>
                {formatChange(item.change_pct)}
              </span>
            </div>
            <div className="gt-index-card__chart">
              <svg width="68" height="28" viewBox="0 0 68 28">
                <path
                  d={getIndexCardSparkline(item.symbol, item.change_pct)}
                  fill="none"
                  stroke={positive ? 'var(--pos)' : 'var(--neg)'}
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </button>
        )
      })}
    </div>
  )
}

const INDEX_REGIONS = [
  { id: 'vietnam', label: 'Việt Nam', symbols: ['VNINDEX', 'VN30', 'HNXINDEX', 'UPCOMINDEX'] },
  { id: 'us', label: 'Mỹ', symbols: ['SPX', 'NDX', 'RUT'] },
  { id: 'europe', label: 'Châu Âu', symbols: ['DAX', 'FTSE'] },
  { id: 'asia', label: 'Châu Á', symbols: ['NIKKEI', 'HANGSENG'] },
]

function IndicesMarketBoard({ items, selectedSymbol, onSelect }) {
  const lookup = new Map(items.map((item) => [item.symbol, item]))
  return (
    <section className="gt-indices-board" aria-label="Các chỉ số thị trường">
      {INDEX_REGIONS.map((region) => {
        const regionItems = region.symbols.map((symbol) => lookup.get(symbol)).filter(Boolean)
        return (
          <section className="gt-indices-board__section" key={region.id} aria-labelledby={`gt-index-region-${region.id}`}>
            <h2 id={`gt-index-region-${region.id}`}>{region.label}</h2>
            {regionItems.length ? (
              <div className="gt-indices-board__table-wrap">
                <table className="gt-indices-board__table">
                  <thead>
                    <tr><th>#</th><th>Mã CK</th><th>Giá</th><th>+/-</th><th>%</th><th>Biểu đồ</th></tr>
                  </thead>
                  <tbody>
                    {regionItems.map((item, index) => (
                      <IndexMarketRow
                        key={item.symbol}
                        item={item}
                        index={index + 1}
                        selected={item.symbol === selectedSymbol}
                        onSelect={onSelect}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="gt-indices-board__empty">Chưa có dữ liệu chỉ số.</div>
            )}
          </section>
        )
      })}
    </section>
  )
}

function IndexMarketRow({ item, index, selected, onSelect }) {
  const change = Number(item.change_pct || 0)
  const positive = change >= 0
  const price = Number(item.price || 0)
  const previous = price - Number(item.change || 0)
  const path = buildIndexMiniPath(item.symbol, previous || price, price)
  return (
    <tr className={selected ? 'is-selected' : ''} onClick={() => onSelect(item.symbol)}>
      <td className="num gt-indices-board__rank">{index}</td>
      <td className="gt-indices-board__symbol"><strong>{item.symbol}</strong><small>{item.name || item.focus || '—'}</small></td>
      <td className="num strong">{formatPrice(item.price)}</td>
      <td className={`num ${positive ? 'is-pos' : 'is-neg'}`}>{formatSigned(item.change)}</td>
      <td className={`num ${positive ? 'is-pos' : 'is-neg'}`}>{formatChange(item.change_pct)}</td>
      <td className="gt-indices-board__chart">
        <svg width="84" height="26" viewBox="0 0 84 26" role="img" aria-label={`Biểu đồ ${item.symbol}`}>
          <line x1="0" x2="84" y1={path.refY} y2={path.refY} className="gt-indices-board__ref" />
          <path d={path.area} className={`gt-indices-board__area ${positive ? 'is-up' : 'is-down'}`} />
          <path d={path.path} className={`gt-indices-board__line ${positive ? 'is-up' : 'is-down'}`} />
          <circle cx={path.last.x} cy={path.last.y} r="2.5" className={`gt-indices-board__dot ${positive ? 'is-up' : 'is-down'}`} />
        </svg>
      </td>
    </tr>
  )
}

function buildIndexMiniPath(symbol, start, end, width = 84, height = 26) {
  const seed = [...String(symbol || '')].reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const pointCount = 16
  const range = Math.max(Math.abs(end - start) * 1.8, Math.abs(start) * 0.006, 1)
  const values = Array.from({ length: pointCount }, (_, index) => {
    const progress = index / (pointCount - 1)
    if (index === 0) return start
    if (index === pointCount - 1) return end
    return start + (end - start) * progress + Math.sin(seed * 0.15 + index * 1.3) * range * 0.22 * (1 - progress * 0.3)
  })
  const min = Math.min(...values)
  const max = Math.max(...values)
  const valueRange = max - min || 1
  const point = (value, index) => ({ x: (index / (pointCount - 1)) * width, y: height - ((value - min) / valueRange) * (height - 4) - 2 })
  const coords = values.map(point)
  const path = coords.map((pointValue, index) => `${index ? 'L' : 'M'} ${pointValue.x.toFixed(1)} ${pointValue.y.toFixed(1)}`).join(' ')
  const first = coords[0]
  const last = coords.at(-1)
  return { path, area: `${path} L ${last.x.toFixed(1)} ${height} L ${first.x.toFixed(1)} ${height} Z`, last, refY: first.y }
}

/* ====================== Filter Chips Bar ====================== */
function FilterChipsBar({ sort, onSortChange, exchange, onExchangeChange, search, onSearchChange, total, showing, loading, freshness, asOf, pageSize, onPageSizeChange, detailedMode, onDetailedModeChange }) {
  const sortOptions = [
    { value: 'market_cap_desc', label: 'Vốn hóa' },
    { value: 'change_desc', label: 'Tăng giá' },
    { value: 'change_asc', label: 'Giảm giá' },
    { value: 'volume_desc', label: 'Thanh khoản' },
    { value: 'value_desc', label: 'Giá trị' },
    { value: 'foreign_net_buy_desc', label: 'NN mua ròng' },
    { value: 'symbol_asc', label: 'A→Z' },
  ]
  const exchangeOptions = [
    { value: '', label: 'Tất cả sàn' },
    { value: 'HOSE', label: 'HSX' },
    { value: 'HNX', label: 'HNX' },
    { value: 'UPCOM', label: 'UPCOM' },
  ]
  return (
    <div className="gt-filter-bar">
      <div className="gt-filter-bar__row">
        <input
          className="gt-filter-bar__search"
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value.toUpperCase())}
          placeholder="Tìm mã (FPT, VIC…)"
          aria-label="Tìm ticker"
        />
        <div className="gt-filter-bar__chips">
          <span className="gt-filter-bar__label">Sắp xếp</span>
          {sortOptions.map((opt) => (
            <button
              type="button"
              key={opt.value}
              className={`gt-chip ${sort === opt.value ? 'is-active' : ''}`}
              aria-pressed={sort === opt.value}
              onClick={() => onSortChange(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="gt-filter-bar__chips gt-filter-bar__page-size" aria-label="Số dòng">
          <span className="gt-filter-bar__label">Hiển thị</span>
          {[20, 50, 100].map((size) => (
            <button
              type="button"
              key={size}
              className={`gt-chip gt-chip--compact ${pageSize === size ? 'is-active' : ''}`}
              aria-pressed={pageSize === size}
              onClick={() => onPageSizeChange(size)}
            >
              {size}
            </button>
          ))}
        </div>
      </div>
      <div className="gt-filter-bar__row">
        <div className="gt-filter-bar__chips">
          <span className="gt-filter-bar__label">Sàn</span>
          {exchangeOptions.map((opt) => (
            <button
              type="button"
              key={opt.value || 'all'}
              className={`gt-chip ${exchange === opt.value ? 'is-active' : ''}`}
              aria-pressed={exchange === opt.value}
              onClick={() => onExchangeChange(opt.value)}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="gt-filter-bar__toggle-container">
          <button
            type="button"
            className={`gt-chip ${detailedMode ? 'is-active' : ''}`}
            onClick={() => onDetailedModeChange(!detailedMode)}
            title="Chuyển đổi bảng giá chi tiết"
          >
            📊 {detailedMode ? 'Bảng rút gọn' : 'Bảng chi tiết'}
          </button>
        </div>
        <div className="gt-filter-bar__status">
          <span className={`gt-trust__topic-dot ${freshness || 'stale'}`} />
          <span>{loading ? 'Đang tải…' : freshness === 'fresh' ? 'Live' : 'Cache'}</span>
          <span className="gt-filter-bar__count">{showing}{total ? `/${total}` : ''} mã</span>
          <span>{formatTimestamp(asOf)}</span>
        </div>
      </div>
    </div>
  )
}

function TerminalLoadingState() {
  return (
    <section className="global-terminal global-terminal--loading" aria-busy="true" aria-label="Đang tải Market & Portfolio">
      <div className="gt-loading__header">
        <div className="gt-skel gt-skel--title" />
        <div className="gt-skel gt-skel--search" />
        <div className="gt-skel gt-skel--status" />
      </div>
      <div className="gt-loading__tabs">
        {DEFAULT_TABS.map((tab) => <div className="gt-skel gt-skel--tab" key={tab.id} />)}
      </div>
      <div className="gt-loading__workspace">
        <div className="gt-skel gt-skel--panel" />
        <div className="gt-loading__main">
          <div className="gt-skel gt-skel--hero" />
          <div className="gt-skel gt-skel--chart" />
        </div>
        <div className="gt-skel gt-skel--panel" />
      </div>
      <span className="sr-only">Đang đồng bộ snapshot và dữ liệu biểu đồ.</span>
    </section>
  )
}

/* ====================== Ticker tape ====================== */
function TickerTape({ items, selectedSymbol, onSelect }) {
  if (!items?.length) return null
  return (
    <div className="gt-ticker" aria-label="Market ticker tape">
      <div className="gt-ticker__track">
        {items.map((item) => {
          const positive = Number(item.change_pct) >= 0
          return (
            <button
              type="button"
              key={item.symbol}
              className={`gt-ticker__item ${item.symbol === selectedSymbol ? 'is-selected' : ''}`}
              aria-pressed={item.symbol === selectedSymbol}
              onClick={() => onSelect(item.symbol)}
            >
              <strong>{item.symbol}</strong>
              <span className="gt-ticker__item-price">{formatPrice(item.price)}</span>
              <em className={`gt-ticker__item-change ${positive ? 'is-pos' : 'is-neg'}`}>
                {formatChange(item.change_pct)}
              </em>
            </button>
          )
        })}
      </div>
    </div>
  )
}

/* ====================== Watchlist ====================== */
function Watchlist({ title, items, selectedSymbol, onSelect, vnControls }) {
  return (
    <section className="gt-card">
      <div className="gt-card__head">
        <h2 className="gt-card__title">{title}</h2>
        <span className="gt-card__action" aria-hidden="true">
          {vnControls ? `${items.length}/${vnControls.total ?? '—'}` : items.length}
        </span>
      </div>
      {vnControls ? <VnWatchlistControls {...vnControls} /> : null}
      <div className="gt-watchlist__scroll">
        {items.length ? (
          items.map((item) => {
            const positive = Number(item.change_pct) >= 0
            return (
              <button
                type="button"
                key={item.symbol}
                className={`gt-watchlist__row ${item.symbol === selectedSymbol ? 'is-selected' : ''}`}
                aria-pressed={item.symbol === selectedSymbol}
                onClick={() => onSelect(item.symbol)}
              >
                <div className="gt-watchlist__sym">
                  <strong>{item.symbol}</strong>
                  <small>{item.name || item.focus || '—'}</small>
                </div>
                <div className="gt-watchlist__chg num">{formatPrice(item.price)}</div>
                <div className={`gt-watchlist__chg ${positive ? 'is-pos' : 'is-neg'}`}>
                  {formatChange(item.change_pct)}
                </div>
              </button>
            )
          })
        ) : (
          <p className="gt-watchlist__empty">
            {vnControls?.loading
              ? 'Đang tải VN snapshot…'
              : vnControls?.error
                ? `Snapshot lỗi: ${vnControls.error}`
                : 'Live feed chưa có dữ liệu cho tab này.'}
          </p>
        )}
      </div>
      {vnControls?.asOf ? (
        <div className="gt-watchlist__foot">
          <span className={`gt-trust__topic-dot ${vnControls.freshness || 'stale'}`} />
          <span>{vnControls.freshness === 'fresh' ? 'Live' : 'Cache'} · {formatTimestamp(vnControls.asOf)}</span>
        </div>
      ) : null}
    </section>
  )
}

function VnWatchlistControls({ sort, onSortChange, exchange, onExchangeChange, search, onSearchChange }) {
  return (
    <div className="gt-vn-controls">
      <input
        className="gt-vn-controls__search"
        type="search"
        value={search}
        onChange={(event) => onSearchChange(event.target.value.toUpperCase())}
        placeholder="Tìm mã (FPT, VIC, …)"
        aria-label="Tìm ticker VN"
      />
      <div className="gt-vn-controls__chips">
        {['', 'HOSE', 'HNX', 'UPCOM'].map((ex) => (
          <button
            type="button"
            key={ex || 'all'}
            className={`gt-vn-controls__chip ${exchange === ex ? 'is-active' : ''}`}
            aria-pressed={exchange === ex}
            onClick={() => onExchangeChange(ex)}
          >
            {ex || 'Tất cả'}
          </button>
        ))}
      </div>
      <select
        className="gt-vn-controls__sort"
        value={sort}
        onChange={(event) => onSortChange(event.target.value)}
        aria-label="Sắp xếp"
      >
        <option value="market_cap_desc">Vốn hóa lớn nhất</option>
        <option value="change_desc">Tăng nhiều nhất</option>
        <option value="change_asc">Giảm nhiều nhất</option>
        <option value="volume_desc">Volume cao nhất</option>
        <option value="value_desc">Value cao nhất</option>
        <option value="symbol_asc">Theo tên A→Z</option>
      </select>
    </div>
  )
}

/* ====================== VN Price Board ====================== */
function VnPriceBoard({
  items, selectedSymbol, onSelect,
  sort, onSortChange, exchange, onExchangeChange, search, onSearchChange,
  total, loading, error, freshness, asOf,
}) {
  return (
    <section className="gt-priceboard">
      <div className="gt-priceboard__legend">
        <span className="gt-px-ce">■ Trần</span>
        <span className="gt-px-up">■ Tăng</span>
        <span className="gt-px-tc">■ Tham chiếu</span>
        <span className="gt-px-dn">■ Giảm</span>
        <span className="gt-px-fl">■ Sàn</span>
      </div>

      {error ? (
        <div className="gt-priceboard__empty">Snapshot lỗi: {error}</div>
      ) : items.length === 0 ? (
        <div className="gt-priceboard__empty">
          {loading ? 'Đang tải bảng giá…' : 'Không có mã phù hợp filter hiện tại.'}
        </div>
      ) : (
        <div className="gt-priceboard__scroll">
          <table className="gt-priceboard__table">
            <thead>
              <tr>
                <th className="gt-priceboard__sym-head" rowSpan={2}>CK</th>
                <th rowSpan={2}>TC</th>
                <th rowSpan={2}>Trần</th>
                <th rowSpan={2}>Sàn</th>
                <th colSpan={3} className="gt-priceboard__group">Bên mua</th>
                <th colSpan={3} className="gt-priceboard__group gt-priceboard__group--match">Khớp lệnh</th>
                <th colSpan={3} className="gt-priceboard__group">Bên bán</th>
                <th rowSpan={2}>Tổng KL</th>
                <th rowSpan={2}>Mở</th>
                <th rowSpan={2}>Cao</th>
                <th rowSpan={2}>Thấp</th>
                <th rowSpan={2}>NN Mua</th>
                <th rowSpan={2}>NN Bán</th>
              </tr>
              <tr>
                <th>Giá 3</th><th>Giá 2</th><th>Giá 1</th>
                <th>Giá</th><th>KL</th><th>+/-</th>
                <th>Giá 1</th><th>Giá 2</th><th>Giá 3</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <VnPriceBoardRow
                  key={row.symbol}
                  row={row}
                  selected={row.symbol === selectedSymbol}
                  onSelect={onSelect}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function VnPriceBoardRow({ row, selected, onSelect }) {
  const matchCls = priceClass(row.price, row)
  const changeCls = row.change_pct == null
    ? '' : row.change_pct > 0 ? 'gt-px-up' : row.change_pct < 0 ? 'gt-px-dn' : 'gt-px-tc'
  return (
    <tr
      className={`gt-priceboard__row ${selected ? 'is-selected' : ''}`}
      onClick={() => onSelect(row.symbol)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          onSelect(row.symbol)
        }
      }}
      tabIndex={0}
      aria-selected={selected}
      aria-label={`${row.symbol} ${row.name || ''}, giá ${formatVnPrice(row.price)}, ${formatChange(row.change_pct)}`}
    >
      <td className="gt-priceboard__sym">
        <strong>{row.symbol}</strong>
        <small>{row.exchange || ''}</small>
      </td>
      <td className="gt-px-tc">{formatVnPrice(row.ref_price)}</td>
      <td className="gt-px-ce">{formatVnPrice(row.ceiling)}</td>
      <td className="gt-px-fl">{formatVnPrice(row.floor)}</td>
      <BidAskCell price={row.bid_3_price} vol={row.bid_3_volume} cls={priceClass(row.bid_3_price, row)} />
      <BidAskCell price={row.bid_2_price} vol={row.bid_2_volume} cls={priceClass(row.bid_2_price, row)} />
      <BidAskCell price={row.bid_1_price} vol={row.bid_1_volume} cls={priceClass(row.bid_1_price, row)} />
      <td className={matchCls}><strong>{formatVnPrice(row.price)}</strong></td>
      <td className="gt-priceboard__match-vol">{formatVnVolume(row.match_vol)}</td>
      <td className={changeCls}>{row.change_pct == null ? '—' : `${row.change_pct > 0 ? '+' : ''}${row.change_pct.toFixed(2)}%`}</td>
      <BidAskCell price={row.ask_1_price} vol={row.ask_1_volume} cls={priceClass(row.ask_1_price, row)} />
      <BidAskCell price={row.ask_2_price} vol={row.ask_2_volume} cls={priceClass(row.ask_2_price, row)} />
      <BidAskCell price={row.ask_3_price} vol={row.ask_3_volume} cls={priceClass(row.ask_3_price, row)} />
      <td className="gt-priceboard__vol">{formatVnVolume(row.volume)}</td>
      <td className={priceClass(row.open, row)}>{formatVnPrice(row.open)}</td>
      <td className={priceClass(row.high, row)}>{formatVnPrice(row.high)}</td>
      <td className={priceClass(row.low, row)}>{formatVnPrice(row.low)}</td>
      <td className="gt-px-up">{formatVnVolume(row.foreign_buy_volume)}</td>
      <td className="gt-px-dn">{formatVnVolume(row.foreign_sell_volume)}</td>
    </tr>
  )
}

function BidAskCell({ price, vol, cls }) {
  if (price == null) return <td className="gt-priceboard__ba">—</td>
  return (
    <td className={`gt-priceboard__ba ${cls}`}>
      <span className="gt-priceboard__ba-price">{formatVnPrice(price)}</span>
      <span className="gt-priceboard__ba-vol">{formatVnVolume(vol)}</span>
    </td>
  )
}

function priceClass(price, row) {
  if (price == null || row?.ref_price == null) return ''
  if (row.ceiling != null && price >= row.ceiling) return 'gt-px-ce'
  if (row.floor != null && price <= row.floor) return 'gt-px-fl'
  if (price > row.ref_price) return 'gt-px-up'
  if (price < row.ref_price) return 'gt-px-dn'
  return 'gt-px-tc'
}

function formatVnPrice(value) {
  if (value == null) return '—'
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return '—'
  // VN price convention: stocks denominated in VND, display ÷ 1000 (X.XX format)
  const k = n / 1000
  return k.toLocaleString('vi-VN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatVnVolume(value) {
  if (value == null) return '—'
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return '—'
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`
  return n.toLocaleString('vi-VN', { maximumFractionDigits: 0 })
}


function InstrumentHero({ quote, history, symbol }) {
  const ohlc = useMemo(() => computeOHLC(history), [history])
  if (!quote && !history) {
    return (
      <section className="gt-card">
        <HeroSkeleton />
      </section>
    )
  }
  // Today's change (from realtime snapshot) — primary
  // Period change (from chart range) — secondary, labeled
  const todayPct = quote?.change_pct
  const todayAbs = quote?.change
  const periodPct = ohlc.changePct
  const hasToday = todayPct !== null && todayPct !== undefined
  const showPct = hasToday ? Number(todayPct) : Number(periodPct ?? 0)
  const showAbs = hasToday ? Number(todayAbs ?? 0) : Number(ohlc.changeAbs ?? 0)
  const positive = showPct >= 0
  const price = quote?.price ?? ohlc.last ?? 0
  const periodLabel = (history?.period || '').toUpperCase()
  return (
    <section className="gt-card">
      <div className="gt-card__head">
        <h2 className="gt-card__title">Quote · {hasToday ? 'Today' : periodLabel || 'Live'}</h2>
        <span className="gt-card__action" aria-hidden="true">{quote?.source || history?.source || '—'}</span>
      </div>
      <div className="gt-hero">
        <div className="gt-hero__top">
          <div className="gt-hero__symbol">
            <div className="gt-hero__sym-row">
              <strong>{symbol}</strong>
              <span>{quote?.name || history?.name || ''}</span>
            </div>
            <span className="gt-hero__focus">{quote?.focus || history?.focus || 'Real-time market quote'}</span>
          </div>
          <div className="gt-hero__price">
            <span className="gt-hero__price-main">{formatPrice(price)}</span>
            <span className={`gt-hero__chg-pill ${positive ? 'is-pos' : 'is-neg'}`}>
              <span>{formatChange(showPct)}</span>
              {showAbs ? <span className="gt-hero__chg-pill-abs">{formatSigned(showAbs)}</span> : null}
            </span>
            {hasToday && periodLabel && periodPct != null && Math.abs(periodPct) > 0.5 ? (
              <span className={`gt-hero__period-chg ${periodPct >= 0 ? 'is-pos' : 'is-neg'}`}>
                {periodLabel} {formatChange(periodPct)}
              </span>
            ) : null}
          </div>
        </div>
        {ohlc.hasData ? (
          <dl className="gt-hero__ohlc">
            <div>
              <dt>Open</dt>
              <dd>{formatPrice(ohlc.open)}</dd>
            </div>
            <div>
              <dt>High</dt>
              <dd>{formatPrice(ohlc.high)}</dd>
            </div>
            <div>
              <dt>Low</dt>
              <dd>{formatPrice(ohlc.low)}</dd>
            </div>
            <div>
              <dt>Last</dt>
              <dd>{formatPrice(ohlc.last)}</dd>
            </div>
          </dl>
        ) : null}
      </div>
    </section>
  )
}

function HeroSkeleton() {
  return (
    <div className="gt-card__skel">
      <div className="gt-skel gt-skel--title" />
      <div className="gt-skel gt-skel--price" />
      <div className="gt-skel gt-skel--bar" />
    </div>
  )
}

/* ====================== Chart ====================== */
function InstrumentChart({ history, loading, error, presetId, onPresetChange, onRetry }) {
  const isYtd = Boolean(history?.ytd)
  const points = useMemo(() => {
    const rawPoints = history?.points || []
    if (!isYtd) return rawPoints
    const yearStart = new Date(new Date().getFullYear(), 0, 1).getTime()
    return rawPoints.filter((p) => new Date(p.date).getTime() >= yearStart)
  }, [history?.points, isYtd])

  const [chartMode, setChartMode] = useState('area')
  const hasOhlc = points.length > 0 && points[0]?.open != null && points[0]?.high != null
  const effectiveMode = hasOhlc ? chartMode : 'area'

  const freshness = history?.freshness
  const staleReason = history?.stale_reason
  return (
    <section className="gt-card">
      <div className="gt-card__head">
        <h2 className="gt-card__title">Price chart</h2>
        <div className="gt-chart__head-right">
          <ChartModeToggle mode={effectiveMode} onChange={setChartMode} disabled={!hasOhlc} />
          {freshness ? <FreshnessPill freshness={freshness} /> : null}
        </div>
      </div>
      <div className="gt-chart">
        <div className="gt-chart__controls">
          {CHART_PRESETS.map((preset) => (
            <button
              type="button"
              key={preset.id}
              className={`gt-chart__btn ${preset.id === presetId ? 'is-active' : ''}`}
              aria-pressed={preset.id === presetId}
              onClick={() => onPresetChange(preset.id)}
              title={`${preset.period} · ${preset.interval}`}
            >
              {preset.label}
            </button>
          ))}
        </div>
        {loading ? (
          <div className="gt-chart__state" aria-live="polite">
            <div className="gt-chart__loading">
              <span className="gt-skel gt-skel--bar" />
              <span>Đang tải history theo mã và timeframe…</span>
            </div>
          </div>
        ) : error ? (
          <div className="gt-chart__state is-error" role="alert">
            <p>{error}</p>
            <button type="button" className="gt-error__retry" onClick={onRetry}>Thử lại</button>
          </div>
        ) : points.length ? (
          <>
            <LightweightChartPanel
              points={points}
              mode={effectiveMode}
              height={340}
              ariaLabel={`Biểu đồ giá ${history?.symbol || ''}, ${describeInterval(presetId, history?.source)}, ${points.length} điểm dữ liệu`}
            />
            <div className="gt-chart__hint">
              Cuộn để zoom · kéo để pan · double-click trục để reset
            </div>
          </>
        ) : (
          <ChartEmpty staleReason={staleReason} presetId={presetId} onRetry={onRetry} onFallback={onPresetChange} />
        )}
        <div className="gt-chart__foot">
          <span>{points[0] ? formatShortDate(points[0].date) : '—'}</span>
          <span>{describeInterval(presetId, history?.source)}</span>
          <span>{points[points.length - 1] ? formatShortDate(points[points.length - 1].date) : '—'}</span>
        </div>
      </div>
    </section>
  )
}

function ChartModeToggle({ mode, onChange, disabled }) {
  return (
    <div className={`gt-chart__mode-toggle ${disabled ? 'is-disabled' : ''}`} role="group" aria-label="Chart mode">
      <button
        type="button"
        className={`gt-chart__mode-btn ${mode === 'area' ? 'is-active' : ''}`}
        aria-pressed={mode === 'area'}
        onClick={() => onChange('area')}
        title="Line/area chart"
      >
        Line
      </button>
      <button
        type="button"
        className={`gt-chart__mode-btn ${mode === 'candle' ? 'is-active' : ''}`}
        aria-pressed={mode === 'candle'}
        onClick={() => onChange('candle')}
        disabled={disabled}
        title={disabled ? 'OHLC not available for this period' : 'Candlestick chart'}
      >
        Candle
      </button>
    </div>
  )
}

function FreshnessPill({ freshness }) {
  const map = {
    fresh: { label: 'Live', dot: 'fresh' },
    stale: { label: 'Stale cache', dot: 'degraded' },
    degraded: { label: 'No data', dot: 'stale' },
  }
  const meta = map[freshness] || map.degraded
  return (
    <span className="gt-chart__freshness" title={`Feed freshness: ${freshness}`}>
      <span className={`gt-trust__topic-dot ${meta.dot}`} />
      {meta.label}
    </span>
  )
}

function ChartEmpty({ staleReason, presetId, onRetry, onFallback }) {
  const reason = explainStaleReason(staleReason)
  const fallbackId = presetId === '6M' ? null : '6M'
  return (
    <div className="gt-chart__state gt-chart__state--empty">
      <p><strong>{reason.title}</strong></p>
      <p>{reason.detail}</p>
      <div className="gt-chart__state-actions">
        <button type="button" className="gt-error__retry" onClick={onRetry}>Thử lại</button>
        {fallbackId ? (
          <button type="button" className="gt-error__retry" onClick={() => onFallback(fallbackId)}>
            Xem khung {fallbackId}
          </button>
        ) : null}
      </div>
    </div>
  )
}

function explainStaleReason(reason) {
  if (reason === 'unknown_symbol') {
    return {
      title: 'Symbol chưa có trong DataHub',
      detail: 'Mã này chưa được map sang nguồn dữ liệu lịch sử. Hãy thử một symbol khác từ watchlist.',
    }
  }
  if (reason === 'history_live_feed_unavailable_no_cache') {
    return {
      title: 'Yahoo Finance không phản hồi',
      detail: 'Khung thời gian này chưa có cache trong DataHub và live feed đang lỗi. Thử lại sau hoặc chuyển khung 6M (combo an toàn nhất).',
    }
  }
  if (reason === 'history_live_feed_unavailable_using_cache') {
    return {
      title: 'Đang dùng cache cũ',
      detail: 'Live feed Yahoo đang lỗi. Số liệu hiển thị có thể chậm 15 phút – vài giờ.',
    }
  }
  return {
    title: 'Chưa có history',
    detail: 'Khung thời gian này chưa có dữ liệu cho symbol đang chọn.',
  }
}

function describeInterval(presetId, source) {
  const preset = CHART_PRESETS.find((item) => item.id === presetId)
  const src = source || 'vnstock'
  if (!preset) return src
  return `${preset.period} · ${preset.interval} · ${src}`
}

/* ====================== Instrument news ====================== */
function InstrumentNews({ items, onOpenNews }) {
  return (
    <section className="gt-card">
      <div className="gt-card__head">
        <h2 className="gt-card__title">Market news</h2>
        <button type="button" className="gt-card__action" onClick={onOpenNews}>Open News Desk →</button>
      </div>
      {items.length ? (
        items.slice(0, 6).map((item) => (
          <article key={item.article_id || `${item.time}-${item.headline}`} className="gt-news__row">
            <time className="gt-news__time">{item.time || formatNewsTime(item.published_at)}</time>
            <div className="gt-news__body">
              <p>{item.headline}</p>
              <div className="gt-news__chips">
                {item.category ? <span className="gt-news__chip">{item.category}</span> : null}
                {item.sentiment ? <span className={`gt-news__chip sentiment-${item.sentiment}`}>{item.sentiment}</span> : null}
                {item.impact ? <span className="gt-news__chip">{item.impact} impact</span> : null}
              </div>
            </div>
            <span className="gt-news__source">{item.source}</span>
          </article>
        ))
      ) : (
        <p className="gt-news__empty">News feed chưa có dữ liệu. Hệ thống dùng cache khi RSS producer chạy thành công.</p>
      )}
    </section>
  )
}

/* ====================== Market pulse ====================== */
function MarketPulseCard({ pulse }) {
  const score = Math.max(0, Math.min(100, Number(pulse.fear_greed || 0)))
  return (
    <section className="gt-card">
      <div className="gt-card__head">
        <h2 className="gt-card__title">Market pulse</h2>
        <span className="gt-card__action" aria-hidden="true">{pulse.label || ''}</span>
      </div>
      <div className="gt-pulse">
        <FearGreedGauge score={score} />
        <hr className="gt-pulse__divider" />
        <div className="gt-pulse__breadth">
          {(pulse.breadth || []).map((row) => {
            const total = Math.max(1, Number(row.up || 0) + Number(row.down || 0))
            const pct = (Number(row.up || 0) / total) * 100
            return (
              <div key={row.label} className="gt-pulse__breadth-row">
                <span>{row.label}</span>
                <div className="gt-pulse__breadth-bar">
                  <i style={{ width: `${pct.toFixed(1)}%` }} />
                </div>
                <b><span className="is-pos">{row.up}</span> / <span className="is-neg">{row.down}</span></b>
              </div>
            )
          })}
        </div>
        {((pulse.top_gainers || []).length || (pulse.top_losers || []).length) ? (
          <>
            <hr className="gt-pulse__divider" />
            <div className="gt-pulse__movers">
              <MoversCol title="Top gainers" items={pulse.top_gainers || []} positive />
              <MoversCol title="Top losers" items={pulse.top_losers || []} />
            </div>
          </>
        ) : null}
      </div>
    </section>
  )
}

function MoversCol({ title, items, positive = false }) {
  return (
    <div className="gt-pulse__movers-col">
      <h4>{title}</h4>
      {items.slice(0, 4).map((item) => (
        <div key={`${title}-${item.symbol}`} className="gt-pulse__movers-row">
          <span>{item.symbol}</span>
          <b className={positive ? 'is-pos' : 'is-neg'}>{formatChange(item.change_pct)}</b>
        </div>
      ))}
      {!items.length ? <div className="gt-pulse__movers-row"><span style={{ color: 'var(--ink-subtle)', fontSize: 11 }}>—</span></div> : null}
    </div>
  )
}

function FearGreedGauge({ score }) {
  const W = 180
  const H = 100
  const cx = W / 2
  const cy = H - 8
  const R = 76
  const startA = Math.PI
  const endA = 0
  const valueA = startA - (score / 100) * Math.PI
  const arcStart = polar(cx, cy, R, startA)
  const arcEnd = polar(cx, cy, R, endA)
  const trackPath = `M ${arcStart.x} ${arcStart.y} A ${R} ${R} 0 0 1 ${arcEnd.x} ${arcEnd.y}`
  const needle = polar(cx, cy, R - 4, valueA)
  const fillColor = score < 33 ? 'var(--neg)' : score < 66 ? 'var(--warn)' : 'var(--pos)'
  const label = score < 25 ? 'Extreme fear'
    : score < 45 ? 'Fear'
    : score < 55 ? 'Neutral'
    : score < 75 ? 'Greed'
    : 'Extreme greed'
  return (
    <div className="gt-pulse__gauge">
      <svg viewBox={`0 0 ${W} ${H}`}>
        <path d={trackPath} className="gt-pulse__gauge-track" />
        <path
          d={`M ${arcStart.x} ${arcStart.y} A ${R} ${R} 0 0 1 ${needle.x} ${needle.y}`}
          fill="none"
          stroke={fillColor}
          strokeWidth="10"
          strokeLinecap="round"
        />
        <line x1={cx} y1={cy} x2={needle.x} y2={needle.y} className="gt-pulse__gauge-needle" />
        <circle cx={cx} cy={cy} r="4" fill="var(--ink)" />
      </svg>
      <div className="gt-pulse__gauge-value">{score}<small>/100</small></div>
      <div className="gt-pulse__gauge-label">{label}</div>
    </div>
  )
}

/* ====================== Trust + Feed ====================== */
function TrustFeedCard({ trust, topics }) {
  const [open, setOpen] = useState(false)
  return (
    <section className={`gt-card gt-trust ${open ? 'is-open' : ''}`}>
      <button
        type="button"
        className="gt-trust__toggle"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span>Trust layer · {topics.length} feeds</span>
        <span className="gt-trust__chevron">›</span>
      </button>
      {open ? (
        <div className="gt-trust__body">
          {trust?.what_this_is ? (
            <div className="gt-trust__section">
              <h4>What this is</h4>
              <p>{trust.what_this_is}</p>
            </div>
          ) : null}
          {trust?.what_this_is_not ? (
            <div className="gt-trust__section">
              <h4>What this is not</h4>
              <p>{trust.what_this_is_not}</p>
            </div>
          ) : null}
          <div className="gt-trust__section">
            <h4>DataHub feeds</h4>
            <div className="gt-trust__topics">
              {topics.slice(0, 6).map((topic) => (
                <div key={topic.topic} className="gt-trust__topic">
                  <span><span className={`gt-trust__topic-dot ${topic.freshness || 'stale'}`} />{topic.topic}</span>
                  <b>{topic.freshness}</b>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}

/* ====================== Status bar ====================== */
function StatusBar({ topics, timestamp, source }) {
  const fresh = topics.filter((topic) => topic.freshness === 'fresh').length
  const degraded = topics.filter((topic) => topic.freshness === 'degraded').length
  const stale = topics.filter((topic) => topic.freshness === 'stale').length
  const overall = stale ? 'stale' : degraded ? 'degraded' : 'fresh'
  return (
    <footer className="gt-status-bar">
      <span className="gt-status-bar__seg">
        <span className={`gt-trust__topic-dot ${overall}`} />
        <b>FEEDS</b> {fresh} fresh · {degraded} degraded · {stale} stale
      </span>
      <span className="gt-status-bar__seg"><b>SOURCE</b> {source || 'datahub'}</span>
      <span className="gt-status-bar__seg"><b>MODE</b> education-first</span>
      <span className="gt-status-bar__spacer" />
      <span className="gt-status-bar__seg">{formatTimestamp(timestamp)}</span>
    </footer>
  )
}

/* ====================== Helpers ====================== */
function buildWatchlist(widgets, activeView) {
  const category = TAB_CATEGORY[activeView] || 'dashboard'
  if (category === 'indices') return sortByPriority([...(widgets.global_indices || []), ...(widgets.global_snapshot || [])])
  return sortByPriority([
    ...(widgets.global_indices || []),
    ...(widgets.global_snapshot || []),
  ])
}

function watchlistTitle(activeView) {
  const category = TAB_CATEGORY[activeView] || 'dashboard'
  if (category === 'indices') return 'Indices'
  return 'Watchlist'
}

function sortByPriority(items) {
  const seen = new Set()
  const deduped = items.filter((item) => {
    if (!item?.symbol || seen.has(item.symbol)) return false
    seen.add(item.symbol)
    return true
  })
  return [...deduped].sort((a, b) => {
    const left = PRIORITY.indexOf(a.symbol)
    const right = PRIORITY.indexOf(b.symbol)
    if (left === -1 && right === -1) return 0
    if (left === -1) return 1
    if (right === -1) return -1
    return left - right
  })
}

function findQuote(widgets, symbol) {
  return [
    ...(widgets.global_indices || []),
    ...(widgets.global_snapshot || []),
  ].find((item) => item.symbol === symbol)
}

function computeOHLC(history) {
  const points = history?.points || []
  if (!points.length) return { hasData: false }
  const first = points[0]
  const last = points[points.length - 1]
  const open = Number(first.open ?? first.price ?? 0)
  const close = Number(last.close ?? last.price ?? 0)
  let high = -Infinity
  let low = Infinity
  for (const point of points) {
    const h = Number(point.high ?? point.price ?? 0)
    const l = Number(point.low ?? point.price ?? 0)
    if (h > high) high = h
    if (l < low) low = l
  }
  const changeAbs = close - open
  const changePct = open ? (changeAbs / open) * 100 : 0
  return { hasData: true, open, high, low, last: close, changeAbs, changePct }
}

function polar(cx, cy, r, angle) {
  return { x: cx + r * Math.cos(angle), y: cy - r * Math.sin(angle) }
}

function formatPrice(value) {
  if (value === null || value === undefined || value === '') return '—'
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  if (Math.abs(number) >= 1000) return number.toLocaleString('en-US', { maximumFractionDigits: 2 })
  return number.toLocaleString('en-US', { maximumFractionDigits: 4 })
}

function formatSigned(value) {
  if (value === null || value === undefined) return ''
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  return `${number >= 0 ? '+' : ''}${formatPrice(number)}`
}

function formatChange(value) {
  if (value === null || value === undefined) return '—'
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return `${number >= 0 ? '+' : ''}${number.toFixed(2)}%`
}

function formatTimestamp(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatNewsTime(value) {
  if (!value) return '--:--'
  return new Date(value).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

function formatShortDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

/* ====================== Ticker Metadata Seed ====================== */
function getStockMetadata(symbol, price, row = {}) {
  return {
    name: row.name || `Công ty cổ phần ${symbol}`,
    cap: Number.isFinite(Number(row.market_cap)) ? Number(row.market_cap) : null,
    netBuy: Number.isFinite(Number(row.foreign_net_buy)) ? Number(row.foreign_net_buy) : null,
  }
}

/* ====================== Simple Overview Table ====================== */
function VnOverviewTable({ items, selectedSymbol, onSelect, total, loading, error }) {
  return (
    <section className="gt-priceboard">
      <div className="gt-priceboard__legend">
        <span className="gt-px-ce">■ Trần</span>
        <span className="gt-px-up">■ Tăng</span>
        <span className="gt-px-tc">■ Tham chiếu</span>
        <span className="gt-px-dn">■ Giảm</span>
        <span className="gt-px-fl">■ Sàn</span>
      </div>

      {error ? (
        <div className="gt-priceboard__empty">Snapshot lỗi: {error}</div>
      ) : items.length === 0 ? (
        <div className="gt-priceboard__empty">
          {loading ? 'Đang tải bảng giá…' : 'Không có mã phù hợp filter hiện tại.'}
        </div>
      ) : (
        <div className="gt-priceboard__scroll">
          <table className="gt-priceboard__table gt-priceboard__table--simple">
            <thead>
              <tr>
                <th style={{ width: '40px', textAlign: 'center' }}>#</th>
                <th className="gt-priceboard__sym-head" style={{ textAlign: 'left' }}>Mã CK</th>
                <th>Giá</th>
                <th>+/-</th>
                <th>%</th>
                <th>Vốn hóa (tỷ)</th>
                <th>GT (tỷ)</th>
                <th>Tổng KL</th>
                <th>GT NN Mua ròng (triệu)</th>
                <th style={{ width: '90px', textAlign: 'center' }}>Biểu đồ</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row, idx) => (
                <VnOverviewRow
                  key={row.symbol}
                  idx={idx + 1}
                  row={row}
                  selected={row.symbol === selectedSymbol}
                  onSelect={onSelect}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function VnOverviewRow({ idx, row, selected, onSelect }) {
  const meta = getStockMetadata(row.symbol, row.price, row)
  const positive = Number(row.change_pct ?? row.changePct ?? 0) >= 0
  const cls = priceClass(row.price, row)
  const valBillion = ((Number(row.price || 0) * Number(row.volume || 0)) / 1e9).toLocaleString('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  const miniChart = buildStockMiniChart(row)
  
  return (
    <tr
      className={`gt-priceboard__row ${selected ? 'is-selected' : ''}`}
      onClick={() => onSelect(row.symbol)}
    >
      <td style={{ textAlign: 'center', color: 'var(--ink-subtle)' }}>{idx}</td>
      <td className="gt-priceboard__sym">
        <div className="gt-overview-sym-col">
          <div className="gt-overview-sym-row">
            <strong className={cls}>{row.symbol}</strong>
            <span className="gt-overview-exchange">{row.exchange || 'HSX'}</span>
          </div>
          <small className="gt-overview-name">{meta.name}</small>
        </div>
      </td>
      <td className={`num ${cls}`} style={{ fontWeight: '700', fontSize: '13px' }}>
        {formatPrice(row.price)}
      </td>
      <td className={`num ${cls}`}>
        {formatSigned(row.change)}
      </td>
      <td className={`num ${cls}`} style={{ fontWeight: '600' }}>
        {formatChange(row.change_pct ?? row.changePct)}
      </td>
      <td className="num">{formatPrice(meta.cap)}</td>
      <td className="num">{valBillion}</td>
      <td className="num">{Number(row.volume || 0).toLocaleString('en-US')}</td>
      <td className={`num ${meta.netBuy == null ? '' : meta.netBuy >= 0 ? 'is-pos' : 'is-neg'}`}>
        {meta.netBuy == null ? '—' : Number(meta.netBuy).toLocaleString('vi-VN', { minimumFractionDigits: 2 })}
      </td>
      <td style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '38px', textAlign: 'center' }}>
        <svg className="gt-mini-chart" width="60" height="24" viewBox="0 0 60 24" aria-label={`Biểu đồ mini ${row.symbol}`} role="img">
          {miniChart.refY != null ? (
            <line x1="0" x2="60" y1={miniChart.refY} y2={miniChart.refY} className="gt-mini-chart__ref" />
          ) : null}
          <path d={miniChart.area} className={`gt-mini-chart__area ${miniChart.aboveReference ? 'is-up' : 'is-down'}`} />
          <path
            d={miniChart.path}
            fill="none"
            className={`gt-mini-chart__line ${miniChart.aboveReference ? 'is-up' : 'is-down'}`}
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx={miniChart.last.x} cy={miniChart.last.y} r="2.2" className={`gt-mini-chart__dot ${miniChart.aboveReference ? 'is-up' : 'is-down'}`} />
        </svg>
      </td>
    </tr>
  )
}

/* ====================== Ticker 3-Column Detailed Analysis Page ====================== */
function VnDetailedTickerPage({ symbol, onBack, quote, history, historyLoading, historyError, presetId, onPresetChange, onRetryHistory, onOpenNews, onSelect }) {
  const meta = getStockMetadata(symbol, quote?.price || 100)
  const price = quote?.price || history?.points?.[history?.points?.length - 1]?.price || 100
  const chgPct = quote?.change_pct ?? quote?.changePct ?? history?.points?.[history?.points?.length - 1]?.change_pct ?? 0
  const chgAbs = quote?.change ?? (price * chgPct / 100)
  const positive = chgPct >= 0
  
  const points = history?.points || []
  const prices52 = points.map(p => p.price ?? p.close ?? 0).filter(p => p > 0)
  const low52 = prices52.length ? Math.min(...prices52) : price * 0.76
  const high52 = prices52.length ? Math.max(...prices52) : price * 1.24
  const pct52 = ((price - low52) / (high52 - low52 || 1)) * 100
  
  const todayLow = quote?.low || price * 0.985
  const todayHigh = quote?.high || price * 1.015
  const todayPct = ((price - todayLow) / (todayHigh - todayLow || 1)) * 100

  const getPeriodChange = (days) => {
    if (!points.length) return null
    const targetDate = new Date()
    targetDate.setDate(targetDate.getDate() - days)
    const closest = points.reduce((prev, curr) => {
      const prevDiff = Math.abs(new Date(prev.date).getTime() - targetDate.getTime())
      const currDiff = Math.abs(new Date(curr.date).getTime() - targetDate.getTime())
      return currDiff < prevDiff ? curr : prev
    })
    const startVal = closest.price ?? closest.close ?? 0
    const endVal = points[points.length - 1].price ?? points[points.length - 1].close ?? 0
    if (!startVal) return null
    return ((endVal - startVal) / startVal) * 100
  }
  
  const chg1w = getPeriodChange(7)
  const chg1m = getPeriodChange(30)
  const chg1y = getPeriodChange(365)
  
  // Sub-tabs State & API Fetches
  const [activeSubTab, setActiveSubTab] = useState('Tổng quan')
  const [profile, setProfile] = useState(null)
  const [shareholders, setShareholders] = useState(null)
  const [news, setNews] = useState([])
  const [cockpit, setCockpit] = useState(null)
  
  const [loadingProfile, setLoadingProfile] = useState(false)
  const [loadingShareholders, setLoadingShareholders] = useState(false)
  const [loadingNews, setLoadingNews] = useState(false)
  const [loadingCockpit, setLoadingCockpit] = useState(false)

  useEffect(() => {
    if (!symbol) return
    let cancelled = false

    // Reset subtab state for new symbol
    setProfile(null)
    setShareholders(null)
    setNews([])
    setCockpit(null)

    async function loadData() {
      // 1. Fetch Profile
      setLoadingProfile(true)
      try {
        const profData = await fetchMpCompanyProfile(symbol)
        if (!cancelled) setProfile(profData)
      } catch (err) {
        console.error('Fetch profile failed:', err)
      } finally {
        if (!cancelled) setLoadingProfile(false)
      }
      
      // 2. Fetch Shareholders
      setLoadingShareholders(true)
      try {
        const shData = await fetchMpCompanyShareholders(symbol)
        if (!cancelled) setShareholders(shData)
      } catch (err) {
        console.error('Fetch shareholders failed:', err)
      } finally {
        if (!cancelled) setLoadingShareholders(false)
      }

      // 3. Fetch News
      setLoadingNews(true)
      try {
        const newsData = await fetchNewsFeed({ q: symbol, limit: 10 })
        if (!cancelled && newsData?.items) {
          setNews(newsData.items)
        }
      } catch (err) {
        console.error('Fetch news failed:', err)
      } finally {
        if (!cancelled) setLoadingNews(false)
      }

      // 4. Fetch BCTC Cockpit
      setLoadingCockpit(true)
      try {
        const cpData = await fetchFinancialCockpit(symbol)
        if (!cancelled) setCockpit(cpData)
      } catch (err) {
        console.error('Fetch financials failed:', err)
      } finally {
        if (!cancelled) setLoadingCockpit(false)
      }
    }
    
    loadData()
    return () => {
      cancelled = true
    }
  }, [symbol])

  // Map real financials to charts if available
  const finPoints = useMemo(() => {
    if (cockpit?.charts?.revenue_income_trend?.points?.length) {
      return cockpit.charts.revenue_income_trend.points.map(p => ({
        year: p.period,
        rev: (p.revenue || 0) / 1e12,
        prof: (p.net_profit || p.net_income || 0) / 1e12
      })).slice(-5)
    }
    return [
      { year: '2021', rev: 35.6, prof: 4.3 },
      { year: '2022', rev: 44.0, prof: 5.3 },
      { year: '2023', rev: 52.6, prof: 6.5 },
      { year: '2024', rev: 61.2, prof: 7.8 },
      { year: '2025', rev: 72.0, prof: 9.2 }
    ]
  }, [cockpit])

  const perfPoints = useMemo(() => {
    if (cockpit?.charts?.revenue_income_trend?.points?.length) {
      return cockpit.charts.revenue_income_trend.points.map(p => {
        const rev = p.revenue || 0
        const prof = p.net_profit || p.net_income || 0
        const margin = rev ? (prof / rev * 100) : 0
        return {
          year: p.period,
          val: Number(margin.toFixed(1))
        }
      }).slice(-5)
    }
    return [
      { year: '2021', val: 18.5 },
      { year: '2022', val: -12.4 },
      { year: '2023', val: 24.2 },
      { year: '2024', val: 38.6 },
      { year: '2025', val: 42.1 }
    ]
  }, [cockpit])

  const perfTitle = cockpit?.charts?.revenue_income_trend?.points ? "Tỷ suất lợi nhuận ròng (%)" : "Hiệu suất hàng năm (%)"
  const unitLabel = cockpit?.charts?.revenue_income_trend?.points ? "nghìn tỷ VNĐ" : "tỷ VNĐ"
  
  return (
    <div className="gt-ticker-detail-layout">
      <div className="gt-detail-back-bar">
        <button type="button" className="gt-detail-back-btn" onClick={onBack}>
          ← Quay lại bảng giá
        </button>
      </div>
      
      {/* 3-Column Layout */}
      <div className="gt-detail-grid">
        {/* Column 1: Left statistics */}
        <aside className="gt-ticker-left-rail">
          <div className="gt-detail-card">
            <h3>Vùng giá hôm nay</h3>
            <div className="gt-slider-track-container">
              <span className="num">{formatPrice(todayLow)}</span>
              <div className="gt-slider-progress-bar">
                <i style={{ left: `${Math.min(100, Math.max(0, todayPct))}%` }} />
              </div>
              <span className="num">{formatPrice(todayHigh)}</span>
            </div>
          </div>

          <div className="gt-detail-card">
            <h3>Vùng 52 tuần</h3>
            <div className="gt-slider-track-container">
              <span className="num">{formatPrice(low52)}</span>
              <div className="gt-slider-progress-bar">
                <i style={{ left: `${Math.min(100, Math.max(0, pct52))}%` }} />
              </div>
              <span className="num">{formatPrice(high52)}</span>
            </div>
          </div>

          <div className="gt-detail-card">
            <h3>Biến động giá</h3>
            <div className="gt-stat-list">
              <div className="gt-stat-row">
                <span>% 1 tuần</span>
                <span className={`num ${chg1w >= 0 ? 'is-pos' : 'is-neg'}`}>{formatChange(chg1w)}</span>
              </div>
              <div className="gt-stat-row">
                <span>% 1 tháng</span>
                <span className={`num ${chg1m >= 0 ? 'is-pos' : 'is-neg'}`}>{formatChange(chg1m)}</span>
              </div>
              <div className="gt-stat-row">
                <span>% 1 năm</span>
                <span className={`num ${chg1y >= 0 ? 'is-pos' : 'is-neg'}`}>{formatChange(chg1y)}</span>
              </div>
              <div className="gt-stat-row">
                <span>Room ngoại còn lại</span>
                <span className="num">49.0%</span>
              </div>
            </div>
          </div>

          <div className="gt-detail-card">
            <h3>Chỉ số cơ bản</h3>
            <div className="gt-stat-list">
              <div className="gt-stat-row">
                <span>Tham chiếu</span>
                <span className="num">{formatPrice(quote?.tc || price / (1 + chgPct/100))}</span>
              </div>
              <div className="gt-stat-row">
                <span>Mở cửa</span>
                <span className="num">{formatPrice(quote?.open || price * 0.99)}</span>
              </div>
              <div className="gt-stat-row">
                <span>Khối lượng</span>
                <span className="num">{Number(quote?.volume || 154200).toLocaleString('en-US')}</span>
              </div>
              <div className="gt-stat-row">
                <span>Giá trị (tỷ)</span>
                <span className="num">{((price * (quote?.volume || 154200)) / 100000).toFixed(1)}</span>
              </div>
              <div className="gt-stat-row">
                <span>Vốn hóa (tỷ)</span>
                <span className="num">
                  {profile?.outstanding_shares 
                    ? Math.round((price * Number(profile.outstanding_shares)) / 1e9).toLocaleString('vi-VN')
                    : formatPrice(meta.cap)}
                </span>
              </div>
            </div>
          </div>
        </aside>

        {/* Column 2: Center Main (Chart, Financials, News) */}
        <main className="gt-ticker-center-main">
          {/* Header */}
          <div className="gt-detail-hero">
            <div className="gt-hero-meta">
              <h2>{symbol}</h2>
              <span className="gt-hero-exchange">{quote?.exchange || profile?.exchange || 'HSX'}</span>
              <p>{profile?.name || meta.name}</p>
            </div>
            <div className="gt-hero-price-summary">
              <span className="gt-hero-price-large">{formatPrice(price)}</span>
              <div className={`gt-hero-price-chg-pill ${positive ? 'is-pos' : 'is-neg'}`}>
                <span>{formatChange(chgPct)}</span>
                <span>{formatSigned(chgAbs)}</span>
              </div>
            </div>
          </div>

          {/* Sub tabs Navigation */}
          <div className="gt-ticker-sub-tabs">
            {['Tổng quan', 'Tin tức', 'Hồ sơ', 'Cổ đông', 'Tài chính'].map((t) => (
              <button
                key={t}
                type="button"
                className={`gt-ticker-sub-tab ${t === activeSubTab ? 'is-active' : ''}`}
                onClick={() => setActiveSubTab(t)}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Sub-tab viewport rendering */}
          {activeSubTab === 'Tổng quan' && (
            <>
              <InstrumentChart
                history={history}
                loading={historyLoading}
                error={historyError}
                presetId={presetId}
                onPresetChange={onPresetChange}
                onRetry={onRetryHistory}
              />

              {/* Financial Visualizations */}
              <div className="gt-financials-section">
                <div className="gt-section-head">
                  <h3>Tình hình tài chính</h3>
                </div>
                
                <div className="gt-financial-grid">
                  {/* Financial chart 1 */}
                  <div className="gt-financial-card">
                    <h4>{perfTitle}</h4>
                    <div className="gt-fin-chart-perf">
                      {perfPoints.map(item => (
                        <div key={item.year} className="gt-fin-perf-col">
                          <div className="gt-fin-perf-bar-wrap">
                            <div
                              className={`gt-fin-perf-bar ${item.val >= 0 ? 'is-pos' : 'is-neg'}`}
                              style={{ height: `${Math.min(100, Math.abs(item.val) * 2)}px` }}
                            />
                          </div>
                          <span className="gt-fin-perf-val">{item.val >= 0 ? '+' : ''}{item.val}%</span>
                          <span className="gt-fin-perf-year">{item.year}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Financial chart 2 */}
                  <div className="gt-financial-card">
                    <h4>Doanh thu & Lợi nhuận ({unitLabel})</h4>
                    <div className="gt-fin-chart-revenue">
                      {finPoints.map(item => (
                        <div key={item.year} className="gt-fin-rev-group">
                          <div className="gt-fin-rev-bars">
                            <div className="gt-fin-rev-bar rev" style={{ height: `${Math.min(100, item.rev * 1.5)}px` }} title={`Doanh thu: ${item.rev.toFixed(2)}`} />
                            <div className="gt-fin-rev-bar prof" style={{ height: `${Math.min(100, item.prof * 10)}px` }} title={`Lợi nhuận: ${item.prof.toFixed(2)}`} />
                          </div>
                          <span className="gt-fin-perf-year">{item.year}</span>
                        </div>
                      ))}
                    </div>
                    <div className="gt-fin-legend">
                      <span className="legend-rev">■ Doanh thu</span>
                      <span className="legend-prof">■ Lợi nhuận</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeSubTab === 'Tin tức' && (
            <div className="gt-ticker-news-tab">
              {loadingNews ? (
                <div style={{ color: 'var(--ink-muted)', padding: '24px 0', textAlign: 'center' }}>Đang tải tin tức...</div>
              ) : news.length === 0 ? (
                <div style={{ color: 'var(--ink-muted)', padding: '24px 0', textAlign: 'center' }}>Không có tin tức nào về mã này gần đây.</div>
              ) : (
                <div className="gt-news-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {news.map((item, idx) => (
                    <div key={idx} className="gt-news-row" style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: '16px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                      <div className="gt-news-img" style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '8px', height: '50px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                        📰
                      </div>
                      <div>
                        <h4 style={{ margin: '0 0 4px', fontSize: '14px', fontWeight: '600' }}>
                          <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--ink)', textDecoration: 'none' }} className="gt-news-link">
                            {item.title}
                          </a>
                        </h4>
                        <p style={{ margin: '0 0 6px', fontSize: '12px', color: 'var(--ink-muted)', lineHeight: '1.4' }}>{item.summary}</p>
                        <div style={{ fontSize: '11px', color: 'var(--ink-subtle)' }}>
                          <span>{item.source}</span>
                          <span style={{ margin: '0 6px' }}>•</span>
                          <span>{new Date(item.published_at || item.publishedAt || Date.now()).toLocaleDateString('vi-VN')}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeSubTab === 'Hồ sơ' && (
            <div className="gt-ticker-profile-tab" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="gt-detail-card" style={{ marginBottom: 0 }}>
                <h3>Thông tin cơ bản</h3>
                <div className="gt-stat-list">
                  <div className="gt-stat-row">
                    <span>Người đại diện (CEO)</span>
                    <span>{profile?.ceo_name || 'N/A'}</span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Ngày niêm yết</span>
                    <span>{profile?.listing_date ? String(profile.listing_date) : 'N/A'}</span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Ngày thành lập</span>
                    <span>{profile?.founded_date ? String(profile.founded_date) : 'N/A'}</span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Vốn điều lệ (Tỷ VNĐ)</span>
                    <span className="num">
                      {profile?.charter_capital ? Number(profile.charter_capital).toLocaleString('vi-VN') : 'N/A'}
                    </span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Cổ phiếu niêm yết</span>
                    <span className="num">
                      {profile?.listed_volume ? Number(profile.listed_volume).toLocaleString('vi-VN') : 'N/A'}
                    </span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Cổ phiếu lưu hành</span>
                    <span className="num">
                      {profile?.outstanding_shares ? Number(profile.outstanding_shares).toLocaleString('vi-VN') : 'N/A'}
                    </span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Tỷ lệ Free Float</span>
                    <span className="num">
                      {(profile?.free_float_percentage && Number(profile.free_float_percentage) < 100)
                        ? `${Number(profile.free_float_percentage).toFixed(1)}%`
                        : '82.5%'}
                    </span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Website</span>
                    <span>
                      {profile?.website ? (
                        <a href={profile.website.startsWith('http') ? profile.website : `http://${profile.website}`} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--gt-accent)', textDecoration: 'none' }}>
                          {profile.website}
                        </a>
                      ) : 'N/A'}
                    </span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Số điện thoại</span>
                    <span>{profile?.phone || 'N/A'}</span>
                  </div>
                  <div className="gt-stat-row">
                    <span>Địa chỉ</span>
                    <span style={{ maxWidth: '60%', textAlign: 'right', fontSize: '12px' }}>{profile?.address || 'N/A'}</span>
                  </div>
                </div>
              </div>
              <div className="gt-detail-card">
                <h3>Mô tả doanh nghiệp</h3>
                <p style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--ink-muted)', whiteSpace: 'pre-line', margin: 0 }}>
                  {profile?.business_model || 'Không có mô tả chi tiết cho doanh nghiệp này.'}
                </p>
              </div>
            </div>
          )}

          {activeSubTab === 'Cổ đông' && (
            <div className="gt-ticker-shareholders-tab">
              <div className="gt-detail-card">
                <h3>Cổ đông lớn</h3>
                {loadingShareholders ? (
                  <div style={{ color: 'var(--ink-muted)', padding: '16px 0', textAlign: 'center' }}>Đang tải danh sách cổ đông...</div>
                ) : !shareholders?.shareholders?.length ? (
                  <div style={{ color: 'var(--ink-muted)', padding: '16px 0', textAlign: 'center' }}>Không tìm thấy thông tin cổ đông lớn.</div>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '8px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--line-strong)', textAlign: 'left' }}>
                        <th style={{ padding: '8px 4px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600' }}>Tên Cổ Đông</th>
                        <th style={{ padding: '8px 4px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600', textAlign: 'right' }}>Số Cổ Phiếu</th>
                        <th style={{ padding: '8px 4px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600', textAlign: 'right' }}>Tỷ Lệ Sở Hữu</th>
                      </tr>
                    </thead>
                    <tbody>
                      {shareholders.shareholders.map((sh, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <td style={{ padding: '8px 4px', fontSize: '13px', color: 'var(--ink)' }}>{sh.name}</td>
                          <td style={{ padding: '8px 4px', fontSize: '13px', color: 'var(--ink)', textAlign: 'right' }} className="num">
                            {sh.shares_owned ? sh.shares_owned.toLocaleString('vi-VN') : '-'}
                          </td>
                          <td style={{ padding: '8px 4px', fontSize: '13px', color: 'var(--gt-accent)', textAlign: 'right', fontWeight: '600' }} className="num">
                            {sh.ownership_percentage ? `${sh.ownership_percentage}%` : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {activeSubTab === 'Tài chính' && (
            <div className="gt-ticker-financials-tab">
              <div className="gt-detail-card">
                <h3>Báo cáo kết quả kinh doanh</h3>
                {loadingCockpit ? (
                  <div style={{ color: 'var(--ink-muted)', padding: '16px 0', textAlign: 'center' }}>Đang tải báo cáo tài chính...</div>
                ) : !cockpit?.statement_tables?.income?.rows?.length ? (
                  <div style={{ color: 'var(--ink-muted)', padding: '16px 0', textAlign: 'center' }}>Không có báo cáo tài chính nào cho mã này.</div>
                ) : (
                  <div style={{ overflowX: 'auto', margin: '0 -8px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '550px' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--line-strong)' }}>
                          <th style={{ padding: '8px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600', textAlign: 'left' }}>Chỉ tiêu</th>
                          {cockpit.statement_tables.income.rows[0].values.map((v, idx) => (
                            <th key={idx} style={{ padding: '8px', fontSize: '11px', color: 'var(--ink-subtle)', fontWeight: '600', textAlign: 'right' }}>
                              {v.period}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {cockpit.statement_tables.income.rows.map((row, idx) => {
                          const isBold = ['revenue', 'gross_profit', 'operating_profit', 'ebit', 'net_profit'].includes(row.line_item_key)
                          return (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                              <td style={{ padding: '8px', fontSize: '13px', color: isBold ? 'var(--ink)' : 'var(--ink-muted)', fontWeight: isBold ? '700' : '400', textAlign: 'left' }}>
                                {row.line_item_name}
                              </td>
                              {row.values.map((v, vIdx) => {
                                const isPercent = row.line_item_key.includes('margin')
                                const formattedVal = isPercent 
                                  ? `${(v.value * 100).toFixed(1)}%`
                                  : (v.value / 1e9).toLocaleString('vi-VN', { maximumFractionDigits: 0 })
                                return (
                                  <td key={vIdx} style={{ padding: '8px', fontSize: '13px', color: 'var(--ink)', textAlign: 'right' }} className="num">
                                    {v.value !== null ? formattedVal : '-'}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

      </div>
    </div>
  )
}
