import { formatNewsDate } from '../newsFinnhubCalendarUtils.js'

const PERIODS = [
  { id: 'day', label: 'Ngày' },
  { id: 'week', label: 'Tuần' },
  { id: 'month', label: 'Tháng' },
]

export default function NewsHighlightsSection({
  period,
  payload,
  items,
  loading,
  error,
  activeArticleId,
  onPeriodChange,
  onSelect,
  onRetry,
}) {
  const status = buildStatus(payload, items.length)

  function handleTabKeyDown(event, index) {
    const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End']
    if (!keys.includes(event.key)) return
    event.preventDefault()
    const last = PERIODS.length - 1
    const nextIndex = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? last
        : event.key === 'ArrowRight'
          ? (index + 1) % PERIODS.length
          : (index - 1 + PERIODS.length) % PERIODS.length
    const next = PERIODS[nextIndex]
    onPeriodChange(next.id)
    document.getElementById(`news-highlights-tab-${next.id}`)?.focus()
  }

  return (
    <section className="news-highlights" aria-labelledby="news-highlights-title" aria-busy={loading}>
      <div className="news-highlights__heading">
        <div>
          <h2 id="news-highlights-title">Tin nổi bật</h2>
          <p>Các sự kiện có mức ảnh hưởng cao nhất trong kỳ đã chọn.</p>
        </div>
        <div className="news-highlights__tabs" role="tablist" aria-label="Kỳ tổng hợp tin nổi bật">
          {PERIODS.map((option, index) => (
            <button
              id={`news-highlights-tab-${option.id}`}
              key={option.id}
              type="button"
              role="tab"
              aria-selected={period === option.id}
              aria-controls="news-highlights-panel"
              tabIndex={period === option.id ? 0 : -1}
              className={period === option.id ? 'is-active' : ''}
              onClick={() => onPeriodChange(option.id)}
              onKeyDown={(event) => handleTabKeyDown(event, index)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="news-highlights__status" aria-live="polite">
        <span>{status}</span>
        {loading ? <span>Đang cập nhật…</span> : null}
      </div>

      <div id="news-highlights-panel" role="tabpanel" aria-labelledby={`news-highlights-tab-${period}`}>
        {error ? (
          <div className="news-highlights__notice is-error" role="alert">
            <span>
              {items.length
                ? 'Không thể cập nhật dữ liệu. Kết quả gần nhất vẫn được giữ lại.'
                : 'Không thể tải tin nổi bật cho kỳ này.'}
            </span>
            <button type="button" onClick={onRetry}>Thử lại</button>
          </div>
        ) : null}

        {loading && items.length === 0 ? <HighlightSkeleton /> : null}

        {!loading && !error && items.length === 0 ? (
          <div className="news-highlights__notice">
            Chưa có đủ tin trong kỳ này. Hệ thống sẽ bổ sung khi có dữ liệu mới.
          </div>
        ) : null}

        {items.length > 0 ? (
          <div className="news-highlights__list">
            {items.map((item, index) => (
              <HighlightItem
                key={item.article_id}
                item={item}
                rank={index + 1}
                active={item.article_id === activeArticleId}
                onSelect={onSelect}
              />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  )
}

function HighlightItem({ item, rank, active, onSelect }) {
  return (
    <article className={`news-highlight${active ? ' is-active' : ''}`}>
      <span className="news-highlight__rank" aria-label={`Hạng ${rank}`}>{String(rank).padStart(2, '0')}</span>
      <button type="button" className="news-highlight__open" onClick={() => onSelect(item.article_id)}>
        <span className="news-highlight__meta">
          {item.source || 'Nguồn tổng hợp'} · {formatNewsDate(item.published_at)}
          {item.importance_label ? ` · ${item.importance_label}` : ''}
        </span>
        <strong>{item.headline || item.title || 'Không có tiêu đề'}</strong>
        <span className="news-highlight__why">{item.why_it_matters || item.summary || 'Đang cập nhật phân tích tác động.'}</span>
        {item.affected_markets?.length ? (
          <span className="news-highlight__markets">{item.affected_markets.slice(0, 3).join(' · ')}</span>
        ) : null}
      </button>
    </article>
  )
}

function HighlightSkeleton() {
  return (
    <div className="news-highlights__skeleton" aria-hidden="true">
      {[0, 1, 2].map((item) => <span key={item} />)}
    </div>
  )
}

function buildStatus(payload, count) {
  const start = formatWindowDate(payload?.window_start)
  const end = formatWindowDate(payload?.window_end, true)
  const range = start && end ? (start === end ? start : `${start} – ${end}`) : 'Kỳ hiện tại'
  return `${range} · ${count} tin`
}

function formatWindowDate(value, isExclusiveEnd = false) {
  if (!value) return ''
  const parsed = new Date(value)
  const date = isExclusiveEnd ? new Date(parsed.getTime() - 1) : parsed
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    timeZone: 'Asia/Ho_Chi_Minh',
  }).format(date)
}
