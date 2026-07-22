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
}) {
  return (
    <section className="news-feed" aria-busy={loading}>
      <header className="news-feed__header">
        <div>
          <h2>Dòng tin</h2>
          <p>{feedArticles.length}/{articles.length} tin đang hiển thị</p>
        </div>
        <span data-loading={loading}>{loading ? 'Đang cập nhật…' : 'Sẵn sàng'}</span>
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
        {error ? <p className="news-feed__notice is-error">Không thể cập nhật tin tức. Vui lòng thử lại sau.</p> : null}
        {!loading && articles.length === 0 ? (
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
              {article.sentiment && article.sentiment !== 'neutral' ? ` · ${article.sentiment}` : ''}
            </span>
            {article.affected_markets?.length ? (
              <span className="news-feed__tags">
                {article.affected_markets.slice(0, 3).map((market) => <i key={market}>{market}</i>)}
              </span>
            ) : null}
          </button>
        ))}

        {hasMore ? (
          <button ref={feedSentinelRef} type="button" className="news-feed__more" onClick={onLoadMore}>
            Xem thêm
          </button>
        ) : null}
      </div>
    </section>
  )
}
