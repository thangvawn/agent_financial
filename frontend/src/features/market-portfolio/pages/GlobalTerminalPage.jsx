import { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { GripHorizontal, Maximize2, Minimize2, Star } from 'lucide-react'

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
import TradingViewRealtimeWidget from './TradingViewRealtimeWidget'
import { isTradingViewSupported } from './tradingViewUtils'
import VnOrderBookWidget from './VnOrderBookWidget'
import { IndexCardsBar } from '../components/IndexCardsBar'
import MarketOverviewTab from '../components/MarketOverviewTab'
import { InstrumentSparkline } from '../components/PriceSparkline'
import './global-terminal.css'

const TAB_CATEGORY = {
  dashboard: 'dashboard',
  markets: 'indices',
  indices: 'indices',
  vn_stocks: 'vn_stocks',
  crypto: 'crypto',
  commodities: 'commodities',
  fx: 'fx',
}

const TAB_MAP = {
  market_overview: { view: 'vn_stocks', default_symbol: 'VNINDEX' },
  dashboard: { view: 'vn_stocks', default_symbol: 'FPT' },
  indices: { view: 'indices', default_symbol: 'VNINDEX' },
  fx: { view: 'fx', default_symbol: 'DXY' },
}

const DEFAULT_TABS = [
  { id: 'dashboard', label: 'Dashboard', default_symbol: 'VNINDEX' },
  { id: 'vn_stocks', label: 'VN Stocks', default_symbol: 'FPT' },
  { id: 'markets', label: 'Indices', default_symbol: 'VNINDEX' },
]

const PRIORITY = ['VNINDEX', 'VN30', 'HNXINDEX', 'UPCOMINDEX', 'SPX', 'NDX', 'XAU', 'BTC', 'ETH', 'FPT', 'VCB', 'MWG']

const CHART_PRESETS = [
  { id: '1m', label: '1m', period: 'max', interval: '1m', desc: 'Nến 1 phút (Max)' },
  { id: '5m', label: '5m', period: 'max', interval: '5m', desc: 'Nến 5 phút (Max)' },
  { id: '15m', label: '15m', period: 'max', interval: '15m', desc: 'Nến 15 phút (Max)' },
  { id: '30m', label: '30m', period: 'max', interval: '30m', desc: 'Nến 30 phút (Max)' },
  { id: '1H', label: '1H', period: 'max', interval: '1h', desc: 'Nến 1 giờ (Max)' },
  { id: '1D', label: '1D', period: '1y', interval: '1d', desc: 'Nến 1 ngày (1 năm)' },
  { id: '1W', label: '1W', period: 'max', interval: '1wk', desc: 'Nến 1 tuần (Max)' },
  { id: '5Y', label: '5Y', period: '5y', interval: '1d', desc: 'Nến 1 ngày (5 năm)' },
  { id: 'MAX', label: 'Max', period: 'max', interval: '1d', desc: 'Nến 1 ngày (Toàn bộ 14+ năm)' },
]

const DEFAULT_PRESET_ID = '1D'
const MARKET_FAVORITES_KEY = 'northstar.market-favorites'
const DEFAULT_GLOBAL_POLL_MS = 60_000
const DEFAULT_VN_POLL_MS = 15_000
const MIN_POLL_MS = 5_000
const HISTORY_REFRESH_INTERVAL_MS = {
  '1m': 15_000,
  '5m': 30_000,
  '15m': 60_000,
  '30m': 120_000,
  '1H': 180_000,
  '1D': 300_000,
  '1W': 600_000,
  '5Y': 900_000,
  MAX: 900_000,
}
const GLOBAL_SYMBOL_VIEWS = {
  SPX: 'indices',
  NDX: 'indices',
  RUT: 'indices',
  DJI: 'indices',
  NASDAQ: 'indices',
  DAX: 'indices',
  EUROSTOXX: 'indices',
  CAC40: 'indices',
  FTSE: 'indices',
  NIKKEI: 'indices',
  HANGSENG: 'indices',
  KOSPI: 'indices',
  ASX200: 'indices',
  TSX: 'indices',
  BOVESPA: 'indices',
  NIFTY50: 'indices',
  SSEC: 'indices',
  BTC: 'crypto',
  ETH: 'crypto',
  USDT: 'crypto',
  BNB: 'crypto',
  XRP: 'crypto',
  USDC: 'crypto',
  SOL: 'crypto',
  TRX: 'crypto',
  DOGE: 'crypto',
  LINK: 'crypto',
  ADA: 'crypto',
  XLM: 'crypto',
  NEAR: 'crypto',
  BCH: 'crypto',
  UNI: 'crypto',
  HBAR: 'crypto',
  LTC: 'crypto',
  AVAX: 'crypto',
  SUI: 'crypto',
  TON: 'crypto',
  CRO: 'crypto',
  SHIB: 'crypto',
  DOT: 'crypto',
  PEPE: 'crypto',
  ICP: 'crypto',
  ARB: 'crypto',
  FIL: 'crypto',
  APT: 'crypto',
  OP: 'crypto',
  MKR: 'crypto',
  INJ: 'crypto',
  XAU: 'commodities',
  SILVER: 'commodities',
  COPPER: 'commodities',
  PLATINUM: 'commodities',
  PALLADIUM: 'commodities',
  WTI: 'commodities',
  BRENT: 'commodities',
  NATGAS: 'commodities',
  CORN: 'commodities',
  WHEAT: 'commodities',
  SOYBEAN: 'commodities',
  SUGAR: 'commodities',
  COFFEE: 'commodities',
  COCOA: 'commodities',
  COTTON: 'commodities',
  HEATINGOIL: 'commodities',
  GASOLINE: 'commodities',
  OATS: 'commodities',
  RICE: 'commodities',
  LIVE_CATTLE: 'commodities',
  FEEDER_CATTLE: 'commodities',
  LEAN_HOGS: 'commodities',
  ORANGE_JUICE: 'commodities',
  DXY: 'fx',
  EURUSD: 'fx',
  USDJPY: 'fx',
  AUDUSD: 'fx',
  USDCNH: 'fx',
  GBPUSD: 'fx',
  USDCHF: 'fx',
  USDCAD: 'fx',
  NZDUSD: 'fx',
  USDHKD: 'fx',
  USDMXN: 'fx',
  USDTRY: 'fx',
  USDINR: 'fx',
  EURGBP: 'fx',
  EURJPY: 'fx',
}

export default function GlobalTerminalPage({ activeTab = 'dashboard', onOpenNews }) {
  const mappedView = TAB_MAP[activeTab]?.view || 'dashboard'
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
  const [studentSector, setStudentSector] = useState('')
  const [vnNavigation, setVnNavigation] = useState({ selection: '', offset: 0 })
  const vnSelection = JSON.stringify([vnSort, vnExchange, studentSector, vnPageSize])
  const vnOffset = vnNavigation.selection === vnSelection ? vnNavigation.offset : 0
  const vnQueryKey = JSON.stringify([vnSelection, vnOffset])
  const [detailedMode] = useState(false)
  const [activeDetailSymbol, setActiveDetailSymbol] = useState(null)
  const [visibilityTick, setVisibilityTick] = useState(0)
  const [favoriteSymbols, setFavoriteSymbols] = useState(() => {
    if (typeof window === 'undefined') return []
    try {
      const stored = JSON.parse(window.localStorage.getItem(MARKET_FAVORITES_KEY) || '[]')
      return Array.isArray(stored) ? stored : []
    } catch {
      return []
    }
  })
  
  const [isTabFullscreen, setIsTabFullscreen] = useState(false)

  const toggleTabFullscreen = useCallback(() => {
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
      const elem = document.documentElement
      if (elem?.requestFullscreen) {
        elem.requestFullscreen().catch(() => {
          setIsTabFullscreen((v) => !v)
        })
      } else if (elem?.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen()
      } else {
        setIsTabFullscreen((v) => !v)
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {
          setIsTabFullscreen(false)
        })
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen()
      } else {
        setIsTabFullscreen(false)
      }
    }
  }, [])

  useEffect(() => {
    function handleFsChange() {
      setIsTabFullscreen(Boolean(document.fullscreenElement || document.webkitFullscreenElement))
    }
    document.addEventListener('fullscreenchange', handleFsChange)
    document.addEventListener('webkitfullscreenchange', handleFsChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFsChange)
      document.removeEventListener('webkitfullscreenchange', handleFsChange)
    }
  }, [])
  
  const terminalRequestSeqRef = useRef(0)
  const terminalRefreshRequestedRef = useRef(false)
  const historyRequestSeqRef = useRef(0)
  const vnRequestSeqRef = useRef(0)
  const historyCacheRef = useRef(new Map())
  const commandInputRef = useRef(null)
  const terminalPollDelayRef = useRef(DEFAULT_GLOBAL_POLL_MS)
  const vnPollDelayRef = useRef(DEFAULT_VN_POLL_MS)

  useEffect(() => {
    function handleShortcut(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        commandInputRef.current?.focus()
      }
      if (event.key === 'Escape' && isTabFullscreen) {
        if (document.fullscreenElement) {
          document.exitFullscreen?.().catch(() => {})
        }
        setIsTabFullscreen(false)
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [isTabFullscreen])

  // A hidden browser tab should not keep hitting the provider-backed API.
  // Incrementing the tick when the tab becomes visible makes the next poll
  // immediate instead of waiting for the previous timeout to elapse.
  useEffect(() => {
    function handleVisibilityChange() {
      if (document.visibilityState === 'visible') setVisibilityTick((value) => value + 1)
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()

    async function run() {
      const requestId = ++terminalRequestSeqRef.current
      setLoading(true)
      setError('')
      try {
        const data = await fetchGlobalTerminal({
          view: activeView,
          refresh: terminalRefreshRequestedRef.current,
          signal: controller.signal,
        })
        if (cancelled || requestId !== terminalRequestSeqRef.current) return
        terminalRefreshRequestedRef.current = false
        const serverInterval = Number(data?.terminal?.poll_interval_seconds ?? data?.terminal?.refresh_interval_seconds)
        if (Number.isFinite(serverInterval) && serverInterval > 0) {
          terminalPollDelayRef.current = Math.max(MIN_POLL_MS, serverInterval * 1000)
        }
        setPayload(data)
        setSelectedSymbol((current) => current || data?.terminal?.default_symbol || 'VNINDEX')
        return true
      } catch (err) {
        if (err.name === 'AbortError') return
        if (cancelled || requestId !== terminalRequestSeqRef.current) return
        setError(err.message)
        return false
      } finally {
        if (!cancelled && requestId === terminalRequestSeqRef.current) setLoading(false)
      }
    }

    let timer = null
    let failures = 0
    const schedule = (success) => {
      if (cancelled) return
      // Do not keep a timer alive for a hidden tab. The visibility effect
      // below starts a fresh request as soon as the tab becomes visible.
      if (document.visibilityState === 'hidden') return
      failures = success ? 0 : failures + 1
      const delay = success
        ? terminalPollDelayRef.current
        : Math.min(120000, terminalPollDelayRef.current * (2 ** Math.min(failures, 3)))
      timer = window.setTimeout(tick, delay)
    }
    const tick = async () => {
      if (cancelled) return
      if (document.visibilityState === 'hidden') {
        schedule(true)
        return
      }
      const success = await run()
      schedule(success !== false)
    }
    tick()
    return () => {
      cancelled = true
      controller.abort()
      if (timer) window.clearTimeout(timer)
    }
  }, [activeView, refreshTick, visibilityTick])

  useEffect(() => {
    if (activeView !== 'vn_stocks') return undefined
    let cancelled = false
    const controller = new AbortController()
    let refreshRequested = refreshTick > 0
    async function run() {
      const requestId = ++vnRequestSeqRef.current
      setVnLoading(true)
      setVnError('')
      try {
        const data = await fetchVnSnapshot({
          sort: vnSort,
          exchange: vnExchange,
          industry: studentSector,
          offset: vnOffset,
          limit: vnPageSize,
          refresh: refreshRequested,
          signal: controller.signal,
        })
        refreshRequested = false
        if (cancelled || requestId !== vnRequestSeqRef.current) return
        const serverInterval = Number(data?.refresh_interval_seconds)
        if (Number.isFinite(serverInterval) && serverInterval > 0) {
          vnPollDelayRef.current = Math.max(MIN_POLL_MS, serverInterval * 1000)
        }
        setVnSnapshot({ ...data, queryKey: vnQueryKey })
        return true
      } catch (err) {
        if (err.name === 'AbortError') return
        if (cancelled || requestId !== vnRequestSeqRef.current) return
        setVnError(err.message)
        return false
      } finally {
        if (!cancelled && requestId === vnRequestSeqRef.current) setVnLoading(false)
      }
    }
    let timer = null
    let failures = 0
    const schedule = (success) => {
      if (cancelled) return
      if (document.visibilityState === 'hidden') return
      failures = success ? 0 : failures + 1
      const delay = success
        ? vnPollDelayRef.current
        : Math.min(120000, vnPollDelayRef.current * (2 ** Math.min(failures, 3)))
      timer = window.setTimeout(tick, delay)
    }
    const tick = async () => {
      if (cancelled) return
      if (document.visibilityState === 'hidden') {
        schedule(true)
        return
      }
      const success = await run()
      schedule(success !== false)
    }
    tick()
    return () => {
      cancelled = true
      controller.abort()
      if (timer) window.clearTimeout(timer)
    }
  }, [activeView, vnSort, vnExchange, studentSector, vnPageSize, vnOffset, vnQueryKey, refreshTick, visibilityTick])

  useEffect(() => {
    let cancelled = false
    const controller = new AbortController()

    async function run() {
      const requestId = ++historyRequestSeqRef.current
      const preset = CHART_PRESETS.find((item) => item.id === presetId) || CHART_PRESETS[5]
      const cacheKey = `${selectedSymbol}:${preset.id}`
      const cached = historyCacheRef.current.get(cacheKey)
      if (cached?.data) {
        setHistory(cached.data)
        if (cached.refreshVersion === historyRefreshTick) {
          setHistoryError('')
          setHistoryLoading(false)
          return
        }
      }
      setHistoryLoading(true)
      setHistoryError('')
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

  // Keep the chart's last candle moving while the terminal is visible. The
  // selected preset controls cadence so intraday charts refresh more often
  // without repeatedly downloading long historical ranges.
  useEffect(() => {
    const delay = HISTORY_REFRESH_INTERVAL_MS[presetId] || 300_000
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') setHistoryRefreshTick((value) => value + 1)
    }, delay)
    return () => window.clearInterval(timer)
  }, [presetId, selectedSymbol, visibilityTick])

  // Sync activeView when parent tab changes
  useEffect(() => {
    const mapped = TAB_MAP[activeTab]?.view || 'dashboard'
    setActiveView(mapped)
    const defaultSymbol = TAB_MAP[activeTab]?.default_symbol
    if (defaultSymbol) setSelectedSymbol(defaultSymbol)
    setActiveDetailSymbol(null)
  }, [activeTab])

  function handleTab(nextView) {
    setActiveView(nextView)
    const tabDefault = payload?.navigation?.tabs?.find((tab) => tab.id === nextView)?.default_symbol
      || DEFAULT_TABS.find((tab) => tab.id === nextView)?.default_symbol
    if (tabDefault) setSelectedSymbol(tabDefault)
    setActiveDetailSymbol(null)
  }

  function handleRefreshAll() {
    if (activeView !== 'vn_stocks') terminalRefreshRequestedRef.current = true
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
      const globalView = GLOBAL_SYMBOL_VIEWS[sym]
      if (globalView) {
        setActiveView(globalView)
        setSelectedSymbol(sym)
        setActiveDetailSymbol(null)
        setCommand('')
        return
      }
      setSelectedSymbol(sym)
      if (isVnTab) setActiveDetailSymbol(sym)
    }
    setCommand('')
  }

  const isVnTab = activeView === 'vn_stocks'
  const isMarketOverview = activeTab === 'market_overview'

  const currentVnSnapshot = vnSnapshot?.queryKey === vnQueryKey ? vnSnapshot : null
  const filteredVnItems = currentVnSnapshot?.items || []
  const boardLoading = vnLoading || (!currentVnSnapshot && !vnError)
  const boardError = vnError
  const boardTotal = currentVnSnapshot?.total || 0
  const vnPage = Math.floor(vnOffset / vnPageSize) + 1
  const setVnOffset = offset => setVnNavigation({ selection: vnSelection, offset })

  function handleSelectRow(sym) {
    setSelectedSymbol(sym)
    const isIndex = ['VNINDEX', 'VN30', 'HNXINDEX', 'HNX30', 'UPCOM'].includes(sym)
    if (!isIndex && isVnTab) {
      setActiveDetailSymbol(sym)
    } else {
      setActiveDetailSymbol(null)
    }
  }

  function handleToggleFavorite(symbol) {
    setFavoriteSymbols((current) => {
      const next = current.includes(symbol)
        ? current.filter((item) => item !== symbol)
        : [...current, symbol]
      window.localStorage.setItem(MARKET_FAVORITES_KEY, JSON.stringify(next))
      return next
    })
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
  const indexItems = sortByPriority([...(widgets.global_indices || []), ...(widgets.global_snapshot || [])])
  const selectedQuote = isVnTab
    ? (vnSnapshot?.items || []).find((item) => item.symbol === selectedSymbol)
    : findQuote(widgets, selectedSymbol)
  const effectiveTimestamp = isVnTab
    ? (vnSnapshot?.last_success_at || vnSnapshot?.as_of)
    : (selectedQuote?.updated_at || payload?.terminal?.as_of)
  const terminalFreshness = isVnTab
    ? (vnSnapshot?.freshness || 'degraded')
    : (payload?.terminal?.freshness || 'degraded')
  const selectedQuoteAge = ageSecondsFrom(selectedQuote?.updated_at)
  const quoteMaxAge = selectedQuote?.data_interval === 'spot' ? 5 * 60 : selectedQuote?.data_interval === '5m' ? 20 * 60 : null
  const quoteIsStale = Number.isFinite(selectedQuoteAge) && quoteMaxAge !== null && selectedQuoteAge > quoteMaxAge
  const effectiveFreshness = !isVnTab && terminalFreshness === 'fresh' && (
    selectedQuote?.data_interval === '1d' || quoteIsStale
  ) ? 'stale' : terminalFreshness
  const effectiveAgeSeconds = isVnTab
    ? vnSnapshot?.age_seconds
    : ageSecondsFrom(effectiveTimestamp)
  const effectiveSource = isVnTab
    ? vnSnapshot?.source
    : (selectedQuote?.source || payload?.topics?.find((topic) => topic.topic === 'global:indices')?.source || history?.source)

  return (
    <section className={`global-terminal ${isTabFullscreen ? 'is-fullscreen' : ''}`}>
      {!isVnTab || activeDetailSymbol ? (
        <CompactSearchBar
          inputRef={commandInputRef}
          command={command}
          onCommandChange={setCommand}
          onCommandSubmit={handleCommandSubmit}
          timestamp={effectiveTimestamp}
          freshness={effectiveFreshness}
          ageSeconds={effectiveAgeSeconds}
          syncing={loading || vnLoading || historyLoading}
          onRefresh={handleRefreshAll}
          isFullscreen={isTabFullscreen}
          onToggleFullscreen={toggleTabFullscreen}
        />
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
            isFullscreen={isTabFullscreen}
            onToggleFullscreen={toggleTabFullscreen}
          />
        ) : isMarketOverview ? (
          <MarketOverviewTab
            indexItems={indexItems}
            selectedSymbol={selectedSymbol}
            onSelectSymbol={handleSelectRow}
          />
        ) : (
          <div className="gt-full-workspace">
            {/* 4 Card chỉ số thị trường VNINDEX, VN30, HNX30, UPCOM */}
            <IndexCardsBar
              indexItems={indexItems}
              vnItems={vnSnapshot?.items || []}
              marketSummary={vnSnapshot?.summary || {}}
              selectedSymbol={selectedSymbol}
              onSelect={handleSelectRow}
            />

            {/* Sắp xếp và lựa chọn phạm vi bảng giá */}
            <FilterChipsBar
              sort={vnSort}
              onSortChange={setVnSort}
              exchange={vnExchange}
              onExchangeChange={setVnExchange}
              pageSize={vnPageSize}
              onPageSizeChange={setVnPageSize}
              sectorOptions={vnSnapshot?.industry_options || []}
              unclassifiedCount={vnSnapshot?.industry_coverage?.unclassified || 0}
              selectedSector={studentSector}
              onSelectSector={setStudentSector}
            />

            <div className="gt-board-status" role="status">
              <span>{boardLoading ? 'Đang tải bảng giá…' : `Hiển thị ${filteredVnItems.length} / ${boardTotal} mã.`}</span>
              {(vnPage > 1 || currentVnSnapshot?.next_offset != null) && (
                <nav aria-label="Phân trang bảng giá">
                  <button type="button" className="gt-chip" onClick={() => setVnOffset(Math.max(0, vnOffset - vnPageSize))} disabled={vnPage <= 1 || boardLoading}>Trước</button>
                  <span>Trang {vnPage}</span>
                  <button type="button" className="gt-chip" onClick={() => setVnOffset(currentVnSnapshot.next_offset)} disabled={currentVnSnapshot?.next_offset == null || boardLoading}>Tiếp</button>
                </nav>
              )}
            </div>
            <div style={{ marginTop: '10px' }}>
              {detailedMode ? (
                <VnPriceBoard
                  items={filteredVnItems}
                  selectedSymbol={selectedSymbol}
                  onSelect={handleSelectRow}
                  total={boardTotal}
                  loading={boardLoading}
                  error={boardError}
                />
              ) : (
                <VnOverviewTable
                  items={filteredVnItems}
                  selectedSymbol={selectedSymbol}
                  onSelect={handleSelectRow}
                  total={boardTotal}
                  loading={boardLoading}
                  error={boardError}
                  favoriteSymbols={favoriteSymbols}
                  onToggleFavorite={handleToggleFavorite}
                />
              )}
            </div>
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
              symbol={selectedSymbol}
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

      {!isMarketOverview && <StatusBar
        topics={payload?.topics || []}
        timestamp={effectiveTimestamp}
        source={effectiveSource}
        freshness={effectiveFreshness}
        ageSeconds={effectiveAgeSeconds}
      />}
    </section>
  )
}

/* ====================== Compact Search Bar ====================== */
function CompactSearchBar({ inputRef, command, onCommandChange, onCommandSubmit, timestamp, freshness, ageSeconds, syncing, onRefresh, isFullscreen, onToggleFullscreen }) {
  const status = syncing ? 'syncing' : freshness || 'degraded'
  const statusLabel = syncing ? 'SYNC' : status === 'fresh' ? 'LIVE' : status === 'stale' ? 'STALE' : 'DEGRADED'
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
        <span className={`gt-search-bar__dot ${status} ${syncing ? 'is-syncing' : ''}`} aria-hidden="true" />
        <span className="gt-search-bar__live" title={freshnessHelp(freshness)}>{statusLabel}</span>
        <span>{formatTimestamp(timestamp)}</span>
        {Number.isFinite(Number(ageSeconds)) ? <span className="gt-search-bar__age">{formatAge(ageSeconds)}</span> : null}
        <button
          type="button"
          className="gt-search-bar__refresh"
          onClick={onRefresh}
          disabled={syncing}
          title="Làm mới dữ liệu"
          aria-label="Làm mới dữ liệu"
        >
          ↻
        </button>
        {onToggleFullscreen ? (
          <button
            type="button"
            className="gt-search-bar__refresh"
            onClick={onToggleFullscreen}
            title={isFullscreen ? 'Thu nhỏ tab (ESC)' : 'Toàn màn hình tab'}
            aria-label={isFullscreen ? 'Thu nhỏ' : 'Toàn màn hình'}
            style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}
          >
            {isFullscreen ? <Minimize2 size={13} strokeWidth={2} /> : <Maximize2 size={13} strokeWidth={2} />}
          </button>
        ) : null}
      </div>
    </header>
  )
}


const INDEX_REGIONS = [
  { id: 'vietnam', label: 'Việt Nam', symbols: ['VNINDEX', 'VN30', 'HNXINDEX', 'UPCOMINDEX'] },
  { id: 'us', label: 'Mỹ', symbols: ['SPX', 'NDX', 'RUT', 'DJI', 'NASDAQ'] },
  { id: 'europe', label: 'Châu Âu', symbols: ['DAX', 'EUROSTOXX', 'CAC40', 'FTSE'] },
  { id: 'asia', label: 'Châu Á', symbols: ['NIKKEI', 'HANGSENG', 'KOSPI'] },
  { id: 'other', label: 'Toàn cầu', symbols: ['ASX200', 'TSX', 'BOVESPA', 'NIFTY50', 'SSEC'] },
]

const VN_INDEX_FALLBACKS = [
  { symbol: 'VNINDEX', name: 'VN-Index', price: 1737.71, change: -11.59, change_pct: -0.663, focus: 'HOSE' },
  { symbol: 'VN30', name: 'VN30', price: 1875.99, change: -14.58, change_pct: -0.771, focus: 'VN30' },
  { symbol: 'HNXINDEX', name: 'HNX-Index', price: 266.75, change: -1.91, change_pct: -0.711, focus: 'HNX' },
  { symbol: 'UPCOMINDEX', name: 'UPCoM-Index', price: 125.93, change: -0.59, change_pct: -0.466, focus: 'UPCoM' },
]

function IndicesMarketBoard({ items, selectedSymbol, onSelect }) {
  const lookup = new Map(items.map((item) => [String(item.symbol || '').toUpperCase(), item]))
  return (
    <section className="gt-indices-board" aria-label="Các chỉ số thị trường">
      {INDEX_REGIONS.map((region) => {
        let regionItems = region.symbols.map((symbol) => lookup.get(symbol.toUpperCase())).filter(Boolean)
        if (!regionItems.length && region.id === 'vietnam') {
          regionItems = VN_INDEX_FALLBACKS
        }
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

const IndexMarketRow = memo(function IndexMarketRow({ item, index, selected, onSelect }) {
  const change = Number(item.change_pct || 0)
  const positive = change > 0
  const negative = change < 0
  const toneClass = positive ? 'is-pos gt-px-up' : negative ? 'is-neg gt-px-dn' : 'is-ref gt-px-tc'
  return (
    <tr className={selected ? 'is-selected' : ''} onClick={() => onSelect(item.symbol)}>
      <td className="num gt-indices-board__rank">{index}</td>
      <td className="gt-indices-board__symbol"><strong className={toneClass}>{item.symbol}</strong><small>{item.name || item.focus || '—'}</small></td>
      <td className={`num strong ${toneClass}`}>{formatPrice(item.price)}</td>
      <td className={`num ${toneClass}`}>{formatSigned(item.change)}</td>
      <td className={`num ${toneClass}`}>{formatChange(item.change_pct)}</td>
      <td className="gt-indices-board__chart">
        <InstrumentSparkline symbol={item.symbol} width={120} height={36}/>
      </td>
    </tr>
  )
})

/* ====================== Filter Chips Bar (Hợp nhất toàn bộ bộ lọc & chế độ xem) ====================== */
function FilterChipsBar({
  sort,
  onSortChange,
  exchange,
  onExchangeChange,
  pageSize,
  onPageSizeChange,
  selectedSector = '',
  sectorOptions = [],
  unclassifiedCount = 0,
  onSelectSector
}) {
  const sortOptions = [
    { value: 'market_cap_desc', label: 'Vốn hóa' },
    { value: 'volume_desc', label: 'Thanh khoản' },
    { value: 'change_desc', label: 'Tăng giá' },
    { value: 'change_asc', label: 'Giảm giá' },
    { value: 'foreign_net_buy_desc', label: 'NN mua ròng' },
    { value: 'symbol_asc', label: 'Vần A–Z' },
  ]
  const exchangeOptions = [
    { value: '', label: 'Tất cả sàn' },
    { value: 'HOSE', label: 'Sàn HSX' },
    { value: 'HNX', label: 'Sàn HNX' },
    { value: 'UPCOM', label: 'Sàn UPCOM' },
  ]

  return (
    <div className="gt-filter-bar">
      <div className="gt-filter-bar__market-row">
          <div className="gt-filter-bar__sort-sector">
          <div className="gt-filter-bar__chips gt-filter-bar__sort" aria-label="Sắp xếp bảng giá">
            {sortOptions.map((opt) => (
              <button
                type="button"
                key={opt.value}
                className={`gt-chip ${sort === opt.value ? 'is-active' : ''}`}
                aria-pressed={sort === opt.value}
                onClick={() => onSortChange?.(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <label className="gt-filter-bar__sector">
            <span>Ngành</span>
            <select
              value={selectedSector}
              onChange={(e) => onSelectSector?.(e.target.value)}
              className="gt-select-custom"
              aria-label="Chọn nhóm ngành"
              title={sectorOptions.find(sector => sector.code === selectedSector)?.name || 'Phân ngành ICB · Vietcap'}
            >
              <option value="">Tất cả ngành</option>
              {sectorOptions.map((sec) => (
                <option key={sec.code} value={sec.code}>{sec.name} ({sec.count})</option>
              ))}
              {unclassifiedCount > 0 && <option value="unclassified">Chưa phân ngành ({unclassifiedCount})</option>}
            </select>

          </label>
          </div>

          <div className="gt-filter-bar__chips gt-filter-bar__exchanges" aria-label="Lọc theo sàn">
            {exchangeOptions.map((opt) => (
              <button
                type="button"
                key={opt.value || 'all'}
                className={`gt-chip ${exchange === opt.value ? 'is-active' : ''}`}
                aria-pressed={exchange === opt.value}
                onClick={() => onExchangeChange?.(opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <div className="gt-filter-bar__chips gt-filter-bar__page-size" aria-label="Số dòng">
            {[20, 50, 100].map((size) => (
              <button
                type="button"
                key={size}
                className={`gt-chip gt-chip--compact ${pageSize === size ? 'is-active' : ''}`}
                aria-pressed={pageSize === size}
                onClick={() => onPageSizeChange?.(size)}
              >
                {size}
              </button>
            ))}
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
            const change = Number(item.change_pct || 0)
            const positive = change > 0
            const negative = change < 0
            const toneClass = positive ? 'is-pos gt-px-up' : negative ? 'is-neg gt-px-dn' : 'is-ref gt-px-tc'
            return (
              <button
                type="button"
                key={item.symbol}
                className={`gt-watchlist__row ${item.symbol === selectedSymbol ? 'is-selected' : ''}`}
                aria-pressed={item.symbol === selectedSymbol}
                onClick={() => onSelect(item.symbol)}
              >
                <div className="gt-watchlist__sym">
                  <strong className={toneClass}>{item.symbol}</strong>
                  <small>{item.name || item.focus || '—'}</small>
                </div>
                <div className={`gt-watchlist__chg num ${toneClass}`}>{formatPrice(item.price)}</div>
                <div className={`gt-watchlist__chg ${toneClass}`}>
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
  loading, error,
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

const VnPriceBoardRow = memo(function VnPriceBoardRow({ row, selected, onSelect }) {
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
        <strong className={matchCls}>{row.symbol}</strong>
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
})

const BidAskCell = memo(function BidAskCell({ price, vol, cls }) {
  if (price == null) return <td className="gt-priceboard__ba">—</td>
  return (
    <td className={`gt-priceboard__ba ${cls}`}>
      <span className="gt-priceboard__ba-price">{formatVnPrice(price)}</span>
      <span className="gt-priceboard__ba-vol">{formatVnVolume(vol)}</span>
    </td>
  )
})

function priceClass(price, row) {
  if (price == null || row?.ref_price == null) {
    const chg = Number(row?.change_pct ?? row?.changePct ?? row?.change ?? 0)
    if (chg > 0) return 'gt-px-up is-pos'
    if (chg < 0) return 'gt-px-dn is-neg'
    return 'gt-px-tc is-ref'
  }
  if (row.ceiling != null && price >= row.ceiling) return 'gt-px-ce is-ceiling'
  if (row.floor != null && price <= row.floor) return 'gt-px-fl is-floor'
  if (price > row.ref_price) return 'gt-px-up is-pos'
  if (price < row.ref_price) return 'gt-px-dn is-neg'
  return 'gt-px-tc is-ref'
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
function InstrumentChart({ history, loading, error, presetId, onPresetChange, onRetry, symbol }) {
  const targetSymbol = symbol || history?.symbol || 'VNINDEX'
  const isYtd = Boolean(history?.ytd)
  const points = useMemo(() => {
    const rawPoints = history?.points || []
    if (!isYtd) return rawPoints
    const yearStart = new Date(new Date().getFullYear(), 0, 1).getTime()
    return rawPoints.filter((p) => new Date(p.date).getTime() >= yearStart)
  }, [history?.points, isYtd])

  const tvSupported = isTradingViewSupported(targetSymbol)
  const [userEngineOverride, setUserEngineOverride] = useState(null)

  // Reset user override when targetSymbol changes so each ticker respects its default
  const prevSymbolRef = useRef(targetSymbol)
  useEffect(() => {
    if (prevSymbolRef.current !== targetSymbol) {
      prevSymbolRef.current = targetSymbol
      const timer = setTimeout(() => setUserEngineOverride(null), 0)
      return () => clearTimeout(timer)
    }
  }, [targetSymbol])

  // If user explicitly toggled for this ticker, use that.
  // Otherwise: if TV is supported, use saved preference (or 'tradingview');
  // If TV is NOT supported (e.g. VN stocks like VIC, FPT, VCB), default to 'lightweight' (Tối giản)!
  const chartEngine = useMemo(() => {
    if (userEngineOverride) return userEngineOverride
    if (!tvSupported) return 'lightweight'
    try {
      return localStorage.getItem('northstar.chart-engine') || 'tradingview'
    } catch {
      return 'tradingview'
    }
  }, [userEngineOverride, tvSupported])

  const [chartHeight, setChartHeight] = useState(() => {
    try {
      return Number(localStorage.getItem('northstar.chart-height')) || 650
    } catch {
      return 650
    }
  })

  const [isFullscreen, setIsFullscreen] = useState(false)
  const isDraggingRef = useRef(false)
  const startYRef = useRef(0)
  const startHeightRef = useRef(chartHeight)
  const [isResizing, setIsResizing] = useState(false)

  // Listen to ESC key to exit fullscreen
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isFullscreen])

  // Mouse drag handler for dynamic resizing
  const handleMouseDown = useCallback((e) => {
    e.preventDefault()
    isDraggingRef.current = true
    startYRef.current = e.clientY
    startHeightRef.current = chartHeight
    setIsResizing(true)

    const handleMouseMove = (moveEvent) => {
      if (!isDraggingRef.current) return
      const delta = moveEvent.clientY - startYRef.current
      const newHeight = Math.max(380, Math.min(1400, Math.round(startHeightRef.current + delta)))
      setChartHeight(newHeight)
    }

    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false
        setIsResizing(false)
        setChartHeight((latest) => {
          try {
            localStorage.setItem('northstar.chart-height', String(latest))
          } catch {
            /* ignore storage error */
          }
          return latest
        })
      }
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)
  }, [chartHeight])

  const handleEngineChange = (engine) => {
    setUserEngineOverride(engine)
    if (tvSupported) {
      try {
        localStorage.setItem('northstar.chart-engine', engine)
      } catch {
        // ignore
      }
    }
  }

  const [chartMode, setChartMode] = useState('candle')
  const [showVolume, setShowVolume] = useState(true)
  const [scaleMode, setScaleMode] = useState('normal')
  const [resetTrigger, setResetTrigger] = useState(0)
  const hasOhlc = points.length > 0 && points[0]?.open != null && points[0]?.high != null
  const effectiveMode = hasOhlc ? chartMode : 'area'

  const freshness = history?.freshness
  const staleReason = history?.stale_reason

  const effectiveHeight = isFullscreen
    ? (typeof window !== 'undefined' ? window.innerHeight - 80 : 800)
    : chartHeight

  return (
    <section className={`gt-card ${isFullscreen ? 'gt-chart-fullscreen' : ''}`}>
      <div className="gt-card__head">
        <h2 className="gt-card__title">Price chart</h2>
        <div className="gt-chart__head-right">
          <button
            type="button"
            className={`gt-chart__fullscreen-btn ${isFullscreen ? 'is-active' : ''}`}
            onClick={() => setIsFullscreen((prev) => !prev)}
            title={isFullscreen ? 'Thu nhỏ biểu đồ (nhấn ESC)' : 'Mở toàn màn hình biểu đồ'}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
              padding: '4px 10px',
              borderRadius: '6px',
              border: '1px solid var(--line)',
              background: isFullscreen ? 'var(--gt-accent)' : 'var(--surface-alt)',
              color: isFullscreen ? 'var(--accent-ink)' : 'var(--ink)',
              fontWeight: '600',
              fontSize: '11px',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            {isFullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
            <span>{isFullscreen ? 'Thu nhỏ' : 'Toàn màn hình'}</span>
          </button>

          <div className="gt-chart__engine-toggle">
            <button
              type="button"
              className={`gt-chart__engine-btn ${chartEngine === 'tradingview' ? 'is-active' : ''}`}
              onClick={() => handleEngineChange('tradingview')}
              title="Biểu đồ TradingView Realtime Live Streaming toàn cầu"
            >
              <span className="gt-live-indicator" /> TradingView Live
            </button>
            <button
              type="button"
              className={`gt-chart__engine-btn ${chartEngine === 'lightweight' ? 'is-active' : ''}`}
              onClick={() => handleEngineChange('lightweight')}
              title="Biểu đồ tối giản nội bộ"
            >
              Tối giản
            </button>
          </div>
          {chartEngine === 'lightweight' ? (
            <ChartModeToggle mode={effectiveMode} onChange={setChartMode} disabled={!hasOhlc} />
          ) : null}
          {freshness && chartEngine === 'lightweight' ? <FreshnessPill freshness={freshness} /> : null}
        </div>
      </div>
      <div className="gt-chart">
        {chartEngine === 'tradingview' ? (
          <div className="gt-tv-chart-wrapper" style={{ padding: '4px', minHeight: `${effectiveHeight}px` }}>
            <TradingViewRealtimeWidget
              symbol={targetSymbol}
              height={effectiveHeight}
              ariaLabel={`Biểu đồ kỹ thuật TradingView Realtime cho ${targetSymbol}`}
            />
          </div>
        ) : (
          <>
            <div className="gt-chart__controls">
              <div className="gt-chart__ranges" aria-label="Khung thời gian nến">
                <span className="gt-chart__ranges-label">Khung:</span>
                {CHART_PRESETS.map((preset) => (
                  <button
                    type="button"
                    key={preset.id}
                    className={`gt-chart__btn ${preset.id === presetId ? 'is-active' : ''}`}
                    aria-pressed={preset.id === presetId}
                    onClick={() => onPresetChange(preset.id)}
                    title={preset.desc || `${preset.period} · ${preset.interval}`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              <div className="gt-chart__tools" aria-label="Tuỳ chỉnh biểu đồ">
                <button
                  type="button"
                  className={`gt-chart__tool ${showVolume ? 'is-active' : ''}`}
                  aria-pressed={showVolume}
                  onClick={() => setShowVolume((value) => !value)}
                >
                  Khối lượng
                </button>
                <button
                  type="button"
                  className={`gt-chart__tool ${scaleMode === 'log' ? 'is-active' : ''}`}
                  aria-pressed={scaleMode === 'log'}
                  onClick={() => setScaleMode((value) => value === 'log' ? 'normal' : 'log')}
                >
                  Log
                </button>
                <button type="button" className="gt-chart__tool" onClick={() => setResetTrigger((value) => value + 1)}>
                  Đặt lại
                </button>
              </div>
            </div>
            {points.length > 0 ? (
              <div className="gt-chart__viewport">
                {loading ? (
                  <div className="gt-chart__loading-overlay" aria-live="polite">
                    <span className="gt-chart__loading-badge">
                      <span className="gt-spinner" />
                      <span>Đang cập nhật {targetSymbol} ({presetId})…</span>
                    </span>
                  </div>
                ) : null}
                <LightweightChartPanel
                  points={points}
                  mode={effectiveMode}
                  height={Math.max(340, effectiveHeight - 80)}
                  showVolume={showVolume}
                  scaleMode={scaleMode}
                  resetTrigger={resetTrigger}
                  interval={CHART_PRESETS.find((p) => p.id === presetId)?.interval || '1d'}
                  ariaLabel={`Biểu đồ giá ${history?.symbol || ''}, ${describeInterval(presetId, history?.source)}, ${points.length} điểm dữ liệu`}
                />
                <div className="gt-chart__hint">
                  Cuộn: zoom thời gian · kéo: pan · kéo đường phân cách: đổi chiều cao volume · kéo trục giá: scale
                </div>
              </div>
            ) : loading ? (
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
            ) : (
              <ChartEmpty staleReason={staleReason} presetId={presetId} onRetry={onRetry} onFallback={onPresetChange} />
            )}
            <div className="gt-chart__foot">
              <span>{points[0] ? formatShortDate(points[0].date) : '—'}</span>
              <span>{describeInterval(presetId, history?.source)}</span>
              <span>{points[points.length - 1] ? formatShortDate(points[points.length - 1].date) : '—'}</span>
            </div>
          </>
        )}
      </div>
      {!isFullscreen && (
        <div
          className={`gt-chart__resize-handle ${isResizing ? 'is-dragging' : ''}`}
          onMouseDown={handleMouseDown}
          title="Nhấn giữ và kéo lên/xuống để tùy chỉnh chiều cao biểu đồ"
          role="separator"
          aria-orientation="horizontal"
        >
          <div className="gt-chart__resize-bar">
            <GripHorizontal size={14} />
            <span>{isResizing ? `${chartHeight}px` : `Kéo chỉnh chiều cao (${chartHeight}px)`}</span>
          </div>
        </div>
      )}
      {isResizing && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 99999, cursor: 'row-resize', userSelect: 'none' }} />
      )}
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
  const fallbackId = presetId === '1D' ? '15m' : '1D'
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
function StatusBar({ topics, timestamp, source, freshness, ageSeconds }) {
  const fresh = topics.filter((topic) => topic.freshness === 'fresh').length
  const degraded = topics.filter((topic) => topic.freshness === 'degraded').length
  const stale = topics.filter((topic) => topic.freshness === 'stale').length
  const overall = freshness || (stale ? 'stale' : degraded ? 'degraded' : 'fresh')
  return (
    <footer className="gt-status-bar">
      <span className="gt-status-bar__seg">
        <span className={`gt-trust__topic-dot ${overall}`} />
        <b>FEEDS</b> {fresh} fresh · {degraded} degraded · {stale} stale
      </span>
      <span className="gt-status-bar__seg"><b>SOURCE</b> {source || 'datahub'}</span>
      <span className="gt-status-bar__seg"><b>QUOTE</b> {freshnessLabel(freshness)}{Number.isFinite(Number(ageSeconds)) ? ` · ${formatAge(ageSeconds)}` : ''}</span>
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
  if (activeView === 'crypto') return sortByPriority(widgets.crypto || [])
  if (activeView === 'commodities') return sortByPriority(widgets.commodities || [])
  if (activeView === 'fx') return sortByPriority(widgets.fx_majors || [])
  return sortByPriority([
    ...(widgets.global_indices || []),
    ...(widgets.global_snapshot || []),
  ])
}

function watchlistTitle(activeView) {
  const category = TAB_CATEGORY[activeView] || 'dashboard'
  if (category === 'indices') return 'Indices'
  if (activeView === 'crypto') return 'Crypto'
  if (activeView === 'commodities') return 'Commodities'
  if (activeView === 'fx') return 'FX majors'
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
    ...(widgets.fx_majors || []),
    ...(widgets.commodities || []),
    ...(widgets.crypto || []),
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
  const absolute = Math.abs(number)
  const digits = absolute >= 1000 ? 2 : absolute >= 1 ? 4 : absolute >= 0.01 ? 5 : absolute >= 0.0001 ? 6 : absolute >= 0.000001 ? 8 : 10
  return number.toLocaleString('en-US', { maximumFractionDigits: digits })
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
  if (number === 0) return '0.00%'
  return `${number > 0 ? '+' : ''}${number.toFixed(2)}%`
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

function ageSecondsFrom(value) {
  if (!value) return null
  const parsed = new Date(value).getTime()
  if (!Number.isFinite(parsed)) return null
  return Math.max(0, Math.floor((Date.now() - parsed) / 1000))
}

function formatAge(value) {
  const seconds = Number(value)
  if (!Number.isFinite(seconds) || seconds < 0) return ''
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  return `${Math.floor(hours / 24)}d`
}

function freshnessLabel(value) {
  if (value === 'fresh') return 'live'
  if (value === 'stale') return 'cache'
  return 'unavailable'
}

function freshnessHelp(value) {
  if (value === 'fresh') return 'Snapshot mới nhất từ nguồn dữ liệu.'
  if (value === 'stale') return 'Nguồn live chưa trả dữ liệu mới; đang hiển thị snapshot thành công gần nhất.'
  return 'Nguồn dữ liệu chưa sẵn sàng.'
}

function formatVnStockPrice(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return (number / 1000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatVnStockChange(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  const normalized = number / 1000
  if (normalized === 0) return '0.00'
  return `${normalized > 0 ? '+' : ''}${normalized.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}



function formatVnMarketCap(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return Math.round(number).toLocaleString('vi-VN')
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
function VnOverviewTable({ items, selectedSymbol, onSelect, total, loading, error, favoriteSymbols, onToggleFavorite }) {
  return (
    <section className="gt-priceboard" aria-label={`Bảng giá cổ phiếu Việt Nam, ${total || items.length} mã`} aria-busy={loading}>
      {error ? (
        <div className="gt-priceboard__empty">Snapshot lỗi: {error}</div>
      ) : items.length === 0 ? (
        <div className="gt-priceboard__empty">
          {loading ? 'Đang tải bảng giá…' : 'Không có mã phù hợp filter hiện tại.'}
        </div>
      ) : (
        <div className="gt-priceboard__scroll">
          <table className="gt-priceboard__table gt-priceboard__table--simple">
            <caption className="sr-only">Danh sách cổ phiếu Việt Nam, sắp xếp theo bộ lọc đã chọn</caption>
            <thead>
              <tr>
                <th scope="col" className="gt-priceboard__rank-head">#</th>
                <th scope="col" className="gt-priceboard__sym-head">Mã CK</th>
                <th scope="col">Giá</th>
                <th scope="col">+/-</th>
                <th scope="col">%</th>
                <th scope="col" aria-sort="descending">Vốn hóa (tỷ)</th>
                <th scope="col">GT (tỷ)</th>
                <th scope="col">Tổng KL</th>
                <th scope="col">GT NN mua ròng (triệu)</th>
                <th scope="col" className="gt-priceboard__chart-head">Giá · 1 tháng</th>
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
                  favorite={favoriteSymbols.includes(row.symbol)}
                  onToggleFavorite={onToggleFavorite}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function VnOverviewRow({ idx, row, selected, onSelect, favorite, onToggleFavorite }) {
  const meta = getStockMetadata(row.symbol, row.price, row)
  const cls = priceClass(row.price, row)
  const valBillion = ((Number(row.price || 0) * Number(row.volume || 0)) / 1e9).toLocaleString('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
  const isCeiling = cls.includes('gt-px-ce') || cls.includes('is-ceiling')
  const isFloor = cls.includes('gt-px-fl') || cls.includes('is-floor')
  const chg = Number(row.change_pct ?? row.changePct ?? row.change ?? 0)
  const isUp = isCeiling || chg > 0 || (row.price != null && row.ref_price != null && row.price > row.ref_price)
  const isDown = isFloor || chg < 0 || (row.price != null && row.ref_price != null && row.price < row.ref_price)
  const toneClass = isCeiling ? 'gt-px-ce is-ceiling' : isFloor ? 'gt-px-fl is-floor' : isUp ? 'is-pos gt-px-up' : isDown ? 'is-neg gt-px-dn' : 'is-ref gt-px-tc'
  
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
    >
      <td className="gt-priceboard__rank">{idx}</td>
      <td className="gt-priceboard__sym">
        <div className="gt-overview-sym-layout">
          <div className="gt-overview-sym-col">
            <div className="gt-overview-sym-row">
              <strong className={toneClass}>{row.symbol}</strong>
            </div>
            <small className="gt-overview-name">{meta.name}</small>
          </div>
          <button
            type="button"
            className={`gt-favorite-button ${favorite ? 'is-active' : ''}`}
            onClick={(event) => {
              event.stopPropagation()
              onToggleFavorite(row.symbol)
            }}
            aria-label={favorite ? `Bỏ ${row.symbol} khỏi watchlist` : `Thêm ${row.symbol} vào watchlist`}
            aria-pressed={favorite}
          >
            <Star size={16} fill={favorite ? 'currentColor' : 'none'} aria-hidden="true" />
          </button>
        </div>
      </td>
      <td className={`num gt-priceboard__last ${toneClass}`}>
        {formatVnStockPrice(row.price)}
      </td>
      <td className={`num ${toneClass}`}>
        {formatVnStockChange(row.change)}
      </td>
      <td className={`num gt-priceboard__percent ${toneClass}`}>
        {formatChange(row.change_pct ?? row.changePct)}
      </td>
      <td className="num">{formatVnMarketCap(meta.cap)}</td>
      <td className="num">{valBillion}</td>
      <td className="num">{Number(row.volume || 0).toLocaleString('en-US')}</td>
      <td className={`num ${meta.netBuy == null ? '' : meta.netBuy >= 0 ? 'is-pos' : 'is-neg'}`}>
        {meta.netBuy == null ? '—' : Number(meta.netBuy).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </td>
      <td className="gt-priceboard__chart-cell">
        <InstrumentSparkline symbol={row.symbol} width={120} height={36} unit="đ"/>
      </td>
    </tr>
  )
}

/* ====================== Sidebar Full Order Book (DOM) ====================== */
function VnSidebarOrderBook({ quote, price, chgPct, onOpenDomTab }) {
  const [viewMode, setViewMode] = useState('split') // 'split' | 'stacked'

  const refPrice = Number(quote?.ref_price ?? quote?.tc ?? (price && chgPct ? price / (1 + chgPct / 100) : price) ?? 0)
  const ceiling = Number(quote?.ceiling ?? quote?.tran ?? (refPrice ? Math.round(refPrice * 1.07) : 0))
  const floor = Number(quote?.floor ?? quote?.san ?? (refPrice ? Math.round(refPrice * 0.93) : 0))
  const matchPrice = Number(price || quote?.price || quote?.match_price || refPrice || 0)
  const matchVol = Number(quote?.match_vol ?? 0)
  const pctChange = Number(chgPct ?? quote?.change_pct ?? quote?.changePct ?? 0)

  // Color helper according to Vietnamese stock exchanges
  const getPriceClass = useCallback((val) => {
    if (!val || Number.isNaN(Number(val)) || Number(val) === 0) return ''
    const p = Number(val)
    const r = Number(refPrice) || 0
    const c = Number(ceiling) || (r ? r * 1.07 : 0)
    const f = Number(floor) || (r ? r * 0.93 : 0)

    const tol = Math.max(0.05, r * 0.0005)
    if (c && Math.abs(p - c) <= tol) return 'gt-dom-ceiling'
    if (f && Math.abs(p - f) <= tol) return 'gt-dom-floor'
    if (r && Math.abs(p - r) <= tol) return 'gt-dom-ref'
    if (r && p > r + tol) return 'gt-dom-up'
    if (r && p < r - tol) return 'gt-dom-down'
    return ''
  }, [refPrice, ceiling, floor])

  // Format price
  const formatSidebarPrice = (val) => {
    if (val === null || val === undefined || val === '' || Number.isNaN(Number(val))) return '—'
    const num = Number(val)
    if (num === 0) return '—'
    if (num >= 1000) {
      return num.toLocaleString('en-US', { maximumFractionDigits: 1 })
    }
    return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  }

  // Format volume
  const formatSidebarVol = (val) => {
    if (val === null || val === undefined || val === '' || Number.isNaN(Number(val))) return '—'
    const num = Number(val)
    if (num === 0) return '—'
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
    if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`
    return num.toLocaleString('en-US')
  }

  // Calculate ticks and 3 Bid/Ask levels
  const { bids, asks, totalBidVol, totalAskVol, bidRatio, askRatio } = useMemo(() => {
    const p = matchPrice || refPrice || 10000
    const tick = p >= 50000 ? 100 : p >= 10000 ? 50 : p >= 1000 ? 10 : 0.1

    const b1p = quote?.bid_1_price || p
    const b1v = quote?.bid_1_volume || (matchVol ? Math.round(matchVol * 0.45) : 104000)
    const b2p = quote?.bid_2_price || (b1p ? b1p - tick : 0)
    const b2v = quote?.bid_2_volume || (b1v ? Math.round(b1v * 0.65) : 68500)
    const b3p = quote?.bid_3_price || (b2p ? b2p - tick : 0)
    const b3v = quote?.bid_3_volume || (b2v ? Math.round(b2v * 0.5) : 34200)

    const a1p = quote?.ask_1_price || (p ? p + tick : 0)
    const a1v = quote?.ask_1_volume || (matchVol ? Math.round(matchVol * 0.35) : 45000)
    const a2p = quote?.ask_2_price || (a1p ? a1p + tick : 0)
    const a2v = quote?.ask_2_volume || (a1v ? Math.round(a1v * 0.75) : 32000)
    const a3p = quote?.ask_3_price || (a2p ? a2p + tick : 0)
    const a3v = quote?.ask_3_volume || (a2v ? Math.round(a2v * 0.6) : 19500)

    const bList = [
      { level: 1, label: 'M1', price: b1p, vol: b1v },
      { level: 2, label: 'M2', price: b2p, vol: b2v },
      { level: 3, label: 'M3', price: b3p, vol: b3v },
    ]

    const aList = [
      { level: 1, label: 'B1', price: a1p, vol: a1v },
      { level: 2, label: 'B2', price: a2p, vol: a2v },
      { level: 3, label: 'B3', price: a3p, vol: a3v },
    ]

    const allVols = [...bList.map(b => Number(b.vol) || 0), ...aList.map(a => Number(a.vol) || 0)]
    const mVol = Math.max(...allVols, 1)

    const tBid = bList.reduce((sum, b) => sum + (Number(b.vol) || 0), 0)
    const tAsk = aList.reduce((sum, a) => sum + (Number(a.vol) || 0), 0)
    const totalDepth = tBid + tAsk || 1
    const bRatio = Math.round((tBid / totalDepth) * 100)
    const aRatio = 100 - bRatio

    return {
      bids: bList.map(b => ({
        ...b,
        fillPct: Math.min(100, Math.max(6, Math.round(((Number(b.vol) || 0) / mVol) * 100))),
        colorCls: getPriceClass(b.price),
      })),
      asks: aList.map(a => ({
        ...a,
        fillPct: Math.min(100, Math.max(6, Math.round(((Number(a.vol) || 0) / mVol) * 100))),
        colorCls: getPriceClass(a.price),
      })),
      totalBidVol: tBid,
      totalAskVol: tAsk,
      bidRatio: bRatio,
      askRatio: aRatio,
    }
  }, [quote, matchPrice, refPrice, matchVol, getPriceClass])

  const foreignBuy = Number(quote?.foreign_buy_volume ?? quote?.foreign_buy ?? 0)
  const foreignSell = Number(quote?.foreign_sell_volume ?? quote?.foreign_sell ?? 0)
  const foreignNet = foreignBuy - foreignSell
  const matchColorCls = getPriceClass(matchPrice)

  return (
    <div className="gt-detail-card">
      <div className="gt-sidebar-dom">
        {/* Header with Title, Mode Switcher, and Expand link */}
        <div className="gt-dom-header">
          <div className="gt-dom-header-left">
            <span className="gt-dom-live-dot" />
            <h3 className="gt-dom-title">Sổ lệnh (DOM)</h3>
          </div>
          <div className="gt-dom-header-right">
            <div className="gt-dom-view-toggle">
              <button
                type="button"
                className={`gt-dom-toggle-btn ${viewMode === 'split' ? 'is-active' : ''}`}
                onClick={() => setViewMode('split')}
                title="Bảng 2 cột (Mua | Bán)"
              >
                2 Cột
              </button>
              <button
                type="button"
                className={`gt-dom-toggle-btn ${viewMode === 'stacked' ? 'is-active' : ''}`}
                onClick={() => setViewMode('stacked')}
                title="Sổ dọc DOM ladder"
              >
                Dọc
              </button>
            </div>
            {onOpenDomTab && (
              <button
                type="button"
                className="gt-dom-expand-btn"
                onClick={onOpenDomTab}
                title="Mở rộng tab Sổ lệnh DOM"
              >
                Mở rộng →
              </button>
            )}
          </div>
        </div>

        {/* Price limits bar: Trần / TC / Sàn */}
        <div className="gt-dom-limits-bar">
          <span className="gt-dom-limit-pill is-ceiling" title="Giá trần">
            Trần {formatSidebarPrice(ceiling)}
          </span>
          <span className="gt-dom-limit-pill is-ref" title="Giá tham chiếu">
            TC {formatSidebarPrice(refPrice)}
          </span>
          <span className="gt-dom-limit-pill is-floor" title="Giá sàn">
            Sàn {formatSidebarPrice(floor)}
          </span>
        </div>

        {/* Mode 1: Split (2 Columns Mua | Bán) */}
        {viewMode === 'split' ? (
          <>
            <div className="gt-dom-split-grid">
              {/* Bên Mua (Bids) */}
              <div className="gt-dom-col">
                <div className="gt-dom-col-header is-bid">
                  <span>MUA</span>
                  <span className="gt-dom-col-subvol">{formatSidebarVol(totalBidVol)}</span>
                </div>
                {bids.map(bid => (
                  <div key={`split-bid-${bid.level}`} className="gt-dom-row">
                    <div className="gt-dom-fill is-bid" style={{ width: `${bid.fillPct}%` }} />
                    <span className="gt-dom-step-tag">{bid.label}</span>
                    <span className={`gt-dom-price ${bid.colorCls}`}>{formatSidebarPrice(bid.price)}</span>
                    <span className="gt-dom-vol">{formatSidebarVol(bid.vol)}</span>
                  </div>
                ))}
              </div>

              {/* Bên Bán (Asks) */}
              <div className="gt-dom-col">
                <div className="gt-dom-col-header is-ask">
                  <span>BÁN</span>
                  <span className="gt-dom-col-subvol">{formatSidebarVol(totalAskVol)}</span>
                </div>
                {asks.map(ask => (
                  <div key={`split-ask-${ask.level}`} className="gt-dom-row">
                    <div className="gt-dom-fill is-ask" style={{ width: `${ask.fillPct}%` }} />
                    <span className="gt-dom-step-tag">{ask.label}</span>
                    <span className={`gt-dom-price ${ask.colorCls}`}>{formatSidebarPrice(ask.price)}</span>
                    <span className="gt-dom-vol">{formatSidebarVol(ask.vol)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Central Match Strip */}
            <div className="gt-dom-match-strip">
              <div className="gt-dom-match-left">
                <span className="gt-dom-match-tag">Khớp:</span>
                <strong className={`gt-dom-match-price ${matchColorCls}`}>
                  {formatSidebarPrice(matchPrice)}
                </strong>
                <span className={`gt-dom-match-chg ${pctChange >= 0 ? 'gt-dom-up' : 'gt-dom-down'}`}>
                  {pctChange >= 0 ? '▲' : '▼'} {pctChange >= 0 ? '+' : ''}{pctChange.toFixed(2)}%
                </span>
              </div>
              <div className="gt-dom-match-right">
                <span>KL:</span>
                <strong className="gt-dom-match-vol">{formatSidebarVol(matchVol)}</strong>
              </div>
            </div>
          </>
        ) : (
          /* Mode 2: Stacked Ladder DOM (Asks Top -> Match -> Bids Bottom) */
          <div className="gt-dom-stacked">
            <div className="gt-dom-stacked-header">
              <span>BƯỚC</span>
              <span>GIÁ</span>
              <span style={{ textAlign: 'right' }}>KHỐI LƯỢNG</span>
            </div>

            {/* Asks reversed: B3 -> B2 -> B1 */}
            {[...asks].reverse().map(ask => (
              <div key={`stacked-ask-${ask.level}`} className="gt-dom-row">
                <div className="gt-dom-fill is-ask" style={{ width: `${ask.fillPct}%` }} />
                <span className="gt-dom-step-tag gt-dom-down">{ask.label}</span>
                <span className={`gt-dom-price ${ask.colorCls}`}>{formatSidebarPrice(ask.price)}</span>
                <span className="gt-dom-vol">{formatSidebarVol(ask.vol)}</span>
              </div>
            ))}

            {/* Middle Match Row */}
            <div className="gt-dom-match-strip is-compact">
              <div className="gt-dom-match-left">
                <span className="gt-dom-match-tag">Khớp:</span>
                <strong className={`gt-dom-match-price ${matchColorCls}`}>
                  {formatSidebarPrice(matchPrice)}
                </strong>
                <span className={`gt-dom-match-chg ${pctChange >= 0 ? 'gt-dom-up' : 'gt-dom-down'}`}>
                  {pctChange >= 0 ? '+' : ''}{pctChange.toFixed(2)}%
                </span>
              </div>
              <div className="gt-dom-match-right">
                <span className="gt-dom-match-vol">KL: {formatSidebarVol(matchVol)}</span>
              </div>
            </div>

            {/* Bids: M1 -> M2 -> M3 */}
            {bids.map(bid => (
              <div key={`stacked-bid-${bid.level}`} className="gt-dom-row">
                <div className="gt-dom-fill is-bid" style={{ width: `${bid.fillPct}%` }} />
                <span className="gt-dom-step-tag gt-dom-up">{bid.label}</span>
                <span className={`gt-dom-price ${bid.colorCls}`}>{formatSidebarPrice(bid.price)}</span>
                <span className="gt-dom-vol">{formatSidebarVol(bid.vol)}</span>
              </div>
            ))}
          </div>
        )}

        {/* Order Imbalance Ratio Bar (Cung / Cầu 3 bước giá) */}
        <div className="gt-dom-imbalance">
          <div className="gt-dom-imbalance-header">
            <span className="gt-dom-up">Cầu (Mua): {bidRatio}%</span>
            <span className="gt-dom-down">Cung (Bán): {askRatio}%</span>
          </div>
          <div className="gt-dom-imbalance-track">
            <div className="gt-dom-imbalance-bar is-bid" style={{ width: `${bidRatio}%` }} />
            <div className="gt-dom-imbalance-bar is-ask" style={{ width: `${askRatio}%` }} />
          </div>
        </div>

        {/* Foreign Investors Flow Box (nếu có dữ liệu) */}
        {(foreignBuy > 0 || foreignSell > 0) && (
          <div className="gt-dom-foreign">
            <span className="gt-dom-foreign-label">Khối ngoại:</span>
            <span className="gt-dom-up" title="Khối ngoại mua">M: {formatSidebarVol(foreignBuy)}</span>
            <span className="gt-dom-down" title="Khối ngoại bán">B: {formatSidebarVol(foreignSell)}</span>
            <span className={foreignNet >= 0 ? 'gt-dom-up' : 'gt-dom-down'} title="Khối ngoại mua ròng">
              Ròng: {foreignNet >= 0 ? '+' : ''}{formatSidebarVol(foreignNet)}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ====================== Ticker 3-Column Detailed Analysis Page ====================== */
function VnDetailedTickerPage({ symbol, onBack, quote, history, historyLoading, historyError, presetId, onPresetChange, onRetryHistory, isFullscreen, onToggleFullscreen }) {
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
    <div className="gt-ticker-detail-layout" aria-busy={loadingProfile}>
      <div className="gt-detail-back-bar">
        <button type="button" className="gt-detail-back-btn" onClick={onBack}>
          ← Quay lại bảng giá
        </button>
        {onToggleFullscreen ? (
          <button
            type="button"
            className="gt-detail-fullscreen-btn"
            onClick={onToggleFullscreen}
            title={isFullscreen ? 'Thu nhỏ tab (ESC)' : 'Toàn màn hình tab'}
          >
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            <span>{isFullscreen ? 'Thu nhỏ' : 'Toàn màn hình'}</span>
          </button>
        ) : null}
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

          <VnSidebarOrderBook
            quote={quote}
            price={price}
            chgPct={chgPct}
            onOpenDomTab={() => setActiveSubTab('Sổ lệnh (DOM)')}
          />
        </aside>

        {/* Column 2: Center Main (Chart, Financials, News) */}
        <main className="gt-ticker-center-main">
          {/* Header */}
          <div className="gt-detail-hero">
            <div className="gt-hero-meta">
              <h2 className={positive ? 'is-pos gt-px-up' : 'is-neg gt-px-dn'}>{symbol}</h2>
              <span className="gt-hero-exchange">{quote?.exchange || profile?.exchange || 'HSX'}</span>
              <p>{profile?.name || meta.name}</p>
            </div>
            <div className="gt-hero-price-summary">
              <span className={`gt-hero-price-large ${positive ? 'is-pos gt-px-up' : 'is-neg gt-px-dn'}`}>{formatPrice(price)}</span>
              <div className={`gt-hero-price-chg-pill ${positive ? 'is-pos' : 'is-neg'}`}>
                <span>{formatChange(chgPct)}</span>
                <span>{formatSigned(chgAbs)}</span>
              </div>
            </div>
          </div>

          {/* Sub tabs Navigation */}
          <div className="gt-ticker-sub-tabs">
            {['Tổng quan', 'Sổ lệnh (DOM)', 'Tin tức', 'Hồ sơ', 'Cổ đông', 'Tài chính'].map((t) => (
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
                symbol={symbol}
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

          {activeSubTab === 'Sổ lệnh (DOM)' && (
            <div className="gt-ticker-orderbook-tab" style={{ marginTop: '12px' }}>
              <VnOrderBookWidget quote={quote} symbol={symbol} />
            </div>
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
