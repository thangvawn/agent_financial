export function resolveBookSource(book = {}) {
  const candidates = [
    book.pdf_url,
    book.download_url,
    book.url,
  ].filter((value) => typeof value === 'string' && value.trim())

  const fileHint = `${book.file_name || ''} ${book.mime_type || ''} ${candidates.join(' ')}`.toLowerCase()
  const primary = pickPrimaryUrl(candidates, fileHint)
  const kind = detectKind(primary, fileHint)
  const isRemote = /^https?:\/\//i.test(primary)
  const isLocalAsset = primary.startsWith('/learning-assets/')
  const needsProxy = isRemote && (kind === 'pdf' || kind === 'html' || kind === 'text')

  return {
    kind,
    sourceUrl: primary,
    viewUrl: needsProxy
      ? `/api/v1/public/learning/reader/stream?url=${encodeURIComponent(primary)}`
      : primary,
    openUrl: primary,
    isRemote,
    isLocalAsset,
  }
}

function pickPrimaryUrl(candidates, fileHint) {
  const pdf = candidates.find((url) => /\.pdf($|\?)/i.test(url) || /application\/pdf/i.test(fileHint))
  if (pdf) return pdf
  const html = candidates.find((url) => /\.(html?|htm)($|\?)/i.test(url) || /text\/html/i.test(fileHint))
  if (html) return html
  const text = candidates.find((url) => /\.txt($|\?)/i.test(url) || /text\/plain/i.test(fileHint))
  if (text) return text
  return candidates[0] || ''
}

function detectKind(url, fileHint) {
  const blob = `${url} ${fileHint}`.toLowerCase()
  if (/\.pdf($|\?)|application\/pdf/.test(blob)) return 'pdf'
  if (/\.(html?|htm)($|\?)|text\/html/.test(blob)) return 'html'
  if (/\.txt($|\?)|text\/plain/.test(blob)) return 'text'
  if (/\.epub($|\?)/.test(blob)) return 'epub'
  if (url.startsWith('/learning-assets/')) return 'pdf'
  return 'link'
}

export function toReadableBook(item) {
  const sourceUrl = item.pdf_url || item.download_url || item.url || ''
  const fileName = item.file_name
    || sourceUrl.split('?')[0].split('/').pop()
    || `${item.title || 'book'}.pdf`
  return {
    ...item,
    asset_id: item.asset_id || item.book_id || sourceUrl,
    title: item.title || fileName,
    file_name: fileName,
    url: sourceUrl,
    download_url: item.download_url || '',
    pdf_url: item.pdf_url || '',
  }
}
