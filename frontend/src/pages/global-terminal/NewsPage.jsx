import { useEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'

import { askNewsAnalyst, fetchNewsFeed } from '../../modules/data-hub'
import './news.css'

const CATEGORIES = ['all', 'macro', 'markets', 'commodities', 'crypto', 'regulation', 'geopolitics', 'technology']
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
const NEWS_CHAT_EXAMPLES = [
  'Tin Fed hôm nay ảnh hưởng hàng hóa thế nào?',
  'Headline này có đáng lo cho thị trường không?',
  'Tóm tắt các rủi ro chính trong filter hiện tại.',
]

export default function NewsPage({ sessionId, onBack, onOpenGlobalTerminal }) {
  const [payload, setPayload] = useState(null)
  const [category, setCategory] = useState('all')
  const [query, setQuery] = useState('')
  const [preset, setPreset] = useState('balanced')
  const [region, setRegion] = useState('')
  const [sourceGroup, setSourceGroup] = useState('')
  const [timeRangeHours, setTimeRangeHours] = useState(168)
  const [activeArticleId, setActiveArticleId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [chatPrompt, setChatPrompt] = useState('Tin Fed hôm nay ảnh hưởng hàng hóa thế nào?')
  const [chatMessages, setChatMessages] = useState([])
  const [chatConversationId, setChatConversationId] = useState('')
  const [chatOpen, setChatOpen] = useState(false)
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const apiPreset = preset === 'balanced' ? '' : preset

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
        })
        if (!cancelled) {
          setPayload(data)
          setActiveArticleId((current) => current || data.articles?.[0]?.article_id || '')
        }
      } catch (err) {
        if (!cancelled) setError(err.message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    const timer = window.setTimeout(run, 250)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [category, query, preset, apiPreset, region, sourceGroup, timeRangeHours])

  async function handleRefresh() {
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
        force: true,
      })
      setPayload(data)
      setActiveArticleId(data.articles?.[0]?.article_id || '')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const articles = payload?.articles || []
  const activeArticle = useMemo(
    () => articles.find((article) => article.article_id === activeArticleId) || articles[0],
    [activeArticleId, articles],
  )

  async function handleAskNewsAnalyst(input = chatPrompt) {
    const question = input.trim()
    if (!question || chatLoading) return
    const now = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    const recentHistory = chatMessages.slice(-8).map((message) => ({
      sender: message.sender,
      content: message.body || message.summary || '',
    }))
    setChatMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        sender: 'user',
        body: question,
        timestamp: now,
      },
    ])
    setChatPrompt('')
    setChatLoading(true)
    setChatError('')
    try {
      const response = await askNewsAnalyst({
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
      setChatConversationId(response.conversation_id)
      setChatMessages((current) => [
        ...current,
        {
          id: response.message_id,
          sender: 'assistant',
          title: response.title,
          body: response.explanation,
          summary: response.summary,
          keyPoints: response.key_points || [],
          sources: response.sources || [],
          toolsUsed: response.tools_used || [],
          warnings: response.warnings || [],
          confidenceLabel: response.confidence_label,
          dataFreshness: response.data_freshness,
          timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } catch (err) {
      setChatError(err.message)
    } finally {
      setChatLoading(false)
    }
  }

  function handleChatKeyDown(event) {
    if (event.key !== 'Enter' || event.shiftKey) return
    event.preventDefault()
    void handleAskNewsAnalyst()
  }

  const analystNode = (
    <div className={`news-desk__floating-analyst ${chatOpen ? 'is-open' : ''}`}>
      {chatOpen ? (
        <section className="news-desk__analyst" aria-label="News Analyst chat">
          <div className="news-desk__analyst-head">
            <div>
              <p>News Analyst</p>
              <h2>Hỏi sâu về tin tức</h2>
            </div>
            <button type="button" onClick={() => setChatOpen(false)} aria-label="Thu gọn News Analyst">×</button>
          </div>
          <div className="news-desk__analyst-context">
            <span>{chatLoading ? 'Thinking' : 'Ready'}</span>
            <span>{category === 'all' ? 'all categories' : category}</span>
            <span>{region || 'all regions'}</span>
          </div>
          <div className="news-desk__analyst-thread" aria-live="polite">
            {!chatMessages.length ? (
              <div className="news-desk__analyst-empty">
                <strong>Bot riêng cho News</strong>
                <span>Đọc feed, cụm tin, pulse và headline đang chọn để trả lời theo bối cảnh thị trường.</span>
              </div>
            ) : null}
            {chatMessages.map((message) => (
              <article
                key={message.id}
                className={message.sender === 'assistant' ? 'news-desk__chat-message is-assistant' : 'news-desk__chat-message is-user'}
              >
                {message.title ? <strong>{message.title}</strong> : null}
                {message.summary ? <p className="news-desk__chat-summary">{message.summary}</p> : null}
                <p>{message.body}</p>
                {message.keyPoints?.length ? (
                  <ul>
                    {message.keyPoints.map((point) => <li key={point}>{point}</li>)}
                  </ul>
                ) : null}
                {message.sources?.length ? (
                  <div className="news-desk__chat-sources">
                    {message.sources.slice(0, 3).map((source) => (
                      source.url ? (
                        <a key={source.article_id || source.label} href={source.url} target="_blank" rel="noreferrer">{source.source}</a>
                      ) : (
                        <span key={source.article_id || source.label}>{source.source}</span>
                      )
                    ))}
                  </div>
                ) : null}
                {message.confidenceLabel ? (
                  <div className="news-desk__chat-meta">
                    <span>{message.confidenceLabel}</span>
                    <span>{message.dataFreshness}</span>
                  </div>
                ) : null}
                <time>{message.timestamp}</time>
              </article>
            ))}
            {chatLoading ? <p className="news-desk__chat-typing">News Analyst đang rà feed...</p> : null}
          </div>
          <div className="news-desk__analyst-examples">
            {NEWS_CHAT_EXAMPLES.map((example) => (
              <button key={example} type="button" onClick={() => void handleAskNewsAnalyst(example)} disabled={chatLoading}>
                {example}
              </button>
            ))}
          </div>
          <div className="news-desk__analyst-composer">
            <textarea
              value={chatPrompt}
              onChange={(event) => setChatPrompt(event.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Hỏi về tác động của tin, nguồn xác nhận, hàng hóa, USD, thị trường..."
              rows={3}
            />
            <button type="button" onClick={() => void handleAskNewsAnalyst()} disabled={chatLoading || !chatPrompt.trim()}>
              Ask
            </button>
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
      <header className="news-desk__hero">
        <div className="news-desk__hero-copy">
          <p>News Intelligence</p>
          <h1>Global News Desk</h1>
          <span>{payload?.freshness || 'loading'} · {payload?.successful_source_count || 0}/{payload?.source_count || 0} sources connected</span>
          <p className="news-desk__lede">
            Một bàn tin gọn để đọc bối cảnh thị trường, lọc chủ đề quan trọng và mở nhanh terminal khi cần đào sâu dữ liệu.
          </p>
        </div>
        <nav className="news-desk__hero-actions">
          <button type="button" className="news-desk__button news-desk__button--ghost" onClick={onOpenGlobalTerminal}>Global Terminal</button>
          <button type="button" className="news-desk__button news-desk__button--primary" onClick={handleRefresh}>Refresh feeds</button>
          <button type="button" className="news-desk__button news-desk__button--ghost" onClick={onBack}>Home</button>
        </nav>
      </header>

      <section className="news-desk__control-bar" aria-label="News filters">
        <div className="news-desk__search">
          <label>
            <span>Search</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Fed, BTC, oil, earnings..." />
          </label>
        </div>
        <div className="news-desk__select-grid">
          <label>
            <span>Region</span>
            <select value={region} onChange={(event) => {
              setRegion(event.target.value)
              setPreset('balanced')
            }}>
              {REGIONS.map((item) => (
                <option key={item.value || 'all'} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Source mix</span>
            <select value={sourceGroup} onChange={(event) => {
              setSourceGroup(event.target.value)
              setPreset('balanced')
            }}>
              {SOURCE_GROUPS.map((item) => (
                <option key={item.value || 'all'} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Window</span>
            <select value={timeRangeHours} onChange={(event) => setTimeRangeHours(Number(event.target.value))}>
              {TIME_RANGES.map((item) => (
                <option key={item.value} value={item.value}>{item.label}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="news-desk__preset-row" aria-label="News presets">
          {PRESETS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={preset === item.id ? 'is-active' : ''}
              onClick={() => {
                setPreset(item.id)
                setRegion('')
                setSourceGroup('')
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="news-desk__category-row" aria-label="News categories">
          {CATEGORIES.map((item) => (
            <button
              key={item}
              type="button"
              className={category === item ? 'is-active' : ''}
              onClick={() => setCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </section>

      <div className="news-desk__workspace">
        <aside className="news-desk__feed" aria-label="Article feed">
          <div className="news-desk__panel-head">
            <div>
              <p>Live feed</p>
              <h2>{articles.length} headlines</h2>
            </div>
            {loading ? <span>Syncing</span> : <span>Ready</span>}
          </div>
          {error ? <p className="news-desk__state news-desk__state--error">{error}</p> : null}
          {!loading && !articles.length ? <p className="news-desk__state">Chưa có news trong filter này.</p> : null}
          <div className="news-desk__feed-list">
            {articles.map((article) => (
              <button
                key={article.article_id}
                type="button"
                className={article.article_id === activeArticle?.article_id ? 'news-desk__feed-item is-active' : 'news-desk__feed-item'}
                onClick={() => setActiveArticleId(article.article_id)}
              >
                <time>{formatNewsDate(article.published_at)}</time>
                <strong>{article.headline}</strong>
                <span>
                  <b>{article.category}</b>
                  <em className={`is-${article.sentiment || 'neutral'}`}>
                    {article.sentiment}
                  </em>
                  <em>{article.source}</em>
                </span>
              </button>
            ))}
          </div>
        </aside>

        <article className="news-desk__story">
          {activeArticle ? (
            <>
              <div className="news-desk__badges">
                <span>{activeArticle.source_flag}</span>
                <span>{activeArticle.impact} impact</span>
                <span>{activeArticle.freshness || payload?.freshness || 'fresh'}</span>
                {activeArticle.threat_level !== 'normal' ? <span className="is-warn">{activeArticle.threat_level}</span> : null}
              </div>
              <h2>{activeArticle.headline}</h2>
              <p className="news-desk__summary">{activeArticle.summary || 'Nguồn RSS không cung cấp summary. Mở source để đọc đầy đủ.'}</p>
              <dl className="news-desk__info-grid">
                <InfoRow label="Source" value={`${activeArticle.source} · tier ${activeArticle.source_tier}`} />
                <InfoRow label="Published" value={formatNewsDate(activeArticle.published_at)} />
                <InfoRow label="Category" value={activeArticle.category} />
                <InfoRow label="Source mix" value={activeArticle.source_group || 'global'} />
                <InfoRow label="Tickers" value={activeArticle.tickers?.length ? activeArticle.tickers.join(', ') : 'None detected'} />
              </dl>
              <section className="news-desk__explain">
                <h3>Why this matters</h3>
                <p>
                  Tin được phân loại theo source tier, sentiment, impact và risk keywords. Đây là lớp đọc bối cảnh,
                  không phải tín hiệu mua bán hay khuyến nghị đầu tư cá nhân hóa.
                </p>
              </section>
              {activeArticle.url ? (
                <a className="news-desk__source-link" href={activeArticle.url} target="_blank" rel="noreferrer">
                  Open original source
                </a>
              ) : null}
            </>
          ) : (
            <p className="news-desk__state">Chọn một headline để đọc chi tiết.</p>
          )}
        </article>

        <aside className="news-desk__pulse">
          <div className="news-desk__panel-head">
            <div>
              <p>Market pulse</p>
              <h2>Today</h2>
            </div>
          </div>
          <div className="news-desk__metric-grid">
            <Metric label="Articles" value={payload?.pulse?.article_count || 0} />
            <Metric label="High impact" value={payload?.pulse?.high_impact_count || 0} />
            <Metric label="Negative" value={payload?.pulse?.negative_count || 0} />
            <Metric label="Positive" value={payload?.pulse?.positive_count || 0} />
          </div>
          <h3>Top regions</h3>
          <div className="news-desk__rank-list">
            {(payload?.pulse?.top_regions || []).map((item) => (
              <p key={item.label}><span>{item.label}</span><b>{item.count}</b></p>
            ))}
          </div>
          <h3>Top categories</h3>
          <div className="news-desk__rank-list">
            {(payload?.pulse?.top_categories || []).map((item) => (
              <p key={item.label}><span>{item.label}</span><b>{item.count}</b></p>
            ))}
          </div>
          <h3>Clusters</h3>
          <div className="news-desk__rank-list">
            {(payload?.clusters || []).slice(0, 5).map((cluster) => (
              <p key={cluster.cluster_id}><span>{cluster.similarity_topic}</span><b>{cluster.article_count}</b></p>
            ))}
          </div>
        </aside>
      </div>
    </section>
    {typeof document === 'undefined' ? analystNode : createPortal(analystNode, document.body)}
    </>
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
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}
