import { useEffect, useState } from 'react'
import { resolveBookSource } from './bookSource'

export function BookDocumentPane({ book }) {
  const source = resolveBookSource(book)

  if (!source.sourceUrl) {
    return (
      <div className="br-doc br-doc--empty">
        <p>Không tìm thấy file để đọc.</p>
      </div>
    )
  }

  if (source.kind === 'pdf') {
    return <PdfDocumentView source={source} title={book.title} />
  }

  if (source.kind === 'html') {
    const htmlUrl = source.isRemote
      ? `/api/v1/public/learning/reader/stream?url=${encodeURIComponent(source.sourceUrl)}`
      : source.sourceUrl
    return (
      <div className="br-doc">
        <iframe
          className="br-doc__frame br-doc__frame--html"
          src={htmlUrl}
          title={book.title}
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        />
      </div>
    )
  }

  if (source.kind === 'text') {
    return <TextDocumentView url={source.viewUrl} title={book.title} openUrl={source.openUrl} />
  }

  return (
    <div className="br-doc br-doc--empty">
      <p>Định dạng này chưa xem trực tiếp. Mở nguồn gốc để đọc.</p>
      <a className="br-btn br-btn--solid" href={source.openUrl} target="_blank" rel="noreferrer">Mở sách</a>
    </div>
  )
}

function PdfDocumentView({ source, title }) {
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    setFailed(false)
  }, [source.viewUrl])

  if (failed) {
    return (
      <div className="br-doc br-doc--empty">
        <p>Không nhúng được PDF trong app (nguồn có thể đã gỡ file).</p>
        <a className="br-btn br-btn--solid" href={source.openUrl} target="_blank" rel="noreferrer">Mở nguồn</a>
      </div>
    )
  }

  return (
    <div className="br-doc">
      <iframe
        className="br-doc__frame"
        src={source.viewUrl}
        title={title}
        onError={() => setFailed(true)}
      />
    </div>
  )
}

function TextDocumentView({ url, title, openUrl }) {
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    fetch(url)
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const body = await response.text()
        if (!cancelled) setText(body)
      })
      .catch(() => {
        if (!cancelled) setError('Không tải được nội dung văn bản.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [url])

  if (loading) return <div className="br-doc br-doc--empty"><p>Đang tải sách…</p></div>
  if (error) {
    return (
      <div className="br-doc br-doc--empty">
        <p>{error}</p>
        <a className="br-btn br-btn--solid" href={openUrl} target="_blank" rel="noreferrer">Mở nguồn</a>
      </div>
    )
  }

  return (
    <article className="br-doc br-doc--text" aria-label={title}>
      <pre>{text}</pre>
    </article>
  )
}
