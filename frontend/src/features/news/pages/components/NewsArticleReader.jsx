import { newsLessonLink } from '../../../learn-hub/content/newsLessonLinks'
import { SENTIMENT_LABELS, marketLabel } from '../newsLabels'
import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

export default function NewsArticleReader({
  activeArticle,
  detail,
  detailLoading,
  onSelectRelated,
  error,
  onRetry,
}) {
  if (!activeArticle) {
    return (
      <div className="news-reader news-reader--empty">
        <strong>{detailLoading ? 'Đang tải bài viết…' : 'Chọn một tin để đọc phân tích'}</strong>
        {error && <p role="alert">{error} <button type="button" onClick={onRetry}>Thử lại</button></p>}
        <p>Tiêu đề, tóm tắt, thị trường ảnh hưởng và các bài liên quan sẽ xuất hiện tại đây.</p>
      </div>
    )
  }

  const sourceUrl = detail?.original_source || activeArticle.url
  const affectedMarkets = detail?.affected_markets || activeArticle.affected_markets || []
  const monitors = detail?.what_to_monitor || activeArticle.what_to_monitor || []
  const learnLinks = detail?.learn_links || activeArticle.learn_links || []
  const whyThisMatters = detail?.why_this_matters
  const lessons = [...new Map(learnLinks.map(link => newsLessonLink(link.id)).filter(Boolean).map(link => [link.url, link])).values()]

  return (
    <article className="news-reader" aria-busy={detailLoading}>
      {error && <p role="alert">{error} <button type="button" onClick={onRetry}>Thử lại</button></p>}
      {detailLoading ? (
        <div className="news-reader__loading" role="status">
          <span className="news-reader__spinner" aria-hidden="true" />
          Đang phân tích…
        </div>
      ) : null}

      <header className="news-reader__header">
        <p className="news-reader__eyebrow">Bài đang đọc</p>
        <div className="news-reader__meta">
          <span>{activeArticle.source || 'Nguồn tổng hợp'}</span>
          <span>{formatNewsDate(activeArticle.published_at)}</span>
          <span data-sentiment={activeArticle.sentiment || 'unknown'}>
            {SENTIMENT_LABELS[activeArticle.sentiment] || 'Chưa xác định'}
          </span>
        </div>
        <h2>{activeArticle.headline}</h2>
      </header>

      <section className="news-reader__summary">
        <h3>Tóm tắt &amp; luận điểm</h3>
        <p>
          {activeArticle.summary?.trim()
            ? activeArticle.summary
            : 'Nguồn chỉ cung cấp tiêu đề ngắn. Mở bài viết gốc để xem nội dung đầy đủ.'}
        </p>
        {sourceUrl ? (
          <a href={sourceUrl} target="_blank" rel="noreferrer">
            Xem bài viết gốc ↗
          </a>
        ) : null}
      </section>

      {whyThisMatters ? (
        <section className="news-reader__section news-reader__context">
          <h3>Thông tin phân loại</h3>
          <p>{whyThisMatters}</p>
        </section>
      ) : null}

      {affectedMarkets.length ? (
        <section className="news-reader__section">
          <h3>Thị trường &amp; ngành ảnh hưởng</h3>
          <div className="news-reader__tags">
            {affectedMarkets.map((market) => <span key={market}>{marketLabel(market)}</span>)}
          </div>
        </section>
      ) : null}

      {monitors.length ? (
        <section className="news-reader__section news-reader__monitor">
          <h3>Điều cần theo dõi</h3>
          <ul>
            {monitors.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
      ) : null}

      {lessons.length ? (
        <section className="news-reader__section">
          <h3>Bài học liên quan</h3>
          <div className="news-reader__learn-links">
            {lessons.map(link => <a key={link.url} href={link.url}>{link.label}</a>)}
          </div>
        </section>
      ) : null}

      {detail?.related_articles?.length ? (
        <section className="news-reader__section news-reader__related">
          <h3>Tin tức liên quan</h3>
          <div className="news-reader__related-list">
            {detail.related_articles.map((article) => (
              <button
                key={article.article_id}
                type="button"
                onClick={() => onSelectRelated(article.article_id)}
              >
                <strong>{article.headline || article.title || 'Không có tiêu đề'}</strong>
                <span>{article.source} · {formatNewsDate(article.published_at)}</span>
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </article>
  )
}
