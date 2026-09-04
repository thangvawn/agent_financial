import { useState, useEffect } from 'react'

export function BookDocumentPane({ book }) {
  if (!book) return null

  if (book.isPdf) {
    return <PdfBookPane source={book.source} title={book.title} />
  }

  if (book.isText) {
    return <TextBookPane url={book.source.viewUrl} title={book.title} openUrl={book.source.openUrl} />
  }

  return (
    <div className="br-doc br-doc--empty">
      <p>Không có bản đọc trực tiếp trong ứng dụng cho tài liệu này.</p>
      {book.source?.openUrl ? (
        <a className="br-btn br-btn--solid" href={book.source.openUrl} target="_blank" rel="noreferrer">
          Mở liên kết tài liệu
        </a>
      ) : null}
    </div>
  )
}

function PdfBookPane({ source, title }) {
  const [mode, setMode] = useState(source.isRemote ? 'gview' : 'proxy')
  const [loadedUrl, setLoadedUrl] = useState('')
  const [failedUrl, setFailedUrl] = useState('')

  const embedUrl = mode === 'proxy'
    ? source.viewUrl
    : mode === 'gview'
      ? `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(source.openUrl)}`
      : source.openUrl

  const loading = loadedUrl !== embedUrl && failedUrl !== embedUrl
  const failed = failedUrl === embedUrl

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
          onLoad={() => setLoadedUrl(embedUrl)}
          onError={() => setFailedUrl(embedUrl)}
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
  const [data, setData] = useState({ text: '', error: '', url: '' })

  const loading = data.url !== url
  const text = data.text
  const error = data.error

  useEffect(() => {
    let cancelled = false
    fetch(url)
      .then(async (response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const body = await response.text()
        if (!cancelled) setData({ text: body, error: '', url })
      })
      .catch(() => {
        if (!cancelled) setData({ text: '', error: 'Không tải được nội dung văn bản.', url })
      })
    return () => { cancelled = true }
  }, [url])

  return (
    <div className="br-doc br-doc--text">
      {loading ? <p className="br-doc__meta">Đang tải văn bản…</p> : null}
      {error ? (
        <div className="br-doc br-doc--empty">
          <p>{error}</p>
          <a className="br-btn br-btn--solid" href={openUrl} target="_blank" rel="noreferrer">Mở nguồn gốc</a>
        </div>
      ) : null}
      {!loading && !error ? (
        <article className="br-doc__article">
          <header className="br-doc__header">
            <h2>{title}</h2>
          </header>
          <pre className="br-doc__content">{text}</pre>
        </article>
      ) : null}
    </div>
  )
}
