import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

export default function NewsArticleReader({
  activeArticle,
  detail,
  detailLoading,
  onSelectRelated,
}) {
  if (!activeArticle) {
    return (
      <div className="news-reader news-reader--empty">
        <strong>Chọn một tin để đọc phân tích</strong>
        <p>Tiêu đề, tóm tắt, thị trường ảnh hưởng và các bài liên quan sẽ xuất hiện tại đây.</p>
      </div>
    )
  }

  const sourceUrl = detail?.original_source || activeArticle.url
  const affectedMarkets = detail?.affected_markets || activeArticle.affected_markets || []
  const monitors = detail?.what_to_monitor || activeArticle.what_to_monitor || []
  const learnLinks = detail?.learn_links || activeArticle.learn_links || []
  const whyThisMatters = detail?.why_this_matters
  const info = detail?.info_grid

  return (
    <article className="news-reader" aria-busy={detailLoading}>
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
          <span data-sentiment={activeArticle.sentiment || 'neutral'}>
            {activeArticle.sentiment || 'neutral'}
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
          <h3>Vì sao đáng chú ý</h3>
          <p>{whyThisMatters}</p>
        </section>
      ) : null}

      {info ? (
        <dl className="news-reader__info" aria-label="Thông tin bài viết">
          <div><dt>Phân loại</dt><dd>{info.category || 'Chưa phân loại'}</dd></div>
          <div><dt>Khu vực</dt><dd>{info.region || 'Toàn cầu'}</dd></div>
          <div><dt>Độ tin cậy nguồn</dt><dd>{info.source_tier || 'Đang đánh giá'}</dd></div>
        </dl>
      ) : null}

      {affectedMarkets.length ? (
        <section className="news-reader__section">
          <h3>Thị trường &amp; ngành ảnh hưởng</h3>
          <div className="news-reader__tags">
            {affectedMarkets.map((market) => <span key={market}>{market}</span>)}
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

      {learnLinks.length ? (
        <section className="news-reader__section">
          <h3>Khái niệm liên quan</h3>
          <div className="news-reader__learn-links">
            {learnLinks.map((link) => (
              <a key={link.id || link.label || link} href={link.url || `/learn?concept=${link.id || ''}`}>
                {link.label || link.title || link}
              </a>
            ))}
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
