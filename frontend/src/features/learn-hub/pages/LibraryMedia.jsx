import { BookIcon, FileTextIcon, PlayIcon } from '../../../shared/Icons'
import { formatBytes } from '../utils/mediaUtils'

export function VideoPreview({ video, onClose }) {
  return (
    <section className="lh-media-preview" aria-label="Xem video">
      <video className="lh-media__player" controls autoPlay src={video.url}>
        Trình duyệt không hỗ trợ video.
      </video>
      <div className="lh-media-preview__meta">
        <strong>{video.title}</strong>
        <button type="button" className="lh-btn lh-btn--outline" onClick={onClose}>Đóng</button>
      </div>
    </section>
  )
}

export function LocalVideoGrid({ items, loading, error, onPlay }) {
  return (
    <section className="lh-library__section" aria-labelledby="lh-local-video-title">
      <h2 id="lh-local-video-title">Video local ({items.length})</h2>
      {loading ? <p className="lh-empty">Đang quét thư mục…</p> : null}
      {error ? <p className="lh-alert" role="alert">{error}</p> : null}
      {!loading && !items.length ? <p className="lh-empty">Chưa có video local.</p> : null}
      <div className="lh-media-list">
        {items.map((item) => (
          <article key={item.asset_id} className="lh-media-row">
            <div className="lh-media-row__thumb" aria-hidden="true"><PlayIcon size={18} /></div>
            <div className="lh-media-row__body">
              <strong>{item.title}</strong>
              <small>{item.file_name} · {formatBytes(item.size_bytes)}</small>
            </div>
            <button type="button" className="lh-btn lh-btn--primary" onClick={() => onPlay(item)}>Xem</button>
          </article>
        ))}
      </div>
    </section>
  )
}

export function LocalBookGrid({ items, loading, error, onRead }) {
  return (
    <section className="lh-library__section" aria-labelledby="lh-local-book-title">
      <h2 id="lh-local-book-title">Sách local ({items.length})</h2>
      {loading ? <p className="lh-empty">Đang quét thư mục…</p> : null}
      {error ? <p className="lh-alert" role="alert">{error}</p> : null}
      {!loading && !items.length ? <p className="lh-empty">Chưa có sách local.</p> : null}
      <div className="lh-media-list">
        {items.map((item) => (
          <article key={item.asset_id} className="lh-media-row">
            <div className="lh-media-row__thumb lh-media-row__thumb--book" aria-hidden="true"><BookIcon size={18} /></div>
            <div className="lh-media-row__body">
              <strong>{item.title}</strong>
              <small>{item.file_name} · {formatBytes(item.size_bytes)}</small>
            </div>
            <button type="button" className="lh-btn lh-btn--primary" onClick={() => onRead(item)}>Đọc</button>
            <a className="lh-btn lh-btn--outline" href={item.url} target="_blank" rel="noreferrer">File</a>
          </article>
        ))}
      </div>
    </section>
  )
}

export function CatalogCard({ kind, item, onOpenBook }) {
  const title = item.title || 'Untitled'
  const meta = []
  if (kind === 'video' && item.channel) meta.push(item.channel)
  if (kind === 'book' && item.author) meta.push(item.author)
  if (kind === 'paper' && Array.isArray(item.authors) && item.authors.length) {
    meta.push(item.authors.slice(0, 2).join(', '))
  }
  const thumb = item.thumbnail_url || item.cover_url
  const downloadUrl = item.pdf_url || item.download_url || ''
  const icon = kind === 'video' ? <PlayIcon size={22} /> : kind === 'book' ? <BookIcon size={22} /> : <FileTextIcon size={22} />

  return (
    <article className="lh-card">
      <div className="lh-card__cover">
        {thumb ? <img src={thumb} alt="" loading="lazy" /> : <span className="lh-card__icon">{icon}</span>}
      </div>
      <div className="lh-card__body">
        <p className="lh-card__partner">{kind === 'video' ? 'Video' : kind === 'book' ? 'Sách' : 'Tài liệu'}</p>
        <h3 className="lh-card__title">{title}</h3>
        {meta.length ? <p className="lh-card__meta">{meta.join(' · ')}</p> : null}
        <div className="lh-card__actions">
          <a className="lh-btn lh-btn--primary" href={item.url} target="_blank" rel="noreferrer">Mở</a>
          {downloadUrl ? <a className="lh-btn lh-btn--outline" href={downloadUrl} target="_blank" rel="noreferrer">PDF</a> : null}
          {kind === 'book' && onOpenBook && (item.pdf_url || item.download_url || item.url) ? (
            <button
              type="button"
              className="lh-btn lh-btn--outline"
              onClick={() => onOpenBook(item)}
            >
              Đọc
            </button>
          ) : null}
        </div>
      </div>
    </article>
  )
}
