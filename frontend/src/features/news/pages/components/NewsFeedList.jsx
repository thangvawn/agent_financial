import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

const CATEGORY_MAP = {
  all: 'Tất cả',
  macro: 'Vĩ mô',
  markets: 'Thị trường',
  commodities: 'Hàng hóa',
  crypto: 'Số',
  regulation: 'Pháp lý',
  geopolitics: 'Địa chính trị',
  technology: 'Công nghệ',
  earnings: 'Doanh nghiệp',
  personal_finance: 'Cá nhân',
  risk_alerts: 'Rủi ro',
}

const CATEGORIES = [
  'all', 'macro', 'markets', 'commodities', 'crypto', 'regulation',
  'geopolitics', 'technology', 'earnings', 'personal_finance', 'risk_alerts',
]

/*
 * ALL styles injected via <style> with !important.
 * Zero className on any child element.
 * Every single property is locked.
 */
const STYLES = `
/* ═══ Feed Panel Container ═══ */
[data-feed-panel] {
  display: flex !important;
  flex-direction: column !important;
  gap: 0 !important;
  background: #161b26 !important;
  border: 1px solid #1f293d !important;
  border-radius: 8px !important;
  padding: 16px !important;
  height: 85vh !important;
  max-height: 900px !important;
  min-height: 500px !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
  width: 100% !important;
}

/* ═══ Panel Header ═══ */
[data-feed-header] {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  border-bottom: 1px solid rgba(31,41,61,0.5) !important;
  padding-bottom: 12px !important;
  margin-bottom: 12px !important;
  flex-shrink: 0 !important;
}
[data-feed-header] h2 {
  font-size: 11px !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  color: #94a3b8 !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1.4 !important;
}
[data-feed-header] p {
  font-size: 10px !important;
  color: #64748b !important;
  margin: 2px 0 0 0 !important;
  padding: 0 !important;
  line-height: 1.3 !important;
}
[data-feed-status] {
  font-size: 10px !important;
  font-family: monospace !important;
  font-weight: 700 !important;
}

/* ═══ Category Tabs ═══ */
[data-feed-cats] {
  display: flex !important;
  gap: 6px !important;
  overflow-x: auto !important;
  padding-bottom: 10px !important;
  margin-bottom: 12px !important;
  border-bottom: 1px solid rgba(31,41,61,0.3) !important;
  flex-shrink: 0 !important;
  scrollbar-width: none !important;
}
[data-feed-cats]::-webkit-scrollbar { display: none !important; }
[data-feed-cat] {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 4px 10px !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  border-radius: 999px !important;
  cursor: pointer !important;
  flex-shrink: 0 !important;
  white-space: nowrap !important;
  border: 1px solid rgba(31,41,61,0.7) !important;
  background: #0f1420 !important;
  color: #94a3b8 !important;
  min-height: 0 !important;
  height: auto !important;
  box-shadow: none !important;
  transform: none !important;
  transition: all 0.15s ease !important;
}
[data-feed-cat]:hover {
  color: #e2e8f0 !important;
}
[data-feed-cat][data-selected="true"] {
  background: rgba(13,148,136,0.15) !important;
  color: #2dd4bf !important;
  border-color: rgba(45,212,191,0.4) !important;
}

/* ═══ Scroll Body ═══ */
[data-feed-scroll] {
  flex: 1 1 0% !important;
  min-height: 0 !important;
  overflow-y: scroll !important;
  overflow-x: hidden !important;
  padding-right: 4px !important;
}
[data-feed-scroll]::-webkit-scrollbar { width: 5px !important; }
[data-feed-scroll]::-webkit-scrollbar-track { background: transparent !important; }
[data-feed-scroll]::-webkit-scrollbar-thumb { background: #1f293d !important; border-radius: 3px !important; }

/* ═══ Individual Card ═══ */
[data-nfl-card] {
  display: block !important;
  width: 100% !important;
  text-align: left !important;
  height: auto !important;
  min-height: 0 !important;
  padding: 14px 16px !important;
  border-radius: 8px !important;
  cursor: pointer !important;
  margin: 0 0 8px 0 !important;
  box-sizing: border-box !important;
  box-shadow: none !important;
  transform: none !important;
  font-size: 14px !important;
  line-height: 1.55 !important;
  position: relative !important;
  overflow: visible !important;
  white-space: normal !important;
  transition: background 0.15s ease, border-color 0.15s ease !important;
}
[data-nfl-card]:hover {
  background: rgba(22,27,38,0.95) !important;
  border-color: #374151 !important;
}
[data-nfl-card][data-active="true"] {
  background: rgba(13,148,136,0.12) !important;
  border: 1px solid rgba(45,212,191,0.45) !important;
}
[data-nfl-card][data-active="false"] {
  background: rgba(15,20,32,0.55) !important;
  border: 1px solid rgba(31,41,61,0.55) !important;
}

/* ═══ Headline ═══ */
[data-nfl-title] {
  all: unset !important;
  display: block !important;
  font-size: 13.5px !important;
  font-weight: 600 !important;
  line-height: 1.55 !important;
  margin: 0 0 8px 0 !important;
  padding: 0 !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  max-height: none !important;
  letter-spacing: -0.01em !important;
  box-sizing: border-box !important;
  width: 100% !important;
}
[data-nfl-card][data-active="true"] [data-nfl-title] {
  color: #f1f5f9 !important;
}
[data-nfl-card][data-active="false"] [data-nfl-title] {
  color: #e2e8f0 !important;
}

/* ═══ Meta Row ═══ */
[data-nfl-meta] {
  all: unset !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  font-size: 11px !important;
  color: #94a3b8 !important;
  line-height: 1.4 !important;
  margin: 0 !important;
  padding: 0 !important;
  flex-wrap: wrap !important;
  white-space: nowrap !important;
  box-sizing: border-box !important;
  width: 100% !important;
}

/* ═══ Tags ═══ */
[data-nfl-tags] {
  all: unset !important;
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 5px !important;
  margin: 8px 0 0 0 !important;
  padding: 0 !important;
  box-sizing: border-box !important;
}
[data-nfl-tag] {
  all: unset !important;
  display: inline-block !important;
  padding: 2px 8px !important;
  background: rgba(22,27,38,0.8) !important;
  border: 1px solid rgba(31,41,61,0.7) !important;
  border-radius: 4px !important;
  font-size: 10px !important;
  font-family: monospace !important;
  color: #2dd4bf !important;
  line-height: 1.5 !important;
  box-sizing: border-box !important;
}
`

export default function NewsFeedList({
  articles,
  feedArticles,
  activeArticleId,
  onSelectArticle,
  category,
  onCategoryChange,
  loading,
  error,
  feedSentinelRef,
  onLoadMore,
  hasMore,
}) {
  return (
    <div data-feed-panel="">
      <style dangerouslySetInnerHTML={{ __html: STYLES }} />

      {/* Header */}
      <div data-feed-header="">
        <div>
          <h2>Dòng tin tức ({articles.length} tin)</h2>
          {articles.length > 0 && (
            <p>Đang hiển thị {feedArticles.length}/{articles.length}</p>
          )}
        </div>
        <span data-feed-status="" style={{ color: loading ? '#64748b' : '#14b8a6' }}>
          {loading ? 'CẬP NHẬT...' : 'READY'}
        </span>
      </div>

      {/* Category Tabs */}
      <div data-feed-cats="">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            type="button"
            data-feed-cat=""
            data-selected={category === cat ? 'true' : 'false'}
            onClick={() => onCategoryChange(cat)}
          >
            {CATEGORY_MAP[cat] || cat}
          </button>
        ))}
      </div>

      {/* Feed Scroll Body */}
      <div data-feed-scroll="">
        {error && (
          <p style={{ fontSize: '12px', color: '#f87171', background: 'rgba(127,29,29,0.15)', border: '1px solid rgba(127,29,29,0.3)', padding: '12px', borderRadius: '6px', textAlign: 'center' }}>
            Không thể cập nhật tin tức. Vui lòng thử lại sau.
          </p>
        )}

        {!loading && articles.length === 0 && (
          <p style={{ fontSize: '12px', color: '#64748b', padding: '40px 0', textAlign: 'center' }}>
            Không tìm thấy tin tức phù hợp với bộ lọc hiện tại.
          </p>
        )}

        {feedArticles.map((a) => {
          const isActive = a.article_id === activeArticleId
          const showSentiment = a.sentiment && a.sentiment !== 'neutral'
          const showImportance = a.importance_label
            && a.importance_label !== 'noise'
            && a.importance_label.toLowerCase() !== 'low'

          const sentimentColor =
            a.sentiment === 'positive' ? '#34d399'
              : a.sentiment === 'negative' ? '#f87171'
              : null

          return (
            <div
              key={a.article_id}
              data-nfl-card=""
              data-active={isActive ? 'true' : 'false'}
              role="button"
              tabIndex={0}
              onClick={() => onSelectArticle(a.article_id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSelectArticle(a.article_id)
                }
              }}
            >
              <div data-nfl-title="">
                {a.headline || a.title || 'Không có tiêu đề'}
              </div>

              <div data-nfl-meta="">
                <span style={{ fontWeight: 500 }}>{a.source}</span>
                <span style={{ color: '#475569' }}>·</span>
                <span style={{ fontFamily: 'monospace' }}>
                  {formatNewsDate(a.published_at)}
                </span>
                {showSentiment && (
                  <>
                    <span style={{ color: '#475569' }}>·</span>
                    <span style={{
                      color: sentimentColor,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}>
                      {a.sentiment}
                    </span>
                  </>
                )}
                {showImportance && (
                  <span style={{
                    marginLeft: 'auto',
                    padding: '1px 5px',
                    borderRadius: '2px',
                    background: a.importance_label === 'critical'
                      ? 'rgba(239,68,68,0.12)'
                      : 'rgba(245,158,11,0.12)',
                    color: a.importance_label === 'critical'
                      ? '#f87171' : '#fbbf24',
                    fontWeight: 700,
                    fontSize: '9px',
                    textTransform: 'uppercase',
                  }}>
                    {a.importance_label}
                  </span>
                )}
              </div>

              {a.affected_markets?.length > 0 && (
                <div data-nfl-tags="">
                  {a.affected_markets.slice(0, 3).map((m) => (
                    <span key={m} data-nfl-tag="">{m}</span>
                  ))}
                </div>
              )}
            </div>
          )
        })}

        {hasMore && (
          <div style={{ padding: '16px', textAlign: 'center' }}>
            <span
              ref={feedSentinelRef}
              role="button"
              tabIndex={0}
              onClick={onLoadMore}
              style={{
                fontSize: '10px',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: '#64748b',
                cursor: 'pointer',
              }}
            >
              Xem thêm...
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
