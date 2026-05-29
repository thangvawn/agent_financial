import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

import {
  askNewsAnalyst,
  fetchArticleDetail,
  fetchFinnhubMacroDesk,
  fetchNewsFeed,
  saveNewsArticle,
  unsaveNewsArticle,
} from '../../modules/data-hub'
import { getNewsEconomicCalendarEmbedUrl } from './newsEconomicCalendarUrl.js'
import { finnhubCell, formatFinnhubEconTimeCell } from './newsFinnhubCalendarUtils.js'
import './news.css'

// ── Constants ──────────────────────────────────────────────────────────

const CATEGORIES = [
  'all', 'macro', 'markets', 'commodities', 'crypto', 'regulation',
  'geopolitics', 'technology', 'earnings', 'personal_finance', 'risk_alerts',
]
const PRESETS = [
  { id: 'balanced', label: 'Balanced' },
  { id: 'vietnam', label: 'Việt Nam' },
  { id: 'us', label: 'US markets' },
  { id: 'global_macro', label: 'Global macro' },
  { id: 'energy', label: 'Energy' },
  { id: 'crypto', label: 'Crypto' },
]
const REGIONS = [
  { value: '', label: 'All regions' },
  { value: 'VN', label: 'Việt Nam' },
  { value: 'US', label: 'United States' },
  { value: 'global', label: 'Global' },
  { value: 'EU', label: 'Europe' },
  { value: 'Asia', label: 'Asia' },
]
const SOURCE_GROUPS = [
  { value: '', label: 'All sources' },
  { value: 'official', label: 'Official only' },
  { value: 'vn_markets', label: 'VN stocks & finance' },
  { value: 'vn_macro', label: 'VN macro' },
  { value: 'us_markets', label: 'US markets' },
  { value: 'global_macro', label: 'Global macro' },
  { value: 'commodities_energy', label: 'Energy & commodities' },
  { value: 'crypto', label: 'Crypto' },
  { value: 'technology', label: 'Technology' },
]
const TIME_RANGES = [
  { value: 24, label: '24h' },
  { value: 72, label: '3 days' },
  { value: 168, label: '7 days' },
]
const SENTIMENTS = [
  { value: '', label: 'All sentiment' },
  { value: 'positive', label: 'Positive' },
  { value: 'negative', label: 'Negative' },
  { value: 'neutral', label: 'Neutral' },
]
const IMPACT_LEVELS = [
  { value: '', label: 'All impact' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]
const IMPORTANCE_LABELS = [
  { value: '', label: 'All importance' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]
const NEWS_CHAT_EXAMPLES = [
  'Tin Fed hôm nay ảnh hưởng hàng hóa thế nào?',
  'Headline này có đáng lo cho thị trường không?',
  'Tóm tắt các rủi ro chính trong filter hiện tại.',
]
const HEADER_BADGES = [
  { label: 'Source-aware', variant: 'default' },
  { label: 'AI explained', variant: 'default' },
  { label: 'No buy/sell', variant: 'caution' },
  { label: 'Freshness tracked', variant: 'default' },
]

/** Feed list: show a short chunk first; scroll / “Xem thêm” reveals the rest. */
const FEED_LIST_INITIAL = 12
const FEED_LIST_STEP = 12

/** Briefly highlight the pulse panel — used by hero "Market Pulse" / "Xem chi tiết pulse"
 *  buttons so the action feels visible on desktop where the panel is always on screen. */
function flashPulsePanel() {
  if (typeof document === 'undefined') return
  const el = document.getElementById('news-desk-pulse-panel')
  if (!el) return
  el.classList.remove('is-flash')
  // Force reflow so re-adding the class restarts the animation
  void el.offsetWidth
  el.classList.add('is-flash')
  window.setTimeout(() => el.classList.remove('is-flash'), 1400)
}

// ── Main Component ─────────────────────────────────────────────────────

export default function NewsPage({ sessionId, onBack, onOpenGlobalTerminal }) {
  // Feed state
  const [payload, setPayload] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filter state
  const [marketLens, setMarketLens] = useState('vietnam') // 'vietnam' | 'global' | 'cross_impact'
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')
  const [preset, setPreset] = useState('vietnam')
  const [region, setRegion] = useState('VN')
  const [sourceGroup, setSourceGroup] = useState('vn_markets')
  const [timeRangeHours, setTimeRangeHours] = useState(168)
  const [sentiment, setSentiment] = useState('')
  const [impactLevel, setImpactLevel] = useState('')
  const [importance, setImportance] = useState('')

  // Article state
  const [activeArticleId, setActiveArticleId] = useState('')
  const [articleDetail, setArticleDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  // Saved state
  const [savedIds, setSavedIds] = useState(new Set())

  // Chat state
  const [chatOpen, setChatOpen] = useState(false)
  const [chatPrompt, setChatPrompt] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [chatConversationId, setChatConversationId] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')

  // Mobile tab state
  const [mobileTab, setMobileTab] = useState('feed')

  // Handle lens change
  function handleLensChange(lens) {
    setMarketLens(lens)
    if (lens === 'vietnam') {
      setPreset('vietnam')
      setRegion('VN')
      setSourceGroup('vn_markets')
      setCategory('all')
    } else if (lens === 'global') {
      setPreset('global_macro')
      setRegion('global')
      setSourceGroup('global_macro')
      setCategory('all')
    } else if (lens === 'cross_impact') {
      setPreset('balanced')
      setRegion('')
      setSourceGroup('')
      setCategory('all')
    }
  }

  /** Only update mobileTab when the mobile-tabs UI is actually visible (≤1180px). Avoids
   *  desktop clicks (Today brief, Market Pulse hero, etc.) leaving stale state that hides
   *  panels if the user later resizes to mobile. */
  const setMobileTabIfMobile = useCallback((tab) => {
    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 1180px)').matches) {
      setMobileTab(tab)
    }
  }, [])

  /** Reset to 'feed' when leaving the mobile breakpoint, so the next time the user
   *  resizes back down they see the canonical Feed pane. */
  useEffect(() => {
    if (typeof window === 'undefined') return undefined
    const mq = window.matchMedia('(max-width: 1180px)')
    function onChange(e) {
      if (!e.matches) setMobileTab('feed')
    }
    mq.addEventListener?.('change', onChange)
    return () => mq.removeEventListener?.('change', onChange)
  }, [])

  /** Finnhub macro desk (calendar + quotes); server caches to protect rate limits. */
  const [macroDesk, setMacroDesk] = useState(null)

  /** Full economic calendar in overlay iframe */
  const [econCalendarIframeOpen, setEconCalendarIframeOpen] = useState(false)
  const [econCalendarIframeKey, setEconCalendarIframeKey] = useState(0)

  const [feedVisible, setFeedVisible] = useState(FEED_LIST_INITIAL)

  const apiPreset = preset === 'balanced' ? '' : preset
  const feedRef = useRef(null)
  const feedScrollRef = useRef(null)
  const feedSentinelRef = useRef(null)

  // ── Fetch feed ───────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false
    async function run() {
      setLoading(true)
      setError('')
      try {
        const data = await fetchNewsFeed({
          category: category === 'all' ? '' : category,
          q: query,
          limit: 80,
          timeRangeHours,
          region,
          sourceGroup,
          preset: apiPreset,
          sentiment: sentiment || undefined,
          impactLevel: impactLevel || undefined,
          importance: importance || undefined,
        })
        if (!cancelled) {
          setPayload(data)
          setActiveArticleId((cur) => cur || data.articles?.[0]?.article_id || '')
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    const timer = window.setTimeout(run, 250)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [category, query, preset, apiPreset, region, sourceGroup, timeRangeHours, sentiment, impactLevel, importance])

  // ── Fetch article detail ─────────────────────────────────────────────

  useEffect(() => {
    if (!activeArticleId) { setArticleDetail(null); return }
    let cancelled = false
    async function run() {
      setDetailLoading(true)
      try {
        const data = await fetchArticleDetail(activeArticleId)
        if (!cancelled) setArticleDetail(data)
      } catch {
        if (!cancelled) setArticleDetail(null)
      } finally {
        if (!cancelled) setDetailLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [activeArticleId])

  useEffect(() => {
    let cancelled = false
    async function run() {
      try {
        const d = await fetchFinnhubMacroDesk({ force: false, calendarDays: 14, includeQuotes: false })
        if (!cancelled) setMacroDesk(d)
      } catch {
        if (!cancelled) setMacroDesk({ enabled: false, client_error: true })
      }
    }
    run()
    const id = window.setInterval(run, 60_000)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  useEffect(() => {
    setFeedVisible(FEED_LIST_INITIAL)
  }, [category, query, preset, apiPreset, region, sourceGroup, timeRangeHours, sentiment, impactLevel, importance])

  // ── Handlers ─────────────────────────────────────────────────────────

  async function handleRefresh() {
    setLoading(true)
    setError('')
    try {
      const data = await fetchNewsFeed({
        category: category === 'all' ? '' : category,
        q: query, limit: 80, timeRangeHours, region, sourceGroup,
        preset: apiPreset, force: true,
      })
      setPayload(data)
      setFeedVisible(FEED_LIST_INITIAL)
      setActiveArticleId(data.articles?.[0]?.article_id || '')
    } catch (err) { setError(err.message) }
    finally { setLoading(false) }
  }

  function handleResetFilters() {
    setCategory('all'); setQuery(''); setPreset('balanced')
    setRegion(''); setSourceGroup(''); setTimeRangeHours(168)
    setSentiment(''); setImpactLevel(''); setImportance('')
  }

  const handleSave = useCallback(async (articleId) => {
    const isSaved = savedIds.has(articleId)
    try {
      if (isSaved) {
        await unsaveNewsArticle(articleId)
        setSavedIds((prev) => { const next = new Set(prev); next.delete(articleId); return next })
      } else {
        await saveNewsArticle(articleId)
        setSavedIds((prev) => new Set(prev).add(articleId))
      }
    } catch { /* silently fail */ }
  }, [savedIds])

  // ── Chat handlers ────────────────────────────────────────────────────

  async function handleAskNewsAnalyst(input = chatPrompt) {
    const question = (typeof input === 'string' ? input : chatPrompt).trim()
    if (!question || chatLoading) return
    const now = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    const recentHistory = chatMessages.slice(-8).map((m) => ({
      sender: m.sender, content: m.body || m.summary || '',
    }))
    setChatMessages((cur) => [...cur, { id: `user-${Date.now()}`, sender: 'user', body: question, timestamp: now }])
    setChatPrompt('')
    setChatLoading(true)
    setChatError('')
    try {
      const r = await askNewsAnalyst({
        message: question,
        conversation_id: chatConversationId || undefined,
        category: category === 'all' ? undefined : category,
        region: region || undefined,
        source_group: sourceGroup || undefined,
        preset: apiPreset || undefined,
        time_range_hours: timeRangeHours,
        active_article_id: activeArticle?.article_id,
        session_id: sessionId || undefined,
        history: recentHistory,
      })
      setChatConversationId(r.conversation_id)
      setChatMessages((cur) => [...cur, {
        id: r.message_id, sender: 'assistant',
        title: r.title, body: r.explanation,
        summary: r.summary, keyPoints: r.key_points || [],
        sources: r.sources || [], toolsUsed: r.tools_used || [],
        warnings: r.warnings || [],
        confidenceLabel: r.confidence_label, dataFreshness: r.data_freshness,
        safetyNote: r.safety_note || r.safety?.disclaimer || '',
        affectedMarkets: r.affected_markets || [],
        whatToMonitor: r.what_to_monitor || [],
        suggestedFollowups: r.suggested_followups || r.suggested_questions || [],
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      }])
    } catch (err) { setChatError(err.message) }
    finally { setChatLoading(false) }
  }

  function handleChatKeyDown(e) {
    if (e.key !== 'Enter' || e.shiftKey) return
    e.preventDefault()
    void handleAskNewsAnalyst()
  }

  // ── Derived data ─────────────────────────────────────────────────────

  const articles = payload?.articles || []
  const feedCap = Math.min(feedVisible, articles.length)
  const feedArticles = articles.slice(0, feedCap)

  const finnhubCalEvents = macroDesk?.calendar?.events || []

  useEffect(() => {
    if (!activeArticleId || !articles.length) return
    const idx = articles.findIndex((a) => a.article_id === activeArticleId)
    if (idx < 0) return
    const need = idx + 1
    setFeedVisible((v) => (need > v ? need : v))
  }, [activeArticleId, articles])

  useEffect(() => {
    const root = feedScrollRef.current
    const target = feedSentinelRef.current
    if (!root || !target || feedVisible >= articles.length) return
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setFeedVisible((n) => Math.min(n + FEED_LIST_STEP, articles.length))
        }
      },
      { root, rootMargin: '120px 0px', threshold: 0 },
    )
    io.observe(target)
    return () => io.disconnect()
  }, [articles.length, feedVisible])

  const todayBrief = payload?.today_brief || []
  const clusters = payload?.clusters || []
  const pulse = payload?.pulse || {}
  const activeArticle = useMemo(
    () => articles.find((a) => a.article_id === activeArticleId) || articles[0],
    [activeArticleId, articles],
  )
  const detail = articleDetail || null
  const freshness = payload?.freshness || 'loading'
  const sourceCount = payload?.source_count || 0
  const successfulSourceCount = payload?.successful_source_count || 0

  const pulseSentiment = useMemo(() => {
    const n = Number(pulse.article_count) || articles.length || 0
    const pos = Number(pulse.positive_count) || 0
    const neg = Number(pulse.negative_count) || 0
    const neu = Math.max(0, n - pos - neg)
    const pct = (c) => (n > 0 ? Math.min(100, Math.round((c / n) * 100)) : 0)
    return { n, pos, neg, neu, posPct: pct(pos), negPct: pct(neg), neuPct: pct(neu) }
  }, [pulse.article_count, pulse.positive_count, pulse.negative_count, articles.length])

  const topImpactCats = useMemo(() => (pulse.top_categories || []).slice(0, 3), [pulse.top_categories])
  const maxImpactCount = useMemo(
    () => Math.max(1, ...topImpactCats.map((c) => Number(c.count) || 0)),
    [topImpactCats],
  )
  const previewEconEvents = useMemo(() => finnhubCalEvents.slice(0, 5), [finnhubCalEvents])
  const topBrief = todayBrief[0]

  useNewsSparkleMotion()

  useEffect(() => {
    if (!econCalendarIframeOpen) return undefined
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prevOverflow
    }
  }, [econCalendarIframeOpen])

  useEffect(() => {
    if (!econCalendarIframeOpen) return undefined
    function onKey(e) {
      if (e.key === 'Escape') setEconCalendarIframeOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [econCalendarIframeOpen])

  function openEconomicCalendarIframe() {
    setEconCalendarIframeKey((k) => k + 1)
    setEconCalendarIframeOpen(true)
  }

  // ── Render ───────────────────────────────────────────────────────────

  const analystNode = (
    <div className={`news-desk__floating-analyst ${chatOpen ? 'is-open' : ''}`}>
      {chatOpen ? (
        <section className="news-desk__analyst" aria-label="News Analyst chat">
          <div className="news-desk__analyst-head">
            <div>
              <p>News Analyst</p>
              <h2>Hỏi sâu về tin tức</h2>
            </div>
            <button type="button" onClick={() => setChatOpen(false)} aria-label="Thu gọn">×</button>
          </div>
          <div className="news-desk__analyst-context">
            <span>{chatLoading ? 'Thinking' : 'Ready'}</span>
            <span>{category === 'all' ? 'all categories' : category}</span>
            <span>{region || 'all regions'}</span>
            {activeArticle ? <span>Article selected</span> : null}
          </div>
          <div className="news-desk__analyst-thread" aria-live="polite">
            {!chatMessages.length ? (
              <div className="news-desk__analyst-empty">
                <strong>News Analyst</strong>
                <span>Đọc feed, cụm tin, pulse và headline đang chọn để trả lời theo bối cảnh thị trường.</span>
              </div>
            ) : null}
            {chatMessages.map((msg) => (
              <article key={msg.id} className={msg.sender === 'assistant' ? 'news-desk__chat-message is-assistant' : 'news-desk__chat-message is-user'}>
                {msg.title ? <strong>{msg.title}</strong> : null}
                {msg.summary ? <p className="news-desk__chat-summary">{msg.summary}</p> : null}
                <p>{msg.body}</p>
                {msg.keyPoints?.length ? (
                  <ul>{msg.keyPoints.map((p, i) => <li key={i}>{p}</li>)}</ul>
                ) : null}
                {msg.affectedMarkets?.length ? (
                  <div className="news-desk__chat-tags">
                    {msg.affectedMarkets.map((m) => <span key={m} className="news-desk__tag">{m}</span>)}
                  </div>
                ) : null}
                {msg.whatToMonitor?.length ? (
                  <div className="news-desk__chat-monitors">
                    <span className="news-desk__chat-monitors-label">Monitor:</span>
                    {msg.whatToMonitor.map((m) => <span key={m} className="news-desk__tag is-monitor">{m}</span>)}
                  </div>
                ) : null}
                {msg.sources?.length ? (
                  <div className="news-desk__chat-sources">
                    {msg.sources.slice(0, 3).map((s) => (
                      s.url ? <a key={s.article_id || s.label} href={s.url} target="_blank" rel="noreferrer">{s.source}</a>
                        : <span key={s.article_id || s.label}>{s.source}</span>
                    ))}
                  </div>
                ) : null}
                {msg.confidenceLabel ? (
                  <div className="news-desk__chat-meta">
                    <span>{msg.confidenceLabel}</span>
                    <span>{msg.dataFreshness}</span>
                  </div>
                ) : null}
                {msg.safetyNote ? <p className="news-desk__chat-safety">{msg.safetyNote}</p> : null}
                {msg.suggestedFollowups?.length ? (
                  <div className="news-desk__analyst-examples">
                    {msg.suggestedFollowups.map((q) => (
                      <button key={q} type="button" onClick={() => void handleAskNewsAnalyst(q)} disabled={chatLoading}>{q}</button>
                    ))}
                  </div>
                ) : null}
                <time>{msg.timestamp}</time>
              </article>
            ))}
            {chatLoading ? <p className="news-desk__chat-typing">News Analyst đang phân tích...</p> : null}
          </div>
          <div className="news-desk__analyst-examples">
            {NEWS_CHAT_EXAMPLES.map((ex) => (
              <button key={ex} type="button" onClick={() => void handleAskNewsAnalyst(ex)} disabled={chatLoading}>{ex}</button>
            ))}
          </div>
          <div className="news-desk__analyst-composer">
            <textarea value={chatPrompt} onChange={(e) => setChatPrompt(e.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Hỏi về tác động của tin, nguồn xác nhận, hàng hóa, USD, thị trường..."
              rows={3} />
            <button type="button" onClick={() => void handleAskNewsAnalyst()}
              disabled={chatLoading || !chatPrompt.trim()}>Ask</button>
          </div>
          {chatError ? <p className="news-desk__state news-desk__state--error">{chatError}</p> : null}
        </section>
      ) : (
        <button type="button" className="news-desk__analyst-launcher" onClick={() => setChatOpen(true)}>
          <span aria-hidden="true">N</span>
          <span>
            <strong>News Analyst</strong>
            <em>{chatMessages.length ? `${chatMessages.length} messages` : 'Hỏi sâu về news'}</em>
          </span>
        </button>
      )}
    </div>
  )

  return (
    <>
      <section className="news-desk">
        <div className="news-sparkle-home">
          <div className="news-sparkle-compact-header">
            <div className="news-sparkle-compact-title">
              <span className="news-sparkle-shield-ic" aria-hidden>🛡</span>
              <h1>News Intelligence</h1>
              <div className="news-sparkle-dash news-sparkle-dash--compact">
                {/* Today Brief Ticker */}
                {topBrief ? (
                  <button type="button" className="news-sparkle-compact-ticker" onClick={() => { setActiveArticleId(topBrief.article_id); setMobileTabIfMobile('detail') }}>
                    <span className="ticker-badge">Top story</span>
                    <strong className="ticker-headline">{topBrief.headline}</strong>
                    <span className="ticker-source">{topBrief.source} · {topBrief.time || formatNewsDate(topBrief.published_at)}</span>
                  </button>
                ) : null}
              </div>
            </div>
            
            <nav className="news-sparkle-actions" aria-label="Thao tác nhanh">
              <button type="button" className="news-sparkle-btn news-sparkle-btn--dark" onClick={() => setChatOpen(true)}>
                <span aria-hidden>✦</span> Ask Analyst
              </button>
              <button type="button" className="news-sparkle-btn news-sparkle-btn--light" onClick={handleRefresh}>
                ↻ Refresh feeds
              </button>
            </nav>
          </div>
        </div>

        <div id="news-desk-main" className="news-desk__main-panel">

        {/* ── Control Bar ───────────────────────────────────────────── */}
        <section className="news-desk__control-bar" aria-label="News filters">
          <div className="news-desk__market-lens" aria-label="Market Lens">
            <button
              type="button"
              className={marketLens === 'vietnam' ? 'is-active' : ''}
              onClick={() => handleLensChange('vietnam')}
            >
              🇻🇳 Thị trường Việt Nam
            </button>
            <button
              type="button"
              className={marketLens === 'global' ? 'is-active' : ''}
              onClick={() => handleLensChange('global')}
            >
              🌎 Vĩ mô Toàn cầu
            </button>
            <button
              type="button"
              className={marketLens === 'cross_impact' ? 'is-active is-impact' : ''}
              onClick={() => handleLensChange('cross_impact')}
            >
              🔗 Tác động chéo (Cross-Impact)
            </button>
          </div>

          <div className="news-desk__control-tier1">
            <div className="news-desk__search">
              <label>
                <span>Search</span>
                <input value={query} onChange={(e) => setQuery(e.target.value)}
                  placeholder="Tìm Fed, BTC, oil, earnings..." />
              </label>
            </div>
            {marketLens === 'cross_impact' && (
              <div className="news-desk__preset-hint" aria-label="Cross Impact Hint">
                💡 <em>Chế độ AI Insight:</em> Hãy thử chọn 1 tin Quốc tế và hỏi "Tin này ảnh hưởng gì đến chứng khoán Việt Nam?"
              </div>
            )}
          </div>
        </section>

        {/* ── Today Brief (các tin còn lại; tin đầu đã ở hero) ─────────── */}
        {todayBrief.length > 1 ? (
          <section id="news-today-brief-rest" className="news-desk__today-brief" aria-label="Today Brief thêm">
            <div className="news-desk__section-head">
              <h2>Today Brief</h2>
              <span>{todayBrief.length - 1} tin nổi bật khác</span>
            </div>
            <div className="news-desk__brief-grid">
              {todayBrief.slice(1).map((item) => (
                <TodayBriefCard
                  key={item.article_id}
                  item={item}
                  isActive={item.article_id === activeArticleId}
                  isSaved={savedIds.has(item.article_id)}
                  onSelect={() => { setActiveArticleId(item.article_id); setMobileTabIfMobile('detail') }}
                  onSave={() => handleSave(item.article_id)}
                  onAskAi={() => { setChatOpen(true); setChatPrompt(`Giải thích tin này: ${item.headline}`) }}
                />
              ))}
            </div>
          </section>
        ) : null}

        {/* ── Mobile tabs ───────────────────────────────────────────── */}
        <div className="news-desk__mobile-tabs">
          {['feed', 'detail', 'pulse'].map((tab) => (
            <button key={tab} type="button"
              className={mobileTab === tab ? 'is-active' : ''}
              onClick={() => setMobileTab(tab)}>
              {tab === 'feed' ? 'Feed' : tab === 'detail' ? 'Detail' : 'Pulse'}
            </button>
          ))}
        </div>

        {/* ── 3-Column Desk ─────────────────────────────────────────── */}
        <div className="news-desk__workspace">
          {/* Feed Panel */}
          <aside className={`news-desk__feed ${mobileTab !== 'feed' ? 'is-mobile-hidden' : ''}`} ref={feedRef} aria-label="Article feed">
            <div className="news-desk__panel-head">
              <div>
                <p>Live feed</p>
                <h2>{articles.length} tin</h2>
                {articles.length > 0 ? (
                  <p className="news-desk__feed-count">
                    Đang hiển thị {feedArticles.length}/{articles.length}
                    {feedArticles.length < articles.length ? ' · cuộn xuống hoặc bấm “Xem thêm”' : ''}
                  </p>
                ) : null}
              </div>
              {loading ? <span>Syncing</span> : <span>Ready</span>}
            </div>
            {error ? <p className="news-desk__state news-desk__state--error">{error}</p> : null}
            {!loading && !articles.length ? <p className="news-desk__state">Chưa có news trong filter này.</p> : null}
            <div className="news-desk__feed-scroll" ref={feedScrollRef}>
              <div className="news-desk__feed-list">
                {feedArticles.map((a) => (
                  <button key={a.article_id} type="button"
                    className={a.article_id === activeArticle?.article_id ? 'news-desk__feed-item is-active' : 'news-desk__feed-item'}
                    aria-label={`Xem chi tiết: ${a.headline}`}
                    onClick={() => { setActiveArticleId(a.article_id); setMobileTabIfMobile('detail') }}>
                    <div className="news-desk__feed-item-top">
                      <time>{formatNewsDate(a.published_at)}</time>
                      <ImportanceBadge label={a.importance_label} score={a.importance_score} />
                    </div>
                    <strong>{a.headline}</strong>
                    <span className="news-desk__feed-item-meta">
                      <b>{a.category}</b>
                      <em className={`is-${a.sentiment || 'neutral'}`}>{a.sentiment}</em>
                      <em>{a.source}</em>
                      {a.impact === 'high' ? <em className="is-impact-high">high impact</em> : null}
                    </span>
                    {a.affected_markets?.length ? (
                      <span className="news-desk__feed-item-tags">
                        {a.affected_markets.slice(0, 3).map((m) => <span key={m} className="news-desk__tag is-small">{m}</span>)}
                      </span>
                    ) : null}
                  </button>
                ))}
              </div>
              {feedArticles.length < articles.length ? (
                <>
                  <div ref={feedSentinelRef} className="news-desk__list-sentinel" aria-hidden />
                  <div className="news-desk__load-more-wrap">
                    <button
                      type="button"
                      className="news-desk__button news-desk__button--ghost news-desk__load-more"
                      onClick={() => setFeedVisible((n) => Math.min(n + FEED_LIST_STEP, articles.length))}>
                      Xem thêm ({articles.length - feedArticles.length} tin)
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          </aside>

          {/* Article Detail Panel */}
          <article className={`news-desk__story ${mobileTab !== 'detail' ? 'is-mobile-hidden' : ''}`}>
            {activeArticle ? (
              <>

                {/* Headline — scan anchor */}
                <h2>{activeArticle.headline}</h2>

                {/* Summary first: reader decides whether to open original */}
                <section className="news-desk__summary-lead" aria-labelledby="news-summary-heading">
                  <h3 id="news-summary-heading" className="news-desk__summary-lead-title">Tóm tắt</h3>
                  <p className="news-desk__summary-lead-body">
                    {activeArticle.summary?.trim()
                      ? activeArticle.summary
                      : 'Nguồn chỉ cung cấp tiêu đề ngắn — mở bài gốc để đọc đầy đủ, hoặc dùng Ask AI để giải thích bối cảnh từ dữ liệu đã thu thập.'}
                  </p>
                  {(detail?.original_source || activeArticle.url) ? (
                    <a className="news-desk__summary-lead-cta" href={detail?.original_source || activeArticle.url} target="_blank" rel="noreferrer">
                      Đọc bài gốc ↗
                    </a>
                  ) : null}
                </section>

                <div className="news-desk__story-actions">
                  <button type="button" className="news-desk__button news-desk__button--ghost"
                    onClick={() => handleSave(activeArticle.article_id)}>
                    {savedIds.has(activeArticle.article_id) ? '✓ Saved' : 'Save'}
                  </button>
                  <button type="button" className="news-desk__button news-desk__button--ghost"
                    onClick={() => { setChatOpen(true); setChatPrompt(`Giải thích tin này: ${activeArticle.headline}`) }}>
                    Ask AI
                  </button>
                </div>


                {/* E. Affected Markets */}
                {(detail?.affected_markets || activeArticle.affected_markets)?.length ? (
                  <section className="news-desk__section-block">
                    <h3>Affected Markets</h3>
                    <div className="news-desk__tag-list">
                      {(detail?.affected_markets || activeArticle.affected_markets).map((m) => (
                        <span key={m} className="news-desk__tag">{m}</span>
                      ))}
                    </div>
                  </section>
                ) : null}


                {/* H. Related Articles */}
                {detail?.related_articles?.length ? (
                  <section className="news-desk__section-block">
                    <h3>Related articles</h3>
                    <div className="news-desk__related-list">
                      {detail.related_articles.map((ra) => (
                        <button key={ra.article_id} type="button" className="news-desk__related-item"
                          onClick={() => setActiveArticleId(ra.article_id)}>
                          <strong>{ra.headline}</strong>
                          <span>{ra.source} · {formatNewsDate(ra.published_at)}</span>
                        </button>
                      ))}
                    </div>
                  </section>
                ) : null}

              </>
            ) : (
              <div className="news-desk__empty-detail">
                <p className="news-desk__state">Chọn một tin trong feed để xem phân tích chi tiết.</p>
                {todayBrief.length ? <p className="news-desk__empty-hint">Hoặc chọn một tin từ Today Brief ở trên.</p> : null}
              </div>
            )}
            {detailLoading ? <div className="news-desk__detail-loading">Loading detail...</div> : null}
          </article>

          {/* Market Pulse panel removed as per user request */}
        </div>

        {/* Safety disclaimer */}
        <footer className="news-desk__safety-footer">
          <span>Tin tức là bối cảnh phân tích, không phải khuyến nghị mua/bán.</span>
        </footer>
        </div>
      </section>
      {typeof document === 'undefined' ? analystNode : createPortal(analystNode, document.body)}
      {econCalendarIframeOpen && typeof document !== 'undefined'
        ? createPortal(
            <div
              className="news-desk__econ-cal-iframe-backdrop"
              role="presentation"
              onClick={() => setEconCalendarIframeOpen(false)}>
              <div
                className="news-desk__econ-cal-iframe-panel"
                role="dialog"
                aria-modal="true"
                aria-labelledby="news-econ-cal-iframe-title"
                onClick={(e) => e.stopPropagation()}>
                <div className="news-desk__econ-cal-iframe-head">
                  <h2 id="news-econ-cal-iframe-title" className="news-desk__econ-cal-iframe-title">
                    Lịch kinh tế
                  </h2>
                  <button
                    type="button"
                    className="news-desk__econ-cal-iframe-close"
                    onClick={() => setEconCalendarIframeOpen(false)}
                    aria-label="Đóng">
                    ×
                  </button>
                </div>
                <iframe
                  key={econCalendarIframeKey}
                  className="news-desk__econ-cal-iframe-el"
                  src={getNewsEconomicCalendarEmbedUrl()}
                  title="Lịch kinh tế Finnhub"
                />
              </div>
            </div>,
            document.body,
          )
        : null}
    </>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────

function useNewsSparkleMotion() {
  useEffect(() => {
    const hero = document.querySelector('.news-sparkle-hero')
    if (!hero) return undefined

    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) return undefined

    function handlePointerMove(event) {
      const rect = hero.getBoundingClientRect()
      const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
      const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2
      hero.style.setProperty('--news-hero-x', x.toFixed(3))
      hero.style.setProperty('--news-hero-y', y.toFixed(3))
    }

    hero.addEventListener('pointermove', handlePointerMove)

    return () => {
      hero.removeEventListener('pointermove', handlePointerMove)
    }
  }, [])
}

function TodayBriefCard({ item, isActive, isSaved, onSelect, onSave, onAskAi }) {
  return (
    <div
      className={`news-desk__brief-card news-desk__brief-card--clickable ${isActive ? 'is-active' : ''}`}
      role="button"
      tabIndex={0}
      aria-label={`Xem chi tiết: ${item.headline}`}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onSelect()
        }
      }}
    >
      <div className="news-desk__brief-card-top">
        <ImportanceBadge label={item.importance_label} score={item.importance_score} />
        <span className="news-desk__brief-card-source">{item.source} · {item.time || formatNewsDate(item.published_at)}</span>
      </div>
      <p className="news-desk__brief-card-headline">
        <strong>{item.headline}</strong>
      </p>
      <p className="news-desk__brief-card-why">{item.why_it_matters}</p>
      {item.affected_markets?.length ? (
        <div className="news-desk__brief-card-tags">
          {item.affected_markets.map((m) => <span key={m} className="news-desk__tag is-small">{m}</span>)}
        </div>
      ) : null}
      <div className="news-desk__brief-card-actions" onClick={(e) => e.stopPropagation()}>
        <button type="button" onClick={onSave}>{isSaved ? '✓ Saved' : 'Save'}</button>
        <button type="button" onClick={onAskAi}>Ask AI</button>
      </div>
    </div>
  )
}

function ImportanceBadge({ label, score }) {
  if (!label || label === 'noise') return null
  return (
    <span className={`news-desk__importance is-${label}`}>
      {label}{score ? ` ${score}` : ''}
    </span>
  )
}

function Metric({ label, value }) {
  return (
    <div className="news-desk__metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="news-desk__info-row">
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

function formatNewsDate(value) {
  if (!value) return '--'
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
