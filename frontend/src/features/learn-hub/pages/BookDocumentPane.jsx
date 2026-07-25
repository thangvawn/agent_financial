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

  if (source.kind === 'pdf') return <PdfDocumentView source={source} title={book.title} />

  if (source.kind === 'html') {
    return (
      <div className="br-doc">
        <iframe
          className="br-doc__frame br-doc__frame--html"
          src={source.viewUrl}
          title={book.title}
          sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
        />
      </div>
    )
  }

  if (source.kind === 'text') {
    return <TextBookPane url={source.viewUrl} title={book.title} openUrl={source.openUrl} />
  }

  return (
    <div className="br-doc br-doc--empty">
      <p>Định dạng này chưa xem trực tiếp.</p>
      <a className="br-btn br-btn--solid" href={source.openUrl} target="_blank" rel="noreferrer">Mở sách</a>
    </div>
  )
}

function PdfDocumentView({ source, title }) {
  const [mode, setMode] = useState(source.isRemote ? 'proxy' : 'direct')
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)

  const embedUrl = mode === 'proxy'
    ? source.viewUrl
    : mode === 'gview'
      ? `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(source.openUrl)}`
      : source.openUrl

  useEffect(() => {
    setLoading(true)
    setFailed(false)
  }, [embedUrl])

  return (
    <div className="br-doc">
      {loading && !failed ? (
        <div className="br-doc br-doc--empty br-doc--overlay">
          <p>Đang tải PDF… (file lớn có thể mất vài giây)</p>
        </div>
      ) : null}
      {failed ? (
        <div className="br-doc br-doc--empty">
          <p>Không nhúng được PDF trong app.</p>
          <a className="br-btn br-btn--solid" href={source.openUrl} target="_blank" rel="noreferrer">
            Mở tab mới
          </a>
          {source.isRemote && mode !== 'gview' ? (
            <button type="button" className="br-btn br-btn--ghost" onClick={() => setMode('gview')}>
              Thử Google Viewer
            </button>
          ) : null}
        </div>
      ) : (
        <iframe
          key={embedUrl}
          className="br-doc__frame"
          src={embedUrl}
          title={title}
          onLoad={() => setLoading(false)}
          onError={() => { setLoading(false); setFailed(true) }}
        />
      )}
      <div className="br-doc__actions">
        <a className="br-btn br-btn--ghost" href={source.openUrl} target="_blank" rel="noreferrer">Mở tab mới</a>
        {source.isRemote && mode !== 'gview' ? (
          <button type="button" className="br-btn br-btn--ghost" onClick={() => setMode('gview')}>
            Thử Google Viewer
          </button>
        ) : null}
        {source.isRemote && mode === 'gview' ? (
          <button type="button" className="br-btn br-btn--ghost" onClick={() => setMode('proxy')}>
            Thử proxy app
          </button>
        ) : null}
      </div>
    </div>
  )
}

function TextBookPane({ url, title, openUrl }) {
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
