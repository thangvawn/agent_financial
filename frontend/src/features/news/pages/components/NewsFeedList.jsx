import { SENTIMENT_LABELS, marketLabel } from '../newsLabels'
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

const CATEGORIES = Object.keys(CATEGORY_MAP)

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
  total,
  loadingMore,
  onRetry,
}) {
  return (
    <section className="news-feed" aria-busy={loading}>
      <header className="news-feed__header">
        <div>
          <h2>Dòng tin</h2>
          <p>{feedArticles.length}/{total} tin đang hiển thị</p>
        </div>
        <span data-loading={loading}>{loading ? 'Đang tải…' : `${total} tin phù hợp`}</span>
      </header>

      <div className="news-feed__categories" aria-label="Danh mục tin tức">
        {CATEGORIES.map((item) => (
          <button
            key={item}
            type="button"
            aria-pressed={category === item}
            onClick={() => onCategoryChange(item)}
          >
            {CATEGORY_MAP[item]}
          </button>
        ))}
      </div>

      <div className="news-feed__scroll">
        {error ? <p className="news-feed__notice is-error">{error} <button type="button" onClick={onRetry}>Thử lại</button></p> : null}
        {!loading && !error && articles.length === 0 ? (
          <p className="news-feed__notice">Không tìm thấy tin tức phù hợp với bộ lọc hiện tại.</p>
        ) : null}

        {feedArticles.map((article) => (
          <button
            key={article.article_id}
            type="button"
            className={`news-feed__item${article.article_id === activeArticleId ? ' is-active' : ''}`}
            onClick={() => onSelectArticle(article.article_id)}
          >
            <strong>{article.headline || article.title || 'Không có tiêu đề'}</strong>
            <span className="news-feed__meta">
              {article.source} · {formatNewsDate(article.published_at)}
              {` · ${SENTIMENT_LABELS[article.sentiment] || 'Chưa xác định'}`}
            </span>
            {article.affected_markets?.length ? (
              <span className="news-feed__tags">
                {article.affected_markets.slice(0, 3).map((market) => <i key={market}>{marketLabel(market)}</i>)}
              </span>
            ) : null}
          </button>
        ))}

        {hasMore ? (
          <button ref={feedSentinelRef} type="button" className="news-feed__more" onClick={onLoadMore} disabled={loading || loadingMore}>
            {loadingMore ? 'Đang tải thêm…' : 'Xem thêm'}
          </button>
        ) : null}
      </div>
    </section>
  )
}
