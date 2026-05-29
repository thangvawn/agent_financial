import { useEffect, useMemo, useRef, useState } from 'react'

import { fetchGlobalTerminal, fetchInstrumentHistory, fetchVnSnapshot } from '../../modules/data-hub'
import LightweightChartPanel from './LightweightChartPanel'
import './global-terminal.css'

const TAB_CATEGORY = {
  dashboard: 'dashboard',
  markets: 'indices',
  indices: 'indices',
  fx: 'fx',
  commodities: 'commodities',
  crypto: 'crypto',
  vn_stocks: 'vn_stocks',
}

const DEFAULT_TABS = [
  { id: 'dashboard', label: 'Dashboard', default_symbol: 'XAU' },
  { id: 'vn_stocks', label: 'VN Stocks', default_symbol: 'FPT' },
  { id: 'markets', label: 'Indices', default_symbol: 'SPX' },
  { id: 'fx', label: 'FX', default_symbol: 'DXY' },
  { id: 'commodities', label: 'Commodities', default_symbol: 'XAU' },
  { id: 'crypto', label: 'Crypto', default_symbol: 'BTC' },
]

const PRIORITY = ['VNINDEX', 'VN30', 'HNXINDEX', 'SPX', 'NDX', 'DJI', 'DXY', 'US10Y', 'XAU', 'WTI', 'BTC']

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

export default function GlobalTerminalPage({ onOpenInsights, onOpenProLab, onOpenNews }) {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('dashboard')
  const [command, setCommand] = useState('')
  const [selectedSymbol, setSelectedSymbol] = useState('XAU')
  const [presetId, setPresetId] = useState(DEFAULT_PRESET_ID)
  const [history, setHistory] = useState(null)
  const [historyError, setHistoryError] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [refreshTick, setRefreshTick] = useState(0)
  const [vnSnapshot, setVnSnapshot] = useState(null)
  const [vnLoading, setVnLoading] = useState(false)
  const [vnError, setVnError] = useState('')
  const [vnSort, setVnSort] = useState('change_desc')
  const [vnExchange, setVnExchange] = useState('')
  const [vnSearch, setVnSearch] = useState('')
  const terminalRequestSeqRef = useRef(0)
  const historyRequestSeqRef = useRef(0)
  const vnRequestSeqRef = useRef(0)

  useEffect(() => {
    let cancelled = false

    async function run() {
      const requestId = ++terminalRequestSeqRef.current
      setLoading(true)
      setError('')
      try {
        const data = await fetchGlobalTerminal({ view: activeView })
        if (cancelled || requestId !== terminalRequestSeqRef.current) return
        setPayload(data)
        setSelectedSymbol((current) => current || data?.terminal?.default_symbol || 'XAU')
      } catch (err) {
        if (cancelled || requestId !== terminalRequestSeqRef.current) return
        setError(err.message)
      } finally {
        if (!cancelled && requestId === terminalRequestSeqRef.current) setLoading(false)
      }
    }

    run()
    const timer = window.setInterval(run, 60000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [activeView, refreshTick])

  useEffect(() => {
    if (activeView !== 'vn_stocks') return undefined
    let cancelled = false
    async function run() {
      const requestId = ++vnRequestSeqRef.current
      setVnLoading(true)
      setVnError('')
      try {
        const data = await fetchVnSnapshot({ sort: vnSort, exchange: vnExchange, search: vnSearch, limit: 300 })
        if (cancelled || requestId !== vnRequestSeqRef.current) return
        setVnSnapshot(data)
      } catch (err) {
        if (cancelled || requestId !== vnRequestSeqRef.current) return
        setVnError(err.message)
      } finally {
        if (!cancelled && requestId === vnRequestSeqRef.current) setVnLoading(false)
      }
    }
    run()
    const timer = window.setInterval(run, 60000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [activeView, vnSort, vnExchange, vnSearch, refreshTick])

  useEffect(() => {
    let cancelled = false

    async function run() {
      const requestId = ++historyRequestSeqRef.current
      setHistoryLoading(true)
      setHistoryError('')
      try {
        const preset = CHART_PRESETS.find((item) => item.id === presetId) || CHART_PRESETS[4]
        const data = await fetchInstrumentHistory(selectedSymbol, { period: preset.period, interval: preset.interval })
        if (cancelled || requestId !== historyRequestSeqRef.current) return
        setHistory({ ...data, presetId: preset.id, ytd: Boolean(preset.ytd) })
      } catch (err) {
        if (cancelled || requestId !== historyRequestSeqRef.current) return
        setHistoryError(err.message)
      } finally {
        if (!cancelled && requestId === historyRequestSeqRef.current) setHistoryLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [selectedSymbol, presetId])

  function handleTab(nextView) {
    setActiveView(nextView)
    const tabDefault = payload?.navigation?.tabs?.find((tab) => tab.id === nextView)?.default_symbol
    if (tabDefault) setSelectedSymbol(tabDefault)
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
      setSelectedSymbol(raw.toUpperCase())
    }
    setCommand('')
  }

  if (loading && !payload) {
    return (
      <section className="global-terminal global-terminal--loading">
        <p>Loading global terminal…</p>
      </section>
    )
  }

  if (error && !payload) {
    return (
      <section className="global-terminal global-terminal--error">
        <p>Global terminal unavailable: {error}</p>
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
  const isVnTab = activeView === 'vn_stocks'
  const watchlist = isVnTab
    ? (vnSnapshot?.items || []).map((item) => ({
        symbol: item.symbol,
        name: item.name,
        price: item.price,
        change_pct: item.change_pct,
        change: item.change,
        focus: item.exchange ? `${item.exchange}${item.name ? ` · ${item.name}` : ''}` : item.name,
        volume: item.volume,
      }))
    : buildWatchlist(widgets, activeView)
  const tickerItems = payload?.ticker_tape || []
  const selectedQuote = isVnTab
    ? (vnSnapshot?.items || []).find((item) => item.symbol === selectedSymbol)
    : findQuote(widgets, selectedSymbol)

  return (
    <section className="global-terminal">
      <TerminalHeader
        command={command}
        onCommandChange={setCommand}
        onCommandSubmit={handleCommandSubmit}
        timestamp={payload?.terminal?.as_of}
      />

      <TerminalTabs
        tabs={tabs}
        active={activeView}
        onSelect={handleTab}
        onOpenInsights={onOpenInsights}
        onOpenNews={onOpenNews}
        onOpenProLab={onOpenProLab}
      />

      <TickerTape items={tickerItems} selectedSymbol={selectedSymbol} onSelect={setSelectedSymbol} />

      {isVnTab ? (
        <div className="gt-vn-workspace">
          <VnPriceBoard
            items={vnSnapshot?.items || []}
            selectedSymbol={selectedSymbol}
            onSelect={setSelectedSymbol}
            sort={vnSort}
            onSortChange={setVnSort}
            exchange={vnExchange}
            onExchangeChange={setVnExchange}
            search={vnSearch}
            onSearchChange={setVnSearch}
            total={vnSnapshot?.total}
            loading={vnLoading}
            error={vnError}
            freshness={vnSnapshot?.freshness}
            asOf={vnSnapshot?.as_of}
          />
          <div className="gt-vn-detail">
            <InstrumentHero quote={selectedQuote} history={history} symbol={selectedSymbol} />
            <InstrumentChart
              history={history}
              loading={historyLoading}
              error={historyError}
              presetId={presetId}
              onPresetChange={setPresetId}
              onRetry={() => setRefreshTick((n) => n + 1)}
            />
          </div>
        </div>
      ) : (
        <div className="gt-workspace">
          <aside className="gt-rail gt-rail--left">
            <Watchlist
              title={watchlistTitle(activeView)}
              items={watchlist}
              selectedSymbol={selectedSymbol}
              onSelect={setSelectedSymbol}
              vnControls={null}
            />
          </aside>

          <main className="gt-main">
            <InstrumentHero quote={selectedQuote} history={history} symbol={selectedSymbol} />
            <InstrumentChart
              history={history}
              loading={historyLoading}
              error={historyError}
              presetId={presetId}
              onPresetChange={setPresetId}
              onRetry={() => setRefreshTick((n) => n + 1)}
            />
            <InstrumentNews items={widgets.market_news || []} onOpenNews={onOpenNews} />
          </main>

          <aside className="gt-rail gt-rail--right">
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

/* ====================== Header ====================== */
function TerminalHeader({ command, onCommandChange, onCommandSubmit, timestamp }) {
  return (
    <header className="gt-header">
      <div className="gt-header__brand">
        <strong>Northstar</strong>
        <span className="gt-header__brand-sep">·</span>
        <span>Global Terminal</span>
      </div>
      <form className="gt-header__search" onSubmit={onCommandSubmit}>
        <span className="gt-header__search-icon" aria-hidden="true">⌕</span>
        <input
          aria-label="Search symbol or command"
          value={command}
          onChange={(event) => onCommandChange(event.target.value)}
          placeholder="Tìm symbol hoặc lệnh… (e.g. XAU, fx)"
        />
        <kbd className="gt-header__search-kbd">⌘K</kbd>
      </form>
      <div className="gt-header__status">
        <span className="gt-header__dot" aria-hidden="true" />
        <span className="gt-header__status-live">LIVE</span>
        <span>{formatTimestamp(timestamp)}</span>
      </div>
    </header>
  )
}

/* ====================== Tabs ====================== */
function TerminalTabs({ tabs, active, onSelect, onOpenInsights, onOpenNews, onOpenProLab }) {
  return (
    <div className="gt-tabs">
      {tabs.map((tab) => (
        <button
          type="button"
          key={tab.id}
          className={`gt-tabs__btn ${tab.id === active ? 'is-active' : ''}`}
          onClick={() => onSelect(tab.id)}
        >
          {tab.label}
        </button>
      ))}
      <div className="gt-tabs__spacer" />
      <button type="button" className="gt-tabs__link" onClick={onOpenInsights}>Insights</button>
      <button type="button" className="gt-tabs__link" onClick={onOpenNews}>News Desk</button>
      <button type="button" className="gt-tabs__link" onClick={onOpenProLab}>Pro Lab</button>
    </div>
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
      <div className="gt-priceboard__bar">
        <input
          className="gt-priceboard__search"
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value.toUpperCase())}
          placeholder="Tìm mã (FPT, VIC, VCB…)"
          aria-label="Tìm ticker VN"
        />
        <div className="gt-priceboard__chips">
          {['', 'HOSE', 'HNX', 'UPCOM'].map((ex) => (
            <button
              type="button"
              key={ex || 'all'}
              className={`gt-vn-controls__chip ${exchange === ex ? 'is-active' : ''}`}
              onClick={() => onExchangeChange(ex)}
            >
              {ex || 'Tất cả'}
            </button>
          ))}
        </div>
        <select
          className="gt-priceboard__sort"
          value={sort}
          onChange={(event) => onSortChange(event.target.value)}
          aria-label="Sắp xếp"
        >
          <option value="change_desc">Tăng nhiều nhất</option>
          <option value="change_asc">Giảm nhiều nhất</option>
          <option value="volume_desc">Volume cao nhất</option>
          <option value="value_desc">Value cao nhất</option>
          <option value="symbol_asc">Tên A→Z</option>
        </select>
        <div className="gt-priceboard__status">
          <span className={`gt-trust__topic-dot ${freshness || 'stale'}`} />
          <span>{loading ? 'Đang tải…' : freshness === 'fresh' ? 'Live' : 'Cache'}</span>
          <span className="gt-priceboard__count">{items.length}{total ? `/${total}` : ''}</span>
          <span>{formatTimestamp(asOf)}</span>
        </div>
      </div>

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
  const rawPoints = history?.points || []
  const isYtd = Boolean(history?.ytd)
  const points = useMemo(() => {
    if (!isYtd) return rawPoints
    const yearStart = new Date(new Date().getFullYear(), 0, 1).getTime()
    return rawPoints.filter((p) => new Date(p.date).getTime() >= yearStart)
  }, [rawPoints, isYtd])

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
              onClick={() => onPresetChange(preset.id)}
              title={`${preset.period} · ${preset.interval}`}
            >
              {preset.label}
            </button>
          ))}
        </div>
        {loading ? (
          <div className="gt-chart__state">Loading history…</div>
        ) : error ? (
          <div className="gt-chart__state is-error">
            <p>{error}</p>
            <button type="button" className="gt-error__retry" onClick={onRetry}>Thử lại</button>
          </div>
        ) : points.length ? (
          <>
            <LightweightChartPanel points={points} mode={effectiveMode} height={340} />
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
        onClick={() => onChange('area')}
        title="Line/area chart"
      >
        Line
      </button>
      <button
        type="button"
        className={`gt-chart__mode-btn ${mode === 'candle' ? 'is-active' : ''}`}
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
  if (category === 'fx') return widgets.fx_majors || []
  if (category === 'commodities') return widgets.commodities || []
  if (category === 'crypto') return widgets.crypto || []
  return sortByPriority([
    ...(widgets.global_indices || []),
    ...(widgets.global_snapshot || []),
    ...(widgets.fx_majors || []),
    ...(widgets.commodities || []),
    ...(widgets.crypto || []),
  ])
}

function watchlistTitle(activeView) {
  const category = TAB_CATEGORY[activeView] || 'dashboard'
  if (category === 'indices') return 'Indices'
  if (category === 'fx') return 'FX majors'
  if (category === 'commodities') return 'Commodities'
  if (category === 'crypto') return 'Crypto'
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
    ...(widgets.fx_majors || []),
    ...(widgets.commodities || []),
    ...(widgets.crypto || []),
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
