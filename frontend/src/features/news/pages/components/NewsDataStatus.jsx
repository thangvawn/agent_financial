import { formatNewsDate } from '../newsFinnhubCalendarUtils'
import { newsQuality } from '../newsLabels'

export default function NewsDataStatus({ payload, loading, error, pending, onRefresh }) {
  const quality = newsQuality(payload)
  return <div className="news-data-status" data-stale={quality.stale}>
    <div role="status" aria-live="polite">
      <strong>{loading ? 'Đang cập nhật…' : quality.label}</strong>
      {quality.updatedAt && <span> · Dữ liệu lúc {formatNewsDate(quality.updatedAt)}</span>}
      {payload?.source_count > 0 && <span> · {payload.successful_source_count}/{payload.source_count} nguồn</span>}
      {error && <p>{error}</p>}
      {pending && <p>Có bản cập nhật. Nhấn Cập nhật tin để xem danh sách mới.</p>}
    </div>
    <button type="button" onClick={onRefresh} disabled={loading}>Cập nhật tin</button>
  </div>
}
