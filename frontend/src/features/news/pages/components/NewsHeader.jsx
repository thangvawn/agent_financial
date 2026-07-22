export default function NewsHeader({
  topHighlight,
  onSelectTopHighlight,
  onRefresh,
  loading,
  freshness,
  sourceCount,
  successfulSourceCount,
}) {
  return (
    <header className="news-header">
      <div className="news-header__main">
        <div className="news-header__identity">
          <p className="news-header__kicker">
            NORTHSTAR / NEWS INTEL DESK
          </p>
          <h1>
            News &amp; Intelligence
          </h1>
          <p className="news-header__lede">
            Phân tích tin tức vĩ mô và doanh nghiệp cùng hệ thống kênh truyền dẫn tác động chéo.
          </p>
        </div>

        <div className="news-header__actions">
          <div className="news-header__source-status" aria-live="polite">
            <span aria-hidden="true" />
            <span>
              SOURCES: {successfulSourceCount}/{sourceCount} ({freshness})
            </span>
          </div>

          <button
            type="button"
            className="news-header__refresh"
            onClick={onRefresh}
            disabled={loading}
            aria-busy={loading}
          >
            {loading ? (
              <>
                <svg className="news-header__spinner" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Đang tải</span>
              </>
            ) : (
              <span>Cập nhật tin</span>
            )}
          </button>
        </div>
      </div>

      {topHighlight && (
        <div className="news-header__ticker">
          <div>
            <span className="news-header__ticker-label">
              NỔI BẬT
            </span>
            <strong>
              {topHighlight.headline}
            </strong>
          </div>
          <button
            type="button"
            onClick={onSelectTopHighlight}
          >
            Đọc phân tích ↗
          </button>
        </div>
      )}
    </header>
  )
}
