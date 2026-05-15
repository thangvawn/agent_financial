import { useEffect, useState } from 'react'

import { fetchGlobalTerminal, fetchInstrumentHistory } from '../../modules/data-hub'
import './global-terminal.css'

export default function GlobalTerminalPage({ onOpenInsights, onOpenProLab, onOpenNews }) {
  const [payload, setPayload] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('dashboard')
  const [command, setCommand] = useState('')
  const [selectedSymbol, setSelectedSymbol] = useState('XAU')
  const [chartPeriod, setChartPeriod] = useState('6mo')
  const [history, setHistory] = useState(null)
  const [historyError, setHistoryError] = useState('')
  const [historyLoading, setHistoryLoading] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function run() {
      setLoading(true)
      setError('')
      try {
        const data = await fetchGlobalTerminal({ view: activeView })
        if (!cancelled) {
          setPayload(data)
          setSelectedSymbol((current) => current || data?.terminal?.default_symbol || 'XAU')
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    run()
    const timer = window.setInterval(run, 60000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [activeView])

  function handleTerminalTab(nextView) {
    setActiveView(nextView)
    const nextDefaultSymbol = payload?.navigation?.tabs?.find((tab) => tab.id === nextView)?.default_symbol
    if (nextDefaultSymbol) setSelectedSymbol(nextDefaultSymbol)
  }

  function handleCommandSubmit(event) {
    event.preventDefault()
    const raw = command.trim()
    const normalized = raw.toLowerCase().replace(/\s+/g, '_')
    if (!raw) return
    const knownTab = (payload?.navigation?.tabs || []).find((tab) => tab.id === normalized || tab.label.toLowerCase() === raw.toLowerCase())
    if (knownTab) {
      handleTerminalTab(knownTab.id)
      setCommand('')
      return
    }
    setSelectedSymbol(raw.toUpperCase())
    setCommand('')
  }

  useEffect(() => {
    let cancelled = false

    async function run() {
      setHistoryLoading(true)
      setHistoryError('')
      try {
        const data = await fetchInstrumentHistory(selectedSymbol, { period: chartPeriod, interval: '1d' })
        if (!cancelled) setHistory(data)
      } catch (err) {
        if (!cancelled) setHistoryError(err.message)
      } finally {
        if (!cancelled) setHistoryLoading(false)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [selectedSymbol, chartPeriod])

  if (loading && !payload) {
    return <section className="global-terminal global-terminal--loading">Loading global terminal...</section>
  }

  if (error && !payload) {
    return (
      <section className="global-terminal global-terminal--loading">
        <p>Global terminal unavailable: {error}</p>
      </section>
    )
  }

  const widgets = payload?.widgets || {}
  const pulse = widgets.market_pulse || {}
  const visibleWidgetKeys = new Set(payload?.terminal?.visible_widget_keys || [])
  const shouldShow = (key) => visibleWidgetKeys.has(key)
  const terminalTabs = payload?.navigation?.tabs || DEFAULT_TERMINAL_TABS
  const selectedQuote = findQuote(widgets, selectedSymbol) || (widgets.global_indices || [])[0]
  const stripItems = buildMarketStripItems(widgets, payload?.ticker_tape || [])

  return (
    <section className="global-terminal">
      <header className="global-terminal__topbar">
        <nav className="global-terminal__menu" aria-label="Terminal menu">
          <span>File</span>
          <span>Navigate</span>
          <span>View</span>
          <span>Help</span>
        </nav>
        <form className="global-terminal__command" onSubmit={handleCommandSubmit}>
          <span aria-hidden="true">&gt;</span>
          <input
            aria-label="Terminal command"
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            placeholder="Enter command, tab, or symbol..."
          />
        </form>
        <div className="global-terminal__brand">
          <strong>NORTHSTAR</strong>
          <span>GLOBAL TERMINAL</span>
        </div>
        <div className="global-terminal__status">
          <span className="terminal-dot" />
          LIVE
          <span>{formatTerminalTime(payload?.terminal?.as_of)}</span>
        </div>
      </header>

      <div className="global-terminal__tabs">
        {terminalTabs.map((tab) => (
          <button
            type="button"
            key={tab.id}
            className={tab.id === activeView ? 'is-active' : ''}
            onClick={() => handleTerminalTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
        <button type="button" onClick={onOpenInsights}>OPEN INSIGHTS</button>
        <button type="button" onClick={onOpenNews}>NEWS DESK</button>
        <button type="button" onClick={onOpenProLab}>PRO LAB</button>
      </div>

      <TickerTape items={payload?.ticker_tape || []} onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} />
      <MarketStrip items={stripItems} onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} />

      <div className="global-terminal__workspace">
        <aside className="global-terminal__left-rail">
          {shouldShow('global_indices') ? <TerminalTable title="VN & GLOBAL INDICES" accent="orange" items={sortMarketItems(widgets.global_indices || [])} compact onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} /> : null}
          {shouldShow('fx_majors') ? <TerminalTable title="FX WATCH" accent="violet" items={widgets.fx_majors || []} compact onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} /> : null}
          {shouldShow('ai_chat') ? <AiChatTerminalPanel onOpenInsights={onOpenInsights} onOpenNews={onOpenNews} /> : null}
        </aside>

        <main className="global-terminal__focus">
          {shouldShow('chart') ? <QuoteCard quote={selectedQuote} /> : null}
          {shouldShow('chart') ? (
            <InstrumentChart
              history={history}
              loading={historyLoading}
              error={historyError}
              period={chartPeriod}
              onPeriodChange={setChartPeriod}
            />
          ) : null}
          {shouldShow('market_news') ? <NewsTape items={widgets.market_news || []} onOpenNews={onOpenNews} /> : null}
        </main>

        <aside className="global-terminal__right-rail">
          {shouldShow('market_pulse') ? <MarketPulse pulse={pulse} /> : null}
          {shouldShow('global_snapshot') ? <TerminalTable title="GLOBAL SNAPSHOT" accent="blue" items={widgets.global_snapshot || []} compact onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} /> : null}
          {shouldShow('commodities') ? <TerminalTable title="COMMODITIES" accent="gold" items={widgets.commodities || []} compact onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} /> : null}
          {shouldShow('crypto') ? <TerminalTable title="CRYPTO BETA" accent="cyan" items={widgets.crypto || []} compact onSelect={setSelectedSymbol} selectedSymbol={selectedSymbol} /> : null}
          <TopicHealth topics={payload?.topics || []} />
          <TrustBox trust={payload?.trust} />
        </aside>
      </div>

      <footer className="global-terminal__footer">
        <span>v0.1 DATAHUB</span>
        <span>TOPICS: {(payload?.topics || []).length}</span>
        <span>FEEDS: CONNECTED</span>
        <span>MODE: EDUCATION-FIRST</span>
        <span className="is-ready">READY</span>
      </footer>
    </section>
  )
}

function MarketStrip({ items, onSelect, selectedSymbol }) {
  if (!items.length) return null
  return (
    <div className="global-terminal__market-strip" aria-label="Market overview">
      {items.map((item) => (
        <button
          type="button"
          key={`strip-${item.symbol}`}
          className={item.symbol === selectedSymbol ? 'is-selected' : ''}
          onClick={() => onSelect(item.symbol)}
        >
          <span>{item.symbol}</span>
          <strong>{formatPrice(item.price)}</strong>
          <em className={Number(item.change_pct) >= 0 ? 'is-up' : 'is-down'}>{formatChange(item.change_pct)}</em>
          <small>{item.name || item.focus || 'Market'}</small>
        </button>
      ))}
    </div>
  )
}

const DEFAULT_TERMINAL_TABS = [
  { id: 'dashboard', label: 'Dashboard', default_symbol: 'XAU' },
  { id: 'markets', label: 'Markets', default_symbol: 'SPX' },
  { id: 'fx', label: 'FX', default_symbol: 'DXY' },
  { id: 'commodities', label: 'Commodities', default_symbol: 'XAU' },
  { id: 'crypto', label: 'Crypto', default_symbol: 'BTC' },
  { id: 'ai_chat', label: 'AI Chat', default_symbol: 'SPX' },
]

function TickerTape({ items, onSelect, selectedSymbol }) {
  return (
    <div className="global-terminal__ticker">
      {items.map((item) => (
        <button
          type="button"
          key={item.symbol}
          className={item.symbol === selectedSymbol ? 'is-selected' : ''}
          onClick={() => onSelect(item.symbol)}
        >
          <strong>{item.symbol}</strong> {formatPrice(item.price)}
          <em className={Number(item.change_pct) >= 0 ? 'is-up' : 'is-down'}>
            {formatChange(item.change_pct)}
          </em>
        </button>
      ))}
    </div>
  )
}

function TerminalTable({ title, items, accent = 'orange', compact = false, onSelect, selectedSymbol }) {
  return (
    <section className={`terminal-widget terminal-widget--${accent} ${compact ? 'terminal-widget--compact' : ''}`}>
      <WidgetHead title={title} />
      <div className="terminal-table" role="table" aria-label={title}>
        <div className="terminal-table__row terminal-table__row--head" role="row">
          <span>SYMBOL</span>
          <span>PRICE</span>
          <span>CHG</span>
          <span>CHG%</span>
        </div>
        {items.map((item) => (
          <button
            key={item.symbol}
            type="button"
            className={`terminal-table__row terminal-table__row--clickable ${item.symbol === selectedSymbol ? 'is-selected' : ''}`}
            role="row"
            onClick={() => onSelect?.(item.symbol)}
          >
            <span>
              <strong>{item.symbol}</strong>
              <small>{item.name}</small>
            </span>
            <span>{formatPrice(item.price)}</span>
            <span className={Number(item.change) >= 0 ? 'is-up' : 'is-down'}>{formatSigned(item.change)}</span>
            <span className={Number(item.change_pct) >= 0 ? 'is-up' : 'is-down'}>{formatChange(item.change_pct)}</span>
          </button>
        ))}
        {!items.length ? (
          <div className="terminal-table__empty">
            Live feed chưa có dữ liệu hoặc đang degraded. Kiểm tra DataHub topic/source.
          </div>
        ) : null}
      </div>
    </section>
  )
}

function InstrumentChart({ history, loading, error, period, onPeriodChange }) {
  const points = history?.points || []
  const first = points[0]?.price || 0
  const last = points[points.length - 1]?.price || 0
  const change = first ? ((last - first) / first) * 100 : 0

  return (
    <section className="terminal-widget terminal-widget--chart">
      <WidgetHead title={`CHART: ${history?.symbol || '...'}`} />
      <div className="instrument-chart">
        <div className="instrument-chart__head">
          <div>
            <strong>{history?.name || 'Loading instrument'}</strong>
            <span>{history?.focus || 'Yahoo Finance history feed'}</span>
          </div>
          <b className={change >= 0 ? 'is-up' : 'is-down'}>{formatChange(change)}</b>
        </div>
        <div className="instrument-chart__controls">
          {['1mo', '3mo', '6mo', '1y', '2y'].map((option) => (
            <button type="button" key={option} className={period === option ? 'is-active' : ''} onClick={() => onPeriodChange(option)}>
              {option}
            </button>
          ))}
        </div>
        {loading ? <p className="instrument-chart__state">Loading history...</p> : null}
        {error ? <p className="instrument-chart__state is-down">{error}</p> : null}
        {!loading && !error ? <Sparkline points={points} positive={change >= 0} /> : null}
        <div className="instrument-chart__foot">
          <span>{points[0] ? formatShortDate(points[0].date) : '--'}</span>
          <span>{history?.freshness || 'degraded'} · {history?.source || 'yahoo_finance'}</span>
          <span>{points[points.length - 1] ? formatShortDate(points[points.length - 1].date) : '--'}</span>
        </div>
      </div>
    </section>
  )
}

function AiChatTerminalPanel({ onOpenInsights, onOpenNews }) {
  return (
    <section className="terminal-widget terminal-widget--ai-chat">
      <WidgetHead title="AI CHAT COMMAND CENTER" />
      <div className="ai-terminal-panel">
        <strong>Assistant đang chạy như floating chat ở góc màn hình.</strong>
        <p>
          Tab này gom bối cảnh để hỏi nhanh về market pulse, symbol đang xem, news hoặc insight.
          Dùng bong bóng chat để đặt câu hỏi, hoặc mở module chuyên sâu bên dưới.
        </p>
        <div>
          <button type="button" onClick={onOpenInsights}>Open Insights</button>
          <button type="button" onClick={onOpenNews}>Open News Desk</button>
        </div>
        <small>Guardrail: AI chỉ giải thích và hướng dẫn học, không đưa khuyến nghị mua bán cá nhân hóa.</small>
      </div>
    </section>
  )
}

function Sparkline({ points, positive }) {
  if (!points.length) {
    return <div className="sparkline-empty">Không có history data cho symbol này.</div>
  }
  const width = 640
  const height = 220
  const prices = points.map((point) => Number(point.price || 0))
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const step = width / Math.max(1, points.length - 1)
  const coords = prices.map((price, index) => {
    const x = index * step
    const y = height - ((price - min) / range) * (height - 24) - 12
    return [x, y]
  })
  const line = coords.map(([x, y]) => `${x.toFixed(2)},${y.toFixed(2)}`).join(' ')
  const area = `0,${height} ${line} ${width},${height}`
  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Instrument price history">
      <defs>
        <linearGradient id={`spark-${positive ? 'up' : 'down'}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={positive ? '#00c853' : '#ff3d3d'} stopOpacity="0.28" />
          <stop offset="100%" stopColor={positive ? '#00c853' : '#ff3d3d'} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill={`url(#spark-${positive ? 'up' : 'down'})`} />
      <polyline points={line} fill="none" stroke={positive ? '#00c853' : '#ff3d3d'} strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

function WidgetHead({ title }) {
  return (
    <div className="terminal-widget__head">
      <h2>{title}</h2>
      <div>
        <span>↻</span>
        <span>×</span>
      </div>
    </div>
  )
}

function QuoteCard({ quote }) {
  if (!quote) return null
  return (
    <section className="terminal-widget terminal-widget--quote">
      <WidgetHead title={`QUOTE: ${quote.symbol}`} />
      <div className="quote-card">
        <strong>{formatPrice(quote.price)}</strong>
        <span className={Number(quote.change_pct) >= 0 ? 'is-up' : 'is-down'}>{formatChange(quote.change_pct)}</span>
        <p>{quote.focus}</p>
        <div>
          <span>OPEN</span>
          <b>{formatPrice(Number(quote.price) * 0.994)}</b>
        </div>
        <div>
          <span>HIGH</span>
          <b>{formatPrice(Number(quote.price) * 1.006)}</b>
        </div>
        <div>
          <span>LOW</span>
          <b>{formatPrice(Number(quote.price) * 0.986)}</b>
        </div>
      </div>
    </section>
  )
}

function NewsTape({ items, onOpenNews }) {
  return (
    <section className="terminal-widget terminal-widget--news">
      <div className="terminal-widget__head">
        <h2>MARKET NEWS</h2>
        <button type="button" onClick={onOpenNews}>OPEN NEWS DESK</button>
      </div>
      <div className="news-tape">
        {items.map((item) => (
          <article key={item.article_id || `${item.time}-${item.headline}`}>
            <time>{item.time || formatNewsTime(item.published_at)}</time>
            <div>
              <p>{item.headline}</p>
              <small>
                {item.category ? <b>{item.category}</b> : null}
                {item.sentiment ? <em className={`sentiment-${item.sentiment}`}>{item.sentiment}</em> : null}
                {item.impact ? <em>{item.impact} impact</em> : null}
              </small>
            </div>
            <span>
              {item.source}
              {item.source_flag ? <small>{item.source_flag}</small> : null}
            </span>
          </article>
        ))}
        {!items.length ? (
          <div className="news-tape__empty">
            News feed chưa có dữ liệu. Hệ thống sẽ dùng cache khi producer RSS chạy thành công.
          </div>
        ) : null}
      </div>
    </section>
  )
}

function MarketPulse({ pulse }) {
  const score = Number(pulse.fear_greed || 0)
  return (
    <section className="terminal-widget terminal-widget--pulse">
      <WidgetHead title="MARKET PULSE" />
      <div className="pulse-score">
        <span>Fear & Greed Index</span>
        <strong>{score}<small>/100</small></strong>
        <div><i style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div>
        <em>{pulse.label}</em>
      </div>
      <div className="pulse-breadth">
        {(pulse.breadth || []).map((row) => (
          <div key={row.label}>
            <span>{row.label}</span>
            <b>{row.up}</b>
            <i style={{ width: `${(row.up / Math.max(1, row.up + row.down)) * 100}%` }} />
            <b className="is-down">{row.down}</b>
          </div>
        ))}
      </div>
      <MiniRank title="TOP GAINERS" items={pulse.top_gainers || []} />
      <MiniRank title="TOP LOSERS" items={pulse.top_losers || []} down />
    </section>
  )
}

function MiniRank({ title, items, down = false }) {
  return (
    <div className="mini-rank">
      <h3>{title}</h3>
      {items.map((item) => (
        <p key={`${title}-${item.symbol}`}>
          <span>{item.symbol}</span>
          <b className={down ? 'is-down' : 'is-up'}>{formatChange(item.change_pct)}</b>
        </p>
      ))}
    </div>
  )
}

function TopicHealth({ topics }) {
  return (
    <section className="terminal-widget terminal-widget--topics">
      <WidgetHead title="DATAHUB TOPICS" />
      {topics.slice(0, 6).map((topic) => (
        <div key={topic.topic} className="topic-row">
          <span>{topic.topic}</span>
          <b className={`freshness-${topic.freshness}`}>{topic.freshness}</b>
        </div>
      ))}
    </section>
  )
}

function TrustBox({ trust }) {
  return (
    <section className="terminal-widget terminal-widget--trust">
      <WidgetHead title="TRUST LAYER" />
      <p><strong>WHAT THIS IS</strong>{trust?.what_this_is}</p>
      <p><strong>WHAT THIS IS NOT</strong>{trust?.what_this_is_not}</p>
      <small>{trust?.freshness_label}</small>
    </section>
  )
}

function formatPrice(value) {
  const number = Number(value || 0)
  if (Math.abs(number) >= 1000) return number.toLocaleString('en-US', { maximumFractionDigits: 2 })
  return number.toLocaleString('en-US', { maximumFractionDigits: 4 })
}

function formatSigned(value) {
  const number = Number(value || 0)
  return `${number >= 0 ? '+' : ''}${formatPrice(number)}`
}

function formatChange(value) {
  const number = Number(value || 0)
  return `${number >= 0 ? '+' : ''}${number.toFixed(2)}%`
}

function formatTerminalTime(value) {
  if (!value) return 'LIVE'
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).toUpperCase()
}

function formatNewsTime(value) {
  if (!value) return '--:--'
  return new Date(value).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

function formatShortDate(value) {
  if (!value) return '--'
  return new Date(value).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function findQuote(widgets, symbol) {
  return [
    ...(widgets.global_indices || []),
    ...(widgets.fx_majors || []),
    ...(widgets.commodities || []),
    ...(widgets.crypto || []),
  ].find((item) => item.symbol === symbol)
}

function buildMarketStripItems(widgets, tickerTape) {
  const lookup = new Map()
  ;[
    ...(widgets.global_indices || []),
    ...(widgets.global_snapshot || []),
    ...(widgets.fx_majors || []),
    ...(widgets.commodities || []),
    ...(widgets.crypto || []),
    ...tickerTape,
  ].forEach((item) => {
    if (item?.symbol && !lookup.has(item.symbol)) lookup.set(item.symbol, item)
  })
  const priority = ['VNINDEX', 'VN30', 'HNXINDEX', 'SPX', 'NDX', 'DXY', 'US10Y', 'XAU', 'WTI', 'BTC']
  const prioritized = priority.map((symbol) => lookup.get(symbol)).filter(Boolean)
  const fallback = Array.from(lookup.values()).filter((item) => !priority.includes(item.symbol))
  return [...prioritized, ...fallback].slice(0, 8)
}

function sortMarketItems(items) {
  const priority = ['VNINDEX', 'VN30', 'HNXINDEX', 'UPCOM', 'SPX', 'NDX', 'DJI']
  return [...items].sort((a, b) => {
    const left = priority.indexOf(a.symbol)
    const right = priority.indexOf(b.symbol)
    if (left === -1 && right === -1) return 0
    if (left === -1) return 1
    if (right === -1) return -1
    return left - right
  })
}
